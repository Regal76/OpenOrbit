"""Execute the scoped native CBS Hangar service hooks without running the client."""
import importlib.util
import os
from pathlib import Path
import struct
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / '_trial/drone-deps'))
try:
    from unicorn import Uc, UC_ARCH_X86, UC_MODE_32
    from unicorn.x86_const import *
except ImportError:
    Uc = None


class CbsHangarCompatibility(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spec = importlib.util.spec_from_file_location('hangar_compat', ROOT / 'tools/cbs_hangar_button_compat.py')
        cls.mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.mod)
        cls.original = None
        cls.mapped = {}
        fixture = os.environ.get('CBS_HANGAR_NATIVE_DLL')
        if fixture:
            raw = Path(fixture).read_bytes()
            if cls.mod.digest(raw) != cls.mod.ORIGINAL_SHA256:
                sp = importlib.util.spec_from_file_location('shield', ROOT / 'tools/cbs_shield_speed_compat.py')
                shield = importlib.util.module_from_spec(sp);sp.loader.exec_module(shield)
                raw = shield.patch_bytes(raw, 'native')
            cls.original = raw
            cls.modified = cls.mod.patch_bytes(raw)

    def test_unknown_binary_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'fingerprint'):
            self.mod.patch_bytes(b'unknown')

    def emulator(self, base):
        import pefile
        if base not in self.mapped:
            p = pefile.PE(data=self.modified, fast_load=True)
            self.mapped[base] = p.get_memory_mapped_image()
        u = Uc(UC_ARCH_X86, UC_MODE_32)
        mapped = self.mapped[base]
        u.mem_map(base, (len(mapped) + 4095) & ~4095);u.mem_write(base, mapped)
        u.mem_map(0x30000000, 0x10000);u.mem_map(0x40000000, 0x10000)
        return u

    def setup_command(self, u, uid, kind=48, name='refinery_invisible_0'):
        obj, type_ptr, name_ptr = 0x30000100, 0x30000200, 0x30000300
        encoded = name.encode('utf-16le')
        u.mem_write(name_ptr, b'\0' * 8 + struct.pack('<I', len(encoded)//2) + encoded + b'\0\0')
        u.mem_write(obj, b'\0' * 0x50)
        u.mem_write(obj+12, struct.pack('<I', name_ptr))
        u.mem_write(obj+28, struct.pack('<I', type_ptr))
        u.mem_write(obj+40, struct.pack('<I', uid))
        u.mem_write(type_ptr+8, struct.pack('<I', kind))
        return obj, name_ptr

    @unittest.skipUnless(Uc is not None and os.environ.get('CBS_HANGAR_NATIVE_DLL'), 'Native fixture required')
    def test_exact_helper_ids_select_empty_pattern_but_icon_queries_use_real_hangar_pattern(self):
        for base in [0x10000000, 0x18000000]:
            for uid, kind, name, icon, selected in [
                    *[(159500000+i,48,'refinery_invisible_0',False,True) for i in range(1,24)],
                    (159500001,48,'refinery_invisible_0',True,False),
                    (159500000,48,'refinery_invisible_0',False,False),
                    (159500024,48,'refinery_invisible_0',False,False),
                    (159500001,36,'refinery_invisible_0',False,False),
                    (159500001,48,'refinery_invisible_0_extra',False,False),
                    (159500001,48,'refinery_invisible_1',False,False)]:
                with self.subTest(base=base, uid=uid, kind=kind, icon=icon, name=name):
                    u=self.emulator(base);obj,name_ptr=self.setup_command(u,uid,kind,name)
                    esp=0x40008000;ret=base+self.mod.ICON_CALL_RETURN_RVA if icon else 0x30000000
                    u.mem_write(esp,struct.pack('<III',ret,obj,0));u.reg_write(UC_X86_REG_ESP,esp)
                    regs=[UC_X86_REG_EBX,UC_X86_REG_ESI,UC_X86_REG_EDI,UC_X86_REG_ECX,UC_X86_REG_EDX]
                    values=[0x12340000+i for i in range(len(regs))]
                    for r,v in zip(regs,values):u.reg_write(r,v)
                    before=bytes(u.mem_read(obj,0x50))
                    end=ret if selected else base+self.mod.PATTERN_ENTRY_RVA+6
                    u.emu_start(base+self.mod.PATTERN_ENTRY_RVA,end,count=1000)
                    self.assertEqual([u.reg_read(r) for r in regs],values)
                    self.assertEqual(bytes(u.mem_read(obj,0x50)),before)
                    if selected:
                        self.assertEqual(u.reg_read(UC_X86_REG_EAX),name_ptr)
                        self.assertEqual(u.reg_read(UC_X86_REG_ESP),esp+4)
                    else:
                        self.assertEqual(u.reg_read(UC_X86_REG_ESP),esp-20)

    @unittest.skipUnless(Uc is not None and os.environ.get('CBS_HANGAR_NATIVE_DLL'), 'Native fixture required')
    def test_only_helper_creation_loads_existing_empty_prefab_and_retains_asset_type(self):
        for base in [0x10000000,0x18000000]:
            for uid,kind,name,selected in [(159500001,48,'refinery_invisible_0',True),
                    (159500023,48,'refinery_invisible_0',True),
                    (159500024,48,'refinery_invisible_0',False),(159500001,36,'refinery_invisible_0',False),
                    (159500001,48,'other',False)]:
                with self.subTest(uid=uid,kind=kind,name=name,base=base):
                    u=self.emulator(base);obj,_=self.setup_command(u,uid,kind,name)
                    ebp,esp,state,build=0x40008000,0x40006000,0x30000400,0x30000500
                    blank,old=0x30000600,0x30000700
                    u.mem_write(base+self.mod.EMPTY_PREFAB_GLOBAL_RVA,struct.pack('<I',blank))
                    u.mem_write(state+8,struct.pack('<I',obj))
                    u.mem_write(ebp+8,struct.pack('<I',state));u.mem_write(ebp-0x24,struct.pack('<I',build))
                    u.mem_write(ebp-0x18,struct.pack('<I',old))
                    u.reg_write(UC_X86_REG_EBP,ebp);u.reg_write(UC_X86_REG_ESP,esp)
                    u.reg_write(UC_X86_REG_ESI,old)
                    before=bytes(u.mem_read(obj,0x50))
                    u.emu_start(base+self.mod.PREFAB_JOIN_RVA,base+self.mod.PREFAB_JOIN_RVA+6,count=1000)
                    self.assertEqual(u.reg_read(UC_X86_REG_ESP),esp)
                    self.assertEqual(u.reg_read(UC_X86_REG_EBP),ebp)
                    self.assertEqual(u.reg_read(UC_X86_REG_EAX),state)
                    self.assertEqual(u.reg_read(UC_X86_REG_EDI),build)
                    self.assertEqual(u.reg_read(UC_X86_REG_ESI),blank if selected else old)
                    self.assertEqual(struct.unpack('<I',u.mem_read(ebp-0x18,4))[0],blank if selected else old)
                    self.assertEqual(bytes(u.mem_read(obj,0x50)),before)

    @unittest.skipUnless(Uc is not None and os.environ.get('CBS_HANGAR_NATIVE_DLL'), 'Native fixture required')
    def test_blank_helper_skips_hangar_animation_requirement_only_for_its_own_instance(self):
        for base in [0x10000000,0x18000000]:
            for uid,kind,name,selected in [(159500001,48,'refinery_invisible_0',True),
                    (159500024,48,'refinery_invisible_0',False),(159500001,36,'refinery_invisible_0',False),
                    (159500001,48,'other',False)]:
                with self.subTest(uid=uid,kind=kind,name=name,base=base):
                    u=self.emulator(base);obj,_=self.setup_command(u,uid,kind,name)
                    build=0x30000900;u.mem_write(build+12,struct.pack('<I',obj))
                    esp=0x40008000;ret=0x30000000
                    u.mem_write(esp,struct.pack('<IIII',ret,0x30000500,0,0))
                    u.reg_write(UC_X86_REG_ESP,esp);u.reg_write(UC_X86_REG_EDI,build)
                    # Enter the actual patched call using its existing arguments.
                    u.reg_write(UC_X86_REG_ESP,esp+4)
                    end=base+self.mod.ANIMATION_CALL_RVA+5 if selected else base+self.mod.SET_ANIMATION_RVA
                    u.emu_start(base+self.mod.ANIMATION_CALL_RVA,end,count=1000)
                    self.assertEqual(u.reg_read(UC_X86_REG_ESP),esp+4 if selected else esp)
                    self.assertEqual(u.reg_read(UC_X86_REG_EDI),build)

    def test_shipped_blank_prefab_has_no_renderer_or_children(self):
        explicit = os.environ.get('CBS_HANGAR_BUNDLE')
        bundle = Path(explicit) if explicit else ROOT/'DarkOrbit_Version1.1.115/DarkOrbit_Data/StreamingAssets/aa/BuildTarget/building_2d_assets_all.bundle'
        if not explicit and not bundle.is_file():
            self.skipTest('Optional building bundle absent; set CBS_HANGAR_BUNDLE')
        raw = bundle.read_bytes()  # An explicit missing fixture must fail.
        try:
            import UnityPy
        except ImportError:
            self.skipTest('Optional bundle replay requires UnityPy')
        env=UnityPy.load(raw)
        pointer=next(p for k,p in env.container.items() if k.endswith('/refinery_invisible.prefab'))
        root=pointer.read().object_reader;tree=root.read_typetree()
        components=[root.assets_file.objects[c['component']['m_PathID']] for c in tree['m_Component']]
        self.assertEqual([o.type.name for o in components],['Transform'])
        self.assertEqual(components[0].read_typetree()['m_Children'],[])

    @unittest.skipUnless(os.environ.get('CBS_HANGAR_NATIVE_DLL'), 'Native fixture required')
    def test_patch_preserves_prior_sections_and_apply_restore_is_exact(self):
        import pefile
        m=self.mod;a=pefile.PE(data=self.original,fast_load=True)
        changed={a.get_offset_from_rva(rva)+i for rva,raw in m.EXPECTED.items() for i in range(len(raw))}
        for section in a.sections:
            start=section.PointerToRawData;end=start+section.SizeOfRawData
            self.assertEqual(bytes(x for i,x in enumerate(self.original[start:end],start) if i not in changed),
                             bytes(x for i,x in enumerate(self.modified[start:end],start) if i not in changed))
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/'GameAssembly.dll';path.write_bytes(self.original)
            with patch.object(m,'native_client_running',return_value=True):
                with self.assertRaises(RuntimeError):m.apply(path)
            with patch.object(m,'native_client_running',return_value=False):
                m.apply(path);first=path.read_bytes();m.apply(path);self.assertEqual(path.read_bytes(),first)
                m.restore(path);self.assertEqual(path.read_bytes(),self.original)
                m.restore(path);self.assertEqual(path.read_bytes(),self.original)

if __name__=='__main__':unittest.main()
