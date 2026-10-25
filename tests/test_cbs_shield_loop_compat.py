"""CBS loop assets are isolated, cyclically interpolated and reversible."""
import base64
import copy
import importlib.util
import json
import os
from pathlib import Path
import struct
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
TOOL=ROOT/'tools/cbs_shield_loop_compat.py'
BUNDLE=ROOT/'DarkOrbit_Version1.1.115/DarkOrbit_Data/StreamingAssets/aa/BuildTarget/effect_2d_assets_bundle_pack_effect_2d_047.bundle'
CATALOG=ROOT/'DarkOrbit_Version1.1.115/DarkOrbit_Data/StreamingAssets/aa/catalog.json'

def require_dependencies(*names):
    for name in names:
        try:
            __import__(name)
        except ImportError as error:
            raise unittest.SkipTest('Optional shield checks require %s: %s' % (name,error))


def fixture_artifacts(module):
    """Use an explicit pristine fixture, or verified backups of the applied layer."""
    explicit = os.environ.get('CBS_LOOP_CLIENT_DIR')
    client = Path(explicit) if explicit else ROOT / 'DarkOrbit_Version1.1.115'
    paths = module.artifact_paths(client)
    if not explicit and any(not path.exists() for path in paths.values()):
        raise unittest.SkipTest('Optional five-artifact shield fixture absent; set CBS_LOOP_CLIENT_DIR')
    current = {kind: path.read_bytes() for kind, path in paths.items()}
    if all(module.digest(raw) == module.INPUT_HASH[module.input_kind(kind)]
           for kind, raw in current.items()):
        return current
    if explicit:
        raise ValueError('CBS_LOOP_CLIENT_DIR must contain all five supported original artifacts')
    # Validate the installed manifest, all current hashes and every original
    # backup before using any of them. An unrelated native layer cannot silently
    # become a fixture, and temporary apply/restore tests never alter this client.
    manifest, originals = module.verified_state(client)
    if not all(module.digest(current[kind]) == manifest['artifacts'][kind]['modified_sha256']
               for kind in paths):
        raise ValueError('Default shield-loop client is only partly applied; use CBS_LOOP_CLIENT_DIR')
    for kind, raw in originals.items():
        module.check(raw, module.input_kind(kind))
    return originals


