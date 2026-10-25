"""Compare real native model dictionary/tiers against installed inventory art."""
import importlib.util
import json
import os
from pathlib import Path
import struct
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'_trial/drone-deps'))
sys.path.insert(0,str(ROOT/'tools/il2cpp'))
sys.path.insert(0,str(ROOT/'server'))
try:
    import pefile
    from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_CODE
    from unicorn.x86_const import *
except ImportError:Uc=None
from test_cbs_hangar_hud_compat import relocation_entries

# Inventory icon pixels, not the names of the shipped map patterns, establish
# these body identities. See docs/cbs-module-art-evidence.json/contact sheet.
INVENTORY_ART={
 'module_repm-1':(4,3,'module_rep'),
 'module_ltm-lr':(7,4,'module_laserhigh'),  # icon I: short red beam
 'module_ltm-mr':(6,5,'module_lasermid'),
 'module_ltm-hr':(5,6,'module_laserlow'),   # icon III: long red beam
 'module_ram-la':(9,7,'module_rocketmid'),  # icon II: slanted striped launcher
 'module_ram-ma':(8,8,'module_rocketlow'),  # icon III: dish
 'module_honm-1':(10,9,'module_hon'),
 'module_dmgm-1':(11,10,'module_dama'),
 'module_xpm-1':(12,11,'module_xp')}


def load_tool():
    spec=importlib.util.spec_from_file_location('cbs_models',ROOT/'tools/cbs_module_model_compat.py')
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m


def ror(v,n):return ((v>>n)|(v<<(32-n)))&0xffffffff


