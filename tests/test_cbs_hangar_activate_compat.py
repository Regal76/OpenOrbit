"""Native Activate accepts docking without granting a peaceful CBS area."""
import importlib.util
import os
from pathlib import Path
import struct
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'_trial/drone-deps'))
try:
    from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_CODE
    from unicorn.x86_const import *
except ImportError:Uc=None


def load(path,name):
    spec=importlib.util.spec_from_file_location(name,ROOT/path)
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);return mod


class HangarActivate(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.m=load('tools/cbs_hangar_activate_compat.py','activate_compat')
        cls.original=None;cls.images={}
        fixture=os.environ.get('CBS_ACTIVATE_NATIVE_DLL')
        if fixture:
            raw=Path(fixture).read_bytes()
            if cls.m.digest(raw)!=cls.m.ORIGINAL_SHA256:
                helper=load('tools/cbs_hangar_button_compat.py','helper_compat')
                if helper.digest(raw)!=helper.ORIGINAL_SHA256:
                    shield=load('tools/cbs_shield_speed_compat.py','shield_compat')
                    raw=shield.patch_bytes(raw,'native')
                raw=helper.patch_bytes(raw)
            cls.original=raw;cls.modified=cls.m.patch_bytes(raw)

    def test_unknown_binary_is_rejected(self):
        with self.assertRaisesRegex(ValueError,'fingerprint'):self.m.patch_bytes(b'unknown')

    def execute(self,raw,base,peace,station):
        import pefile
        key=(raw,base)
        if key not in self.images:self.images[key]=pefile.PE(data=raw,fast_load=True).get_memory_mapped_image()
        image=self.images[key];u=Uc(UC_ARCH_X86,UC_MODE_32)
        u.mem_map(base,(len(image)+4095)&~4095);u.mem_write(base,image)
        heap,stack=0x30000000,0x40000000
        u.mem_map(heap,0x10000);u.mem_map(stack,0x10000)
        settings,bindable=heap+0x100,heap+0x400
        u.mem_write(settings,b'\0'*0x200);u.mem_write(settings+0xd0,bytes([int(peace)]))
        u.mem_write(settings+0xd4,struct.pack('<I',0 if station is None else bindable))
        u.mem_write(bindable+0xc,bytes([int(bool(station))]))
        before=bytes(u.mem_read(settings,0x200));stack_before=bytes(u.mem_read(stack,0x10000))
        regs=[UC_X86_REG_EAX,UC_X86_REG_EBX,UC_X86_REG_ECX,UC_X86_REG_EDX,
              UC_X86_REG_ESI,UC_X86_REG_EDI,UC_X86_REG_EBP,UC_X86_REG_ESP]
        values=[settings,0x11111111,0x22222222,0x33333333,0x44444444,0x55555555,stack+0x8000,stack+0x6000]
        for r,v in zip(regs,values):u.reg_write(r,v)
        for i in range(8):u.reg_write(UC_X86_REG_XMM0+i,int.from_bytes(bytes([i+1])*16,'little'))
        xmm=[u.reg_read(UC_X86_REG_XMM0+i) for i in range(8)]
        u.reg_write(UC_X86_REG_EFLAGS,0x646)
        observed=[]
        def stop(emu,address,size,data):
            if address in [base+self.m.ALLOWED_RVA,base+self.m.DENIED_RVA]:
                observed.append(address-base);emu.emu_stop()
        u.hook_add(UC_HOOK_CODE,stop)
        u.emu_start(base+self.m.GUARD_RVA,base+self.m.DENIED_RVA+1,count=300)
        self.assertEqual([u.reg_read(r) for r in regs],values)
        self.assertEqual([u.reg_read(UC_X86_REG_XMM0+i) for i in range(8)],xmm)
        self.assertEqual(bytes(u.mem_read(settings,0x200)),before)
        # Temporary stack saves are permissible; no live argument/return slot changes.
        self.assertEqual(bytes(u.mem_read(values[-1],0x1000)),stack_before[0x6000:0x7000])
        self.assertEqual(len(observed),1)
        return observed[0],u.reg_read(UC_X86_REG_EFLAGS)

    @unittest.skipUnless(Uc is not None and os.environ.get('CBS_ACTIVATE_NATIVE_DLL'),'Native fixture required')
    def test_all_station_peace_paths_aslr_and_context(self):
        for base in [0x10000000,0x18000000]:
            for peace in [False,True]:
                for station in [None,False,True]:
                    with self.subTest(base=base,peace=peace,station=station):
                        old,flags=self.execute(self.original,base,peace,station)
                        new,new_flags=self.execute(self.modified,base,peace,station)
                        self.assertEqual(old,self.m.ALLOWED_RVA if peace else self.m.DENIED_RVA)
                        self.assertEqual(new,self.m.ALLOWED_RVA if peace or station else self.m.DENIED_RVA)
                        self.assertEqual(flags,new_flags)

    @unittest.skipUnless(os.environ.get('CBS_ACTIVATE_NATIVE_DLL'),'Native fixture required')
    def test_all_prior_patch_sections_and_exact_rollback(self):
        import pefile
        m=self.m;p=pefile.PE(data=self.original,fast_load=True)
        at=p.get_offset_from_rva(m.GUARD_RVA)
        changed=set(range(at,at+len(m.EXPECTED)))
        for section in p.sections:
            start=section.PointerToRawData;end=start+section.SizeOfRawData
            self.assertEqual(bytes(x for i,x in enumerate(self.original[start:end],start) if i not in changed),
                             bytes(x for i,x in enumerate(self.modified[start:end],start) if i not in changed))
        with tempfile.TemporaryDirectory() as directory:
            dll=Path(directory)/'GameAssembly.dll';dll.write_bytes(self.original)
            with patch.object(m,'native_client_running',return_value=True):
                with self.assertRaises(RuntimeError):m.apply(dll)
            self.assertEqual(dll.read_bytes(),self.original)
            with patch.object(m,'native_client_running',return_value=False):
                m.apply(dll);modified=dll.read_bytes();m.apply(dll);self.assertEqual(dll.read_bytes(),modified)
                corrupt=bytearray(modified);corrupt[-1]^=1;dll.write_bytes(corrupt)
                with self.assertRaises(ValueError):m.restore(dll)
                self.assertEqual(dll.read_bytes(),corrupt)
                dll.write_bytes(modified);m.restore(dll);m.restore(dll)
                self.assertEqual(dll.read_bytes(),self.original)

if __name__=='__main__':unittest.main()