class ShieldLoop(unittest.TestCase):
    def module(self):
        self.assertTrue(TOOL.exists(), 'CBS-only seamless loop tool missing')
        spec=importlib.util.spec_from_file_location('shield_loop_compat',TOOL)
        m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

    def test_cyclic_interpolation_preserves_endpoints_and_alpha_brightness(self):
        m=self.module();require_dependencies('PIL')
        from PIL import Image,ImageChops
        a=Image.new('RGBA',(2,2),(240,100,20,120));b=Image.new('RGBA',(2,2),(10,80,200,220))
        frames=m.interpolate_frames([a,b],4)
        self.assertEqual(len(frames),8)
        self.assertEqual(frames[0].tobytes(),a.tobytes());self.assertEqual(frames[4].tobytes(),b.tobytes())
        bg=Image.new('RGBA',(2,2),(0,0,0,255))
        expected=Image.blend(a.convert('RGBa'),b.convert('RGBa'),.5).convert('RGBA')
        self.assertEqual(frames[2].tobytes(),expected.tobytes())
        self.assertEqual(frames[-1].tobytes(),Image.blend(b.convert('RGBa'),a.convert('RGBa'),.75).convert('RGBA').tobytes())

    def test_catalog_alias_preserves_every_existing_location(self):
        m=self.module();raw=fixture_artifacts(m)['catalog'];before=json.loads(raw);after=json.loads(m.patch_catalog(raw))
        old=m.catalog_locations(before);new=m.catalog_locations(after)
        self.assertEqual({k:new[k] for k in old},old)
        self.assertIn(m.ALIAS,new)
        self.assertEqual(new[m.ALIAS][0]['internalId'],m.ALIAS_PATH)
        self.assertEqual(new[m.ALIAS][0]['dependency'],old[m.SOURCE_ALIAS][0]['dependency'])
        for key in ('m_ProviderIds','m_ExtraDataString','m_resourceTypes','m_InternalIdPrefixes'):
            self.assertEqual(before[key],after[key])

    @unittest.skipUnless(os.environ.get('CBS_LOOP_CLIENT_DIR') or BUNDLE.exists(),'Local native bundle required')
    def test_bundle_clone_preserves_original_ish_and_all_other_objects(self):
        m=self.module();raw=fixture_artifacts(m)['bundle'];require_dependencies('UnityPy','PIL')
        import UnityPy
        modified=m.patch_bundle(raw)
        before=UnityPy.load(raw);after=UnityPy.load(modified)
        old={x.path_id:x for x in before.objects};new={x.path_id:x for x in after.objects}
        ab=next(x.path_id for x in before.objects if x.type.name=='AssetBundle')
        for pid,o in old.items():
            if pid!=ab:self.assertEqual(o.get_raw_data(),new[pid].get_raw_data(),(pid,o.type.name))
        catalog=next(x for x in after.objects if x.type.name=='AssetBundle').read()
        names={name:info for name,info in catalog.m_Container}
        self.assertIn(m.SOURCE_PATH,names);self.assertIn(m.ALIAS_PATH,names)
        clones=[x for pid,x in new.items() if pid not in old]
        clips=[x for x in clones if x.type.name=='AnimationClip'];self.assertEqual(len(clips),1)
        clip=clips[0].read_typetree();self.assertEqual(clip['m_SampleRate'],100.)
        self.assertAlmostEqual(clip['m_MuscleClip']['m_StopTime'],.64,places=5)
        self.assertEqual(len(clip['m_ClipBindingConstant']['pptrCurveMapping']),64)
        sprites=[new[x['m_PathID']].read() for x in clip['m_ClipBindingConstant']['pptrCurveMapping']]
        self.assertTrue(all(s.image.size==(350,350) for s in sprites))
        original=old[m.CLIP_ID].read_typetree()
        frames=[old[x['m_PathID']].read().image for x in original['m_ClipBindingConstant']['pptrCurveMapping']]
        for i in range(16):self.assertEqual(sprites[i*4].image.tobytes(),frames[i].tobytes())
        from PIL import Image,ImageChops,ImageStat
        def visible(image):
            return Image.alpha_composite(Image.new('RGBA',image.size,(10,10,18,255)),image).convert('RGB')
        old_visible=[visible(im) for im in frames];new_frames=[sprite.image for sprite in sprites]
        new_visible=[visible(im) for im in new_frames]
        def deltas(images):
            return [sum(ImageStat.Stat(ImageChops.difference(im,images[i-1])).mean)/3 for i,im in enumerate(images)]
        old_delta,new_delta=deltas(old_visible),deltas(new_visible)
        self.assertLessEqual(max(new_delta),max(old_delta)*.3)
        self.assertLessEqual(new_delta[0],max(new_delta))
        # Cyclic blending can only mix the original faint center pixels.
        for i,im in enumerate(new_frames):
            a=frames[i//4].getpixel((175,175))[3]
            b=frames[(i//4+1)%16].getpixel((175,175))[3]
            self.assertLessEqual(im.getpixel((175,175))[3],max(a,b))



class ShieldLoopNative(unittest.TestCase):
    module=ShieldLoop.module

    def test_scoped_native_hook_preserves_context_with_loader_relocations_at_three_bases(self):
        m=self.module();self.assertTrue(callable(getattr(m,'patch_native',None)),'Native CBS-only alias hook missing')
        original=fixture_artifacts(m)['native']
        try:
            import pefile
            sys.path.insert(0,str(ROOT/'_trial/drone-deps'))
            from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_CODE
            from unicorn.x86_const import UC_X86_REG_EAX,UC_X86_REG_EBX,UC_X86_REG_ECX,UC_X86_REG_EDX,UC_X86_REG_ESI,UC_X86_REG_EDI,UC_X86_REG_EBP,UC_X86_REG_ESP,UC_X86_REG_EFLAGS,UC_X86_REG_EIP,UC_X86_REG_XMM0
        except ImportError:
            self.skipTest('Optional shield native replay requires pefile and Unicorn')
        modified=m.patch_native(original)
        pe=pefile.PE(data=modified,fast_load=True);image=pe.get_memory_mapped_image()
        def loaded_image(base):
            # The Windows loader applies HIGHLOW relocations before calling code.
            # Mapping bytes at a new base without this step missed the first live crash.
            result=bytearray(image);directory=pe.OPTIONAL_HEADER.DATA_DIRECTORY[5]
            cursor=directory.VirtualAddress;end=cursor+directory.Size
            delta=base-pe.OPTIONAL_HEADER.ImageBase
            while cursor<end:
                page,size=struct.unpack_from('<II',image,cursor)
                if size<8:raise AssertionError('Invalid relocation block')
                for position in range(cursor+8,cursor+size,2):
                    entry=struct.unpack_from('<H',image,position)[0]
                    kind=entry>>12;target=page+(entry&0xfff)
                    if kind==3:
                        value=struct.unpack_from('<I',result,target)[0]
                        struct.pack_into('<I',result,target,(value+delta)&0xffffffff)
                    elif kind!=0:raise AssertionError('Unsupported PE relocation type')
                cursor+=size
            return bytes(result)
        for base in (0x10000000,0x18000000,0x75420000):
            with self.subTest(base=base):
                mapped=loaded_image(base)
                u=Uc(UC_ARCH_X86,UC_MODE_32);u.mem_map(base,(len(mapped)+4095)&~4095);u.mem_write(base,mapped)
                heap=0x40000000;u.mem_map(heap,0x10000)
                regs=[UC_X86_REG_EAX,UC_X86_REG_EBX,UC_X86_REG_ECX,UC_X86_REG_EDX,UC_X86_REG_ESI,UC_X86_REG_EDI,UC_X86_REG_EBP,UC_X86_REG_ESP]
                values=[0x11111111,0x22222222,0x33333333,0x44444444,heap+0x100,0x66666666,heap+0x8000,heap+0x6000]
                for reg,value in zip(regs,values):u.reg_write(reg,value)
                for i in range(8):u.reg_write(UC_X86_REG_XMM0+i,i+1)
                u.reg_write(UC_X86_REG_EFLAGS,0x646);observed=[]
                def hook(emu,address,size,data):
                    if address==base+0x7645eb:emu.emu_stop()
                    elif address==base+0x2002a0:
                        esp=emu.reg_read(UC_X86_REG_ESP)
                        pointer=struct.unpack('<I',emu.mem_read(esp+4,4))[0]
                        self.assertEqual(bytes(emu.mem_read(pointer,len(m.ALIAS)+1)),m.ALIAS.encode()+b'\0');observed.append(pointer)
                        ret=struct.unpack('<I',emu.mem_read(esp,4))[0]
                        for reg in regs[:-2]:emu.reg_write(reg,0x99999999)
                        for i in range(8):emu.reg_write(UC_X86_REG_XMM0+i,0)
                        emu.reg_write(UC_X86_REG_EAX,heap+0x200);emu.reg_write(UC_X86_REG_EFLAGS,0x202)
                        emu.reg_write(UC_X86_REG_ESP,esp+4);emu.reg_write(UC_X86_REG_EIP,ret)
                u.hook_add(UC_HOOK_CODE,hook);u.emu_start(base+0x7645e6,base+0x7645eb,count=1000)
                self.assertEqual(len(observed),1)
                self.assertEqual(u.reg_read(UC_X86_REG_EAX),heap+0x200)
                self.assertEqual([u.reg_read(reg) for reg in regs[1:]],values[1:])
                self.assertEqual([u.reg_read(UC_X86_REG_XMM0+i) for i in range(8)],list(range(1,9)))
                self.assertEqual(u.reg_read(UC_X86_REG_EFLAGS),0x646)
                u.mem_write(heap+0x10c,struct.pack('<I',heap+0x200))
                u.emu_start(base+0x7645f1,base+0x7645f7,count=20)
                self.assertEqual(u.reg_read(UC_X86_REG_ESP),values[-1]-4)
                self.assertEqual(struct.unpack('<I',u.mem_read(values[-1]-4,4))[0],heap+0x200)

        original_pe=pefile.PE(data=original,fast_load=True)
        changed=set(range(original_pe.get_offset_from_rva(0x7645e6),original_pe.get_offset_from_rva(0x7645e6)+5))
        changed.update(range(original_pe.get_offset_from_rva(0x7645f1),original_pe.get_offset_from_rva(0x7645f1)+6))
        for position,expected in ((0x356efce,0x35e7),(0x356efd0,0x35f3)):
            self.assertEqual(struct.unpack_from('<H',original,position)[0],expected)
            self.assertEqual(struct.unpack_from('<H',modified,position)[0],expected&0xfff)
            changed.update(range(position,position+2))
        for section in original_pe.sections:
            start=section.PointerToRawData;end=start+section.SizeOfRawData
            self.assertEqual(bytes(v for i,v in enumerate(original[start:end],start) if i not in changed),
                             bytes(v for i,v in enumerate(modified[start:end],start) if i not in changed))

class ShieldLoopTransactions(unittest.TestCase):
    module=ShieldLoop.module

    def test_reversible_transaction_idempotence_and_tamper_guards(self):
        m=self.module();import tempfile
        from unittest.mock import patch
        with tempfile.TemporaryDirectory() as directory:
            client=Path(directory)/'client'
            targets=m.artifact_paths(client)
            original=fixture_artifacts(m);require_dependencies('UnityPy','PIL','pefile')
            for kind,path in targets.items():path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(original[kind])
            with patch.object(m,'native_client_running',return_value=True):
                with self.assertRaises(RuntimeError):m.apply(client)
            self.assertFalse(m.manifest_path(client).exists())
            with patch.object(m,'native_client_running',return_value=False):
                manifest=m.apply(client);modified={kind:path.read_bytes() for kind,path in targets.items()}
                self.assertEqual(m.apply(client),manifest)
                for kind,path in targets.items():self.assertEqual(path.read_bytes(),modified[kind])
                native=targets['native'];native.write_bytes(modified['native']+b'tamper')
                with self.assertRaisesRegex(ValueError,'fingerprint'):m.restore(client)
                self.assertEqual(native.read_bytes(),modified['native']+b'tamper')
                native.write_bytes(modified['native']);m.restore(client);m.restore(client)
                for kind,path in targets.items():self.assertEqual(path.read_bytes(),original[kind])

    def test_reapply_upgrades_unrelocated_first_revision(self):
        m=self.module();import tempfile
        from unittest.mock import patch
        with tempfile.TemporaryDirectory() as directory:
            client=Path(directory)/'client';targets=m.artifact_paths(client)
            originals=fixture_artifacts(m);require_dependencies('UnityPy','PIL','pefile')
            for kind,path in targets.items():path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(originals[kind])
            with patch.object(m,'native_client_running',return_value=False):
                manifest=m.apply(client);fixed=targets['native'].read_bytes();bad=bytearray(fixed)
                struct.pack_into('<H',bad,0x356efce,0x35e7);struct.pack_into('<H',bad,0x356efd0,0x35f3)
                targets['native'].write_bytes(bad)
                manifest.pop('revision',None);manifest['artifacts']['native']['modified_sha256']=m.digest(bad)
                m.manifest_path(client).write_text(json.dumps(manifest))
                m.apply(client)
                self.assertEqual(targets['native'].read_bytes(),fixed)
                m.restore(client)
                for kind,path in targets.items():self.assertEqual(path.read_bytes(),originals[kind])

    def test_prepare_changes_only_new_candidate_directory(self):
        m=self.module();import tempfile
        with tempfile.TemporaryDirectory() as directory:
            source=Path(directory)/'original-client';out=Path(directory)/'prepared'
            originals=fixture_artifacts(m);require_dependencies('UnityPy','PIL','pefile')
            for kind,path in m.artifact_paths(source).items():
                path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(originals[kind])
            manifest=m.prepare(source,out)
            for kind,path in m.artifact_paths(source).items():
                self.assertEqual(path.read_bytes(),originals[kind])
                candidate=out/path.relative_to(source)
                self.assertEqual(m.digest(candidate.read_bytes()),manifest['artifacts'][kind]['modified_sha256'])
            with self.assertRaisesRegex(ValueError,'new'):m.prepare(source,out)

if __name__=='__main__':unittest.main()