class ModuleModelCompatibility(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.m=load_tool();cls.images={}
        fixture=os.environ.get('CBS_MODELS_NATIVE_DLL')
        cls.original=Path(fixture).read_bytes() if fixture else None
        cls.modified=cls.m.patch_bytes(cls.original) if fixture else None
        if fixture:
            from meta import Metadata
            cls.literals=Metadata(ROOT/'DarkOrbit_Version1.1.115/DarkOrbit_Data/il2cpp_data/Metadata/global-metadata.dat').string_literals()

    def machine(self,raw,base):
        key=(self.m.digest(raw),base)
        if key not in self.images:
            pe=pefile.PE(data=raw,fast_load=True);image=bytearray(pe.get_memory_mapped_image())
            delta=base-pe.OPTIONAL_HEADER.ImageBase
            if delta:
                for kind,rva in relocation_entries(pe):
                    if kind==3:
                        v,=struct.unpack_from('<I',image,rva);struct.pack_into('<I',image,rva,(v+delta)&0xffffffff)
            self.images[key]=bytes(image)
        image=self.images[key];u=Uc(UC_ARCH_X86,UC_MODE_32)
        u.mem_map(base,(len(image)+4095)&~4095);u.mem_write(base,image)
        u.mem_map(0x30000000,0x10000);u.mem_map(0x40000000,0x10000)
        return u

    def dictionary(self,raw,base):
        u=self.machine(raw,base);dictionary=0x30000400;component=0x30000100
        u.mem_write(component+0x5c,struct.pack('<I',dictionary))
        registers=[UC_X86_REG_EAX,UC_X86_REG_EBX,UC_X86_REG_ECX,UC_X86_REG_EDX,
                   UC_X86_REG_ESI,UC_X86_REG_EDI,UC_X86_REG_EBP,UC_X86_REG_ESP]
        initial=[dictionary,0x11111111,0x22222222,0x33333333,0x44444444,component,0x40008000,0x40006000]
        for r,v in zip(registers,initial):u.reg_write(r,v)
        for i in range(8):u.reg_write(UC_X86_REG_XMM0+i,int.from_bytes(bytes([i+1])*16,'little'))
        u.reg_write(UC_X86_REG_EFLAGS,0xed7)
        before=bytes(u.mem_read(0x30000000,0x10000));rows={};stops=[]
        def hook(emu,address,size,data):
            if address==base+0x1bb79f0:  # Native Dictionary<int,string>.Add interop boundary
                sp=emu.reg_read(UC_X86_REG_ESP)
                ret,d,key,literal,_=struct.unpack('<IIIII',bytes(emu.mem_read(sp,20)))
                self.assertEqual(d,dictionary);self.assertEqual(literal>>29,5)
                text=self.literals[(literal&0x1ffffffe)>>1]
                self.assertNotIn(key,rows);rows[key]=text
                emu.reg_write(UC_X86_REG_ESP,sp+4);emu.reg_write(UC_X86_REG_EIP,ret)
            elif address==base+0x10e1560:  # InitDelegateDict is outside this dictionary's logic
                sp=emu.reg_read(UC_X86_REG_ESP);ret,=struct.unpack('<I',bytes(emu.mem_read(sp,4)))
                emu.reg_write(UC_X86_REG_ESP,sp+4);emu.reg_write(UC_X86_REG_EIP,ret)
            elif address==base+0x2fa147:
                stops.append(address);emu.emu_stop()
        u.hook_add(UC_HOOK_CODE,hook)
        # Executes actual native dictionary insertion instruction sequence, including all four patched PUSHes.
        u.emu_start(base+0x2f9ff2,base+0x2fa148,count=1000)
        self.assertEqual(len(stops),1)
        self.assertEqual(bytes(u.mem_read(0x30000000,0x10000)),before)
        self.assertEqual(u.reg_read(UC_X86_REG_ESP),initial[-1])
        self.assertEqual([u.reg_read(UC_X86_REG_XMM0+i) for i in range(8)],
                         [int.from_bytes(bytes([i+1])*16,'little') for i in range(8)])
        return rows,[u.reg_read(r) for r in registers],u.reg_read(UC_X86_REG_EFLAGS)

    @unittest.skipUnless(Uc is not None and os.environ.get('CBS_MODELS_NATIVE_DLL'),'Exact native image and Unicorn required')
    def test_actual_native_dictionary_matches_inventory_art_without_changing_ids_at_aslr_bases(self):
        import cbs
        for base in (0x10000000,0x18000000):
            with self.subTest(base=hex(base)):
                before,old_regs,old_flags=self.dictionary(self.original,base)
                selected=self.original if os.environ.get('CBS_MODELS_BASELINE') else self.modified
                after,regs,flags=self.dictionary(selected,base)
                self.assertEqual((regs,flags),(old_regs,old_flags))
                self.assertEqual(after[0],'wreck')
                for loot,(inventory_id,design,prefix) in INVENTORY_ART.items():
                    with self.subTest(loot=loot):
                        self.assertEqual((cbs.MODS[loot]['tur'],cbs.MODS[loot]['tasarim']),(inventory_id,design))
                        self.assertEqual(after[design],prefix)
                self.assertEqual(set(after),set(before))

    @unittest.skipUnless(Uc is not None and os.environ.get('CBS_MODELS_NATIVE_DLL'),'Exact native image and Unicorn required')
    def test_real_native_tier_arithmetic_keeps_all_sixteen_levels_and_actual_art_resources(self):
        art=json.loads((ROOT/'docs/cbs-module-art-evidence.json').read_text())
        to_2d={'module_rep':'rep','module_laserhigh':'laser1_','module_lasermid':'laser2_','module_laserlow':'laser3_',
               'module_rocketmid':'rocket1_','module_rocketlow':'rocket2_','module_hon':'hon','module_dama':'dama','module_xp':'xp'}
        for base in (0x10000000,0x18000000):
            mapping,_,_=self.dictionary(self.modified,base)
            u=self.machine(self.modified,base);strings={0x30001000:''};next_string=[0x30002000];stop=[]
            def ret(emu,value):
                sp=emu.reg_read(UC_X86_REG_ESP);addr,=struct.unpack('<I',bytes(emu.mem_read(sp,4)))
                strings[next_string[0]]=value;emu.reg_write(UC_X86_REG_EAX,next_string[0]);next_string[0]+=0x10
                emu.reg_write(UC_X86_REG_ESP,sp+4);emu.reg_write(UC_X86_REG_EIP,addr)
            def hook(emu,address,size,data):
                sp=emu.reg_read(UC_X86_REG_ESP)
                if address==base+0x2218390:  # System.Int32.ToString only; native arithmetic runs above this call
                    ptr,=struct.unpack('<I',bytes(emu.mem_read(sp+4,4)));v,=struct.unpack('<i',bytes(emu.mem_read(ptr,4)));ret(emu,str(v))
                elif address==base+0x208be80:
                    a,b=struct.unpack('<II',bytes(emu.mem_read(sp+4,8)));ret(emu,strings[a]+strings[b])
                elif address==base+0x2b8548:stop.append(address);emu.emu_stop()
            u.hook_add(UC_HOOK_CODE,hook)
            for loot,(_,design,prefix) in INVENTORY_ART.items():
                for level in range(16):
                    with self.subTest(base=hex(base),loot=loot,level=level):
                        strings[0x30001000]=mapping[design];stop.clear()
                        u.reg_write(UC_X86_REG_ESI,design);u.reg_write(UC_X86_REG_EDI,0x30001000)
                        u.reg_write(UC_X86_REG_EBP,0x40008000);u.reg_write(UC_X86_REG_ESP,0x40006000)
                        u.mem_write(0x4000800c,struct.pack('<i',level));u.reg_write(UC_X86_REG_EFLAGS,0xed7)
                        u.emu_start(base+0x2b850c,base+0x2b8549,count=200)
                        expected_tier=1 if level<5 else 2 if level<10 else 3
                        self.assertEqual(strings[u.reg_read(UC_X86_REG_EDI)],prefix+str(expected_tier))
                        actual=to_2d[prefix]+str(expected_tier)+'_2D'
                        row=art['2d_prefabs'][actual]
                        self.assertEqual((len(row['renderers']),len(row['colliders'])),(1,1))
                        self.assertEqual(u.reg_read(UC_X86_REG_ESP),0x40006000)

    @unittest.skipUnless(os.environ.get('CBS_MODELS_NATIVE_DLL'),'Exact native image required')
    def test_all27_actual_sprite_material_collider_and_inventory_pixel_references_match_evidence(self):
        import UnityPy
        art=json.loads((ROOT/'docs/cbs-module-art-evidence.json').read_text())
        bundles=ROOT/'DarkOrbit_Version1.1.115/DarkOrbit_Data/StreamingAssets/aa/BuildTarget'
        for name,sha in art['bundles'].items():self.assertEqual(self.m.digest((bundles/name).read_bytes()),sha)
        e=UnityPy.load(str(bundles/'building_2d_assets_all.bundle'))
        e.load_file(str(bundles/'2dtexture_building_assets_all.bundle'))
        def walk(ptr):
            go=ptr.read()
            for comp in go.m_Component:
                value=comp.component.read();yield comp.component.type.name,value
                if comp.component.type.name=='Transform':
                    for child in value.m_Children:yield from walk(child.read().m_GameObject)
        seen=set()
        for path,ptr in e.container.items():
            name=ptr.read().m_Name
            if name not in art['2d_prefabs']:continue
            seen.add(name);row=art['2d_prefabs'][name]
            with self.subTest(prefab=name):
                sprites=[r for kind,r in walk(ptr) if kind=='SpriteRenderer']
                colliders=[r for kind,r in walk(ptr) if kind=='CircleCollider2D']
                self.assertEqual((len(sprites),len(colliders)),(1,1))
                renderer=sprites[0];sprite=renderer.m_Sprite.read()
                self.assertEqual(self.m.digest(sprite.image.convert('RGBA').tobytes()),row['renderers'][0]['pixel_sha256'])
                self.assertEqual(renderer.m_Materials[0].read().m_Name,'Sprites-Default')
                self.assertEqual([renderer.m_Color.r,renderer.m_Color.g,renderer.m_Color.b,renderer.m_Color.a],[1,1,1,1])
                self.assertEqual((colliders[0].m_Radius,colliders[0].m_Offset.x,colliders[0].m_Offset.y),(60,0,-5))
        self.assertEqual(seen,set(art['2d_prefabs']))
        atlas=UnityPy.load(str(bundles/'atlas_assets_all.bundle'));seen_icons=set()
        for obj in atlas.objects:
            if obj.type.name=='Sprite':
                icon=obj.read()
                if icon.m_Name in art['inventory_icons']:
                    seen_icons.add(icon.m_Name)
                    self.assertEqual(self.m.digest(icon.image.convert('RGBA').tobytes()),art['inventory_icons'][icon.m_Name]['pixel_sha256'])
        self.assertEqual(seen_icons,set(art['inventory_icons']))

    @unittest.skipUnless(os.environ.get('CBS_MODELS_NATIVE_DLL'),'Exact native image required')
    def test_only_four_operand_bytes_change_and_relocations_ai_code_headers_and_resources_stay_exact(self):
        before=pefile.PE(data=self.original,fast_load=True);after=pefile.PE(data=self.modified,fast_load=True)
        changed=[i for i,(a,b) in enumerate(zip(self.original,self.modified)) if a!=b]
        expected=[before.get_offset_from_rva(site)+1 for site in self.m.EXPECTED]
        self.assertEqual(changed,expected);self.assertEqual(len(self.modified),len(self.original))
        self.assertEqual(len(after.sections),len(before.sections))
        self.assertEqual(self.modified[:before.OPTIONAL_HEADER.SizeOfHeaders],self.original[:before.OPTIONAL_HEADER.SizeOfHeaders])
        # No overwritten absolute instruction operand can retain a stale loader fixup.
        for kind,rva in relocation_entries(before):
            if kind==3:
                self.assertFalse(any(rva<site+2 and rva+4>site for site in self.m.EXPECTED))

    def test_unknown_input_is_rejected(self):
        with self.assertRaisesRegex(ValueError,'fingerprint'):self.m.patch_bytes(b'unknown')

    @unittest.skipUnless(os.environ.get('CBS_MODELS_NATIVE_DLL'),'Exact native image required')
    def test_idempotent_application_rollback_and_corruption_rejection_on_temporary_copies(self):
        m=self.m
        with tempfile.TemporaryDirectory() as directory:
            dll=Path(directory)/'GameAssembly.dll';dll.write_bytes(self.original)
            with patch.object(m,'native_client_running',return_value=True):
                with self.assertRaises(RuntimeError):m.apply(dll)
            self.assertEqual(dll.read_bytes(),self.original)
            with patch.object(m,'native_client_running',return_value=False):
                m.apply(dll);m.apply(dll);self.assertEqual(dll.read_bytes(),self.modified)
                damaged=bytearray(self.modified);damaged[-1]^=1;dll.write_bytes(damaged)
                with self.assertRaises(ValueError):m.restore(dll)
                self.assertEqual(dll.read_bytes(),damaged)
                dll.write_bytes(self.modified);m.restore(dll);m.restore(dll)
                self.assertEqual(dll.read_bytes(),self.original)


if __name__=='__main__':unittest.main()
