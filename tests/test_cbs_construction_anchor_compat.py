"""Run construction anchoring after actual PE HIGHLOW relocations."""
from pathlib import Path
import importlib.util,os,struct,sys,tempfile,unittest
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'));sys.path.insert(0,str(ROOT/'_trial/drone-deps'))
try:
    import pefile
except ImportError:
    pefile=None
try:
    from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_CODE
    from unicorn.x86_const import *
except ImportError:
    Uc=None
DLL=ROOT/'DarkOrbit_Version1.1.115/GameAssembly.dll'

class ConstructionAnchor(unittest.TestCase):
    def module(self):
        path=ROOT/'tools/cbs_construction_anchor_compat.py';self.assertTrue(path.exists(),'Construction anchor implementation missing')
        spec=importlib.util.spec_from_file_location('construction_anchor',path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
    def fixture(self,m):
        explicit=os.environ.get('CBS_CONSTRUCTION_NATIVE_DLL')
        path=Path(explicit) if explicit else DLL
        if not explicit and not path.exists():
            self.skipTest('Optional native fixture absent; set CBS_CONSTRUCTION_NATIVE_DLL')
        raw=path.read_bytes()  # Explicit missing or malformed fixtures must fail.
        if m.digest(raw)!=m.ORIGINAL_SHA256 and not explicit:
            raw=m.backup_path(path).read_bytes()
        self.assertEqual(m.digest(raw),m.ORIGINAL_SHA256,'Unsupported construction native fixture fingerprint')
        if pefile is None or Uc is None:
            self.skipTest('Optional construction replay requires pefile and Unicorn')
        return raw
    def machine(self,raw,base):
        pe=pefile.PE(data=raw,fast_load=True);im=bytearray(pe.get_memory_mapped_image());delta=base-pe.OPTIONAL_HEADER.ImageBase
        d=pe.OPTIONAL_HEADER.DATA_DIRECTORY[5];p=d.VirtualAddress
        while p<d.VirtualAddress+d.Size:
            page,size=struct.unpack_from('<II',im,p)
            if not size:break
            for at in range(p+8,p+size,2):
                e=struct.unpack_from('<H',im,at)[0]
                if e>>12==3:
                    rva=page+(e&4095);v=struct.unpack_from('<I',im,rva)[0];struct.pack_into('<I',im,rva,(v+delta)&0xffffffff)
            p+=size
        u=Uc(UC_ARCH_X86,UC_MODE_32);u.mem_map(base,(len(im)+4095)&~4095);u.mem_write(base,bytes(im));u.mem_map(0x50000000,0x20000);u.mem_map(0x60000000,0x10000);return u
    def execute(self,raw,base,kind):
        u=self.machine(raw,base);heap=0x50000000;sp=0x60008000;bp=sp+0x100;selfptr,effect,source,klass,other,go,parent=[heap+x for x in [0x100,0x200,0x300,0x400,0x500,0x600,0x700]]
        w=lambda a,v:u.mem_write(a,struct.pack('<I',v));r=lambda a:struct.unpack('<I',bytes(u.mem_read(a,4)))[0]
        w(bp+8,0 if kind=='null_self' else selfptr);w(selfptr+8,0 if kind=='null_effect' else effect);w(effect+0x34,0 if kind=='null_source' else source);w(source,other if kind=='other' else klass);w(source+0x40,heap+0x900) # hidden 3D model must never become the parent
        component=heap+0x800;w(component+0x68,0 if kind=='null_model' else go);w(base+0x34050c4,klass);w(base+0x3420300,heap+0xa00)
        initial={UC_X86_REG_EAX:parent if kind=='unit' else 0,UC_X86_REG_EBX:0x12345678,UC_X86_REG_ECX:0x22334455,UC_X86_REG_EDX:0x33445566,UC_X86_REG_ESI:0x44556677,UC_X86_REG_EDI:0x55667788,UC_X86_REG_EBP:bp}
        for reg,value in initial.items():u.reg_write(reg,value)
        u.reg_write(UC_X86_REG_ESP,sp);u.reg_write(UC_X86_REG_EFLAGS,0x246)
        xmm={UC_X86_REG_XMM0+i:(i+1)*0x123456789abcdef123456789abcdef for i in range(8)}
        for reg,value in xmm.items():u.reg_write(reg,value)
        calls=[]
        def hook(emu,address,size,data):
            rva=address-base
            if rva in [0x1ef640,0x2920880,0x17b13a0]:
                esp=emu.reg_read(UC_X86_REG_ESP);ret=r(esp)
                if rva==0x1ef640:self.assertIn(r(esp+4),[base+0x34050c4,base+0x3420300]);calls.append('metadata');value=0
                elif rva==0x17b13a0:
                    self.assertEqual(r(esp+4),source);self.assertEqual(r(esp+8),heap+0xa00);calls.append('component');value=0 if kind=='null_component' else component
                else:self.assertEqual(r(esp+4),go);calls.append('transform');value=parent
                emu.reg_write(UC_X86_REG_EAX,value);emu.reg_write(UC_X86_REG_ECX,7);emu.reg_write(UC_X86_REG_EDX,9);emu.reg_write(UC_X86_REG_XMM0,7)
                emu.reg_write(UC_X86_REG_ESP,esp+4);emu.reg_write(UC_X86_REG_EIP,ret)
        u.hook_add(UC_HOOK_CODE,hook);u.emu_start(base+0x762f9f,base+0x762fa7,count=1500)
        self.assertEqual(u.reg_read(UC_X86_REG_ESP),sp)
        for reg,value in initial.items():self.assertEqual(u.reg_read(reg),parent if reg==UC_X86_REG_EAX and kind in ['build','unit'] else value)
        for reg,value in xmm.items():self.assertEqual(u.reg_read(reg),value)
        self.assertEqual(u.reg_read(UC_X86_REG_EFLAGS)&0x8d5,4) # TEST EBX,EBX: positive nonzero, low byte even parity
        return calls
    def test_loader_relocated_build_unit_null_and_other_cases_preserve_context(self):
        m=self.module();raw=m.patch_bytes(self.fixture(m))
        for base in [0x10000000,0x18000000,0x75420000]:
            for kind in ['build','unit','null_self','null_effect','null_source','null_component','null_model','other']:
                with self.subTest(base=hex(base),kind=kind):
                    calls=self.execute(raw,base,kind)
                    self.assertEqual('transform' in calls,kind=='build')
    def test_prior_sections_and_relocations_unchanged_except_hook_and_pe_sizes(self):
        m=self.module();original=self.fixture(m);modified=m.patch_bytes(original);old=pefile.PE(data=original);new=pefile.PE(data=modified)
        self.assertEqual(old.OPTIONAL_HEADER.DATA_DIRECTORY[5].__pack__(),new.OPTIONAL_HEADER.DATA_DIRECTORY[5].__pack__())
        site=old.get_offset_from_rva(m.ENTRY_RVA)
        for sec in old.sections:
            start=sec.PointerToRawData;end=start+sec.SizeOfRawData
            if start<=site<end:
                self.assertEqual(original[start:site],modified[start:site])
                self.assertEqual(original[site+len(m.ORIGINAL_BYTES):end],modified[site+len(m.ORIGINAL_BYTES):end])
            else:self.assertEqual(original[start:end],modified[start:end])
    def test_prepare_apply_restore_and_running_guard(self):
        m=self.module();original=self.fixture(m)
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'GameAssembly.dll';p.write_bytes(original)
            m.prepare(p,Path(d)/'prepared');self.assertEqual(p.read_bytes(),original)
            with patch.object(m,'native_client_running',return_value=True):
                with self.assertRaises(RuntimeError):m.apply(p)
            with patch.object(m,'native_client_running',return_value=False):
                first=m.apply(p);self.assertEqual(m.apply(p),first);modified=p.read_bytes();p.write_bytes(modified+b'bad')
                with self.assertRaises(ValueError):m.restore(p)
                p.write_bytes(modified);m.restore(p);self.assertEqual(p.read_bytes(),original)

if __name__=='__main__':unittest.main()
