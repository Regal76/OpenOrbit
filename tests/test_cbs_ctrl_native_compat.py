"""Native Ctrl event/request/toggle regression; Unity and network boundaries are stubbed."""
import hashlib
import importlib.util
import os
from pathlib import Path
import struct
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'_trial/drone-deps'));sys.path.insert(0,str(ROOT/'tools'))
try:
    import pefile
    from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_CODE
    from unicorn.x86_const import UC_X86_REG_EAX,UC_X86_REG_EDX,UC_X86_REG_EIP,UC_X86_REG_ESP
except ImportError:Uc=None
TOOL=ROOT/'tools/cbs_ctrl_native_compat.py'
DLL=ROOT/'DarkOrbit_Version1.1.115/GameAssembly.dll'
BACKUP=Path(str(DLL)+'.cbs-ctrl.original')
FIXTURE=Path(os.environ.get('CBS_CTRL_NATIVE_DLL',str(BACKUP if BACKUP.exists() else DLL)))


@unittest.skipUnless(Uc is not None and FIXTURE.exists(),'Exact native fixture and Unicorn required')
class CtrlNative(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original=FIXTURE.read_bytes();cls.tool=None
        if TOOL.exists():
            spec=importlib.util.spec_from_file_location('cbs_ctrl',TOOL);cls.tool=importlib.util.module_from_spec(spec);spec.loader.exec_module(cls.tool)
        cls.modified=cls.tool.patch_bytes(cls.original) if cls.tool else cls.original

    def machine(self,raw,kind='building',uid=402,base=0x10000000):
        pe=pefile.PE(data=raw,fast_load=True);image=bytearray(pe.get_memory_mapped_image());delta=base-pe.OPTIONAL_HEADER.ImageBase
        directory=pe.OPTIONAL_HEADER.DATA_DIRECTORY[5];cursor,end=directory.VirtualAddress,directory.VirtualAddress+directory.Size
        while cursor<end:
            page,size=struct.unpack_from('<II',image,cursor)
            if not size:break
            for at in range(cursor+8,cursor+size,2):
                entry,=struct.unpack_from('<H',image,at)
                if entry>>12==3:
                    rva=page+(entry&4095);value,=struct.unpack_from('<I',image,rva);struct.pack_into('<I',image,rva,(value+delta)&0xffffffff)
            cursor+=size
        u=Uc(UC_ARCH_X86,UC_MODE_32);u.mem_map(base,(len(image)+4095)&~4095);u.mem_write(base,bytes(image))
        heap,stack=0x50000000,0x60000000;u.mem_map(heap,0x20000);u.mem_map(stack,0x10000)
        w32=lambda a,v:u.mem_write(a,struct.pack('<I',v&0xffffffff))
        r32=lambda a:struct.unpack('<I',bytes(u.mem_read(a,4)))[0]
        classes={};nextclass=heap+0x100
        def klass(global_rva):
            nonlocal nextclass
            address=nextclass;nextclass+=0x200;classes[global_rva]=address
            w32(base+global_rva,address);w32(address+0x74,1);w32(address+0x5c,address+0x100);w32(address+0x20,global_rva)
            return address
        for rva in (0x340c1f8,0x33f6380,0x3402aac,0x3419bcc,0x33ce0e0,0x340ba6c,0x34050c4,0x34101b8,
                    0x33f4058,0x33e329c,0x33e4348,0x33e22dc,0x33f3e30,0x33f3954,0x33e4f7c,0x33cb8fc,0x33cc2a4,0x33cc3bc):klass(rva)
        helperstat=classes[0x340c1f8]+0x100
        scene,hero,target,info,ship,unitwrapper,keyboard= [heap+x for x in (0x6000,0x6200,0x6400,0x6600,0x6800,0x6a00,0x6c00)]
        w32(helperstat,0 if kind=='null' else target)
        w32(classes[0x33f6380]+0x100+0xc,scene)
        w32(classes[0x3402aac]+0x100+0xc,177)
        w32(classes[0x3419bcc]+0x100+0x28,heap+0x6e00)
        w32(classes[0x33cb8fc]+0x100+0x1ac,heap+0x7000);u.mem_write(heap+0x7000+0xc,b'\x01')
        w32(target,classes[0x34050c4] if kind=='building' else classes[0x340ba6c])
        w32(target+0x30,uid);w32(target+0x34,-1 if uid==-1 else 0)
        w32(ship+0x48,info);w32(unitwrapper+0x38,info);w32(info,classes[0x33ce0e0]);w32(info+0x98,hero)
        for cl in (classes[0x340ba6c],classes[0x33ce0e0]):
            u.mem_write(cl+0xb8,b'\x01');w32(cl+0x64,heap+0x7200+(cl-heap));w32(heap+0x7200+(cl-heap),cl)
        for rva in (0x34fae0c,0x34fa678,0x34fa78b,0x34fcc19,0x34fcc1a,0x34faae8):u.mem_write(base+rva,b'\x01')
        events,requests,errors=[],[],[];nextbox=heap+0x9000;nextrequest=heap+0xe000
        enumglobals=(0x33e329c,0x33e22dc)
        def finish(emu,eax=None,edx=None):
            sp=emu.reg_read(UC_X86_REG_ESP);ret=r32(sp)
            if eax is not None:emu.reg_write(UC_X86_REG_EAX,eax)
            if edx is not None:emu.reg_write(UC_X86_REG_EDX,edx)
            emu.reg_write(UC_X86_REG_ESP,sp+4);emu.reg_write(UC_X86_REG_EIP,ret)
        def hook(emu,address,size,data):
            nonlocal nextbox,nextrequest
            rva=address-base;sp=emu.reg_read(UC_X86_REG_ESP)
            if rva in (0x1eeac0,0x1ef8a0):errors.append('invalid cast' if rva==0x1eeac0 else 'null object');emu.emu_stop()
            elif rva==0x2eb5e0:finish(emu,hero)
            elif rva==0x2de070:finish(emu,keyboard)
            elif rva==0x101db00:
                obj,value=r32(sp+4),r32(sp+8);u.mem_write(obj+0xc,bytes([value&255]));finish(emu)
            elif rva==0x17b13a0:
                obj,method=r32(sp+4),r32(sp+8)
                result=ship if method==r32(base+0x33c5e70) else unitwrapper
                finish(emu,result if obj==hero else 0)
            elif rva in (0x2375c0,):
                w32(heap+0x7400,heap+0x1f000);w32(heap+0x7404,0);finish(emu,heap+0x7400)
            elif address==heap+0x1f000:finish(emu,uid,-1 if uid==-1 else 0)
            elif rva==0x37f608 and kind=='null':self.fail('null target must not reach cast')
            elif rva==0x10098f0:finish(emu,hero)
            elif rva==0x1eea40:
                cl,source=r32(sp+4),r32(sp+8);obj=nextbox;nextbox+=0x80
                size=4 if cl in [classes[g] for g in enumglobals] else 8 if cl==classes[0x33f4058] else 16
                w32(obj,cl);u.mem_write(obj+8,bytes(u.mem_read(source,size)));finish(emu,obj)
            elif rva==0x1eec30:finish(emu,r32(sp+4)+8)
            elif rva==0x1eea70:finish(emu)
            elif rva==0xf7c220:finish(emu,int(r32(sp+4)==hero))
            elif rva==0x73a0e0:
                event,payload=r32(sp+8),r32(sp+12);events.append((r32(event+8),payload));finish(emu)
            elif rva==0x0034c0:
                slot,cl,obj=r32(sp+4),r32(sp+8),r32(sp+12)
                finish(emu,uid if slot==1 else obj,0)
            elif rva==0x0037d0:
                out,slot,cl,obj=r32(sp+4),r32(sp+8),r32(sp+12),r32(sp+16)
                self.assertEqual(obj,target);u.mem_write(out,struct.pack('<fff',9137.75,0,7282.25));finish(emu,out)
            elif rva==0x1ac3a0:
                obj=nextrequest;nextrequest+=0x80;w32(obj,r32(sp+4));finish(emu,obj)
            elif rva==0x2c8ef0:
                obj=r32(sp+8);cl=r32(obj)
                if cl==classes[0x33f3e30]:requests.append(('laser',struct.unpack('<iii',bytes(u.mem_read(obj+8,12)))))
                elif cl==classes[0x33f3954]:requests.append(('abort',None))
                else:self.fail('Unexpected native request type')
                finish(emu)
            elif rva in (0x7a5a90,0x7a8b00):finish(emu)
        u.hook_add(UC_HOOK_CODE,hook)
        def invoke(rva,args):
            sp=stack+0x8000;end=stack+0xf000
            u.mem_write(sp,struct.pack('<'+'I'*(len(args)+1),end,*args));u.reg_write(UC_X86_REG_ESP,sp)
            try:u.emu_start(base+rva,end,count=15000)
            except Exception as error:raise RuntimeError('native EIP='+hex(u.reg_read(UC_X86_REG_EIP))) from error
        def ctrl():invoke(0x37f270,[heap+0x7600,0])
        def dispatch():
            event,payload=events[-1]
            invoke(0x7127c0 if event==6 else 0x3183b0,[heap+0x7600,payload,0])
        return dict(ctrl=ctrl,dispatch=dispatch,events=events,requests=requests,errors=errors,u=u,info=info,keyboard=keyboard,r32=r32,w32=w32,target=target)

    def test_ctrl_building_start_stop_restart_uses_existing_native_events_and_requests(self):
        for base in (0x10000000,0x30000000):
            with self.subTest(base=hex(base)):
                m=self.machine(self.modified,base=base);m['ctrl']()
                self.assertEqual(m['errors'],[]);self.assertEqual(m['events'][-1][0],6)
                self.assertEqual(m['r32'](m['info']+0xa0),m['target'])
                self.assertEqual(bytes(m['u'].mem_read(m['keyboard']+0xc,1)),b'\x01')
                m['dispatch']();self.assertEqual(m['requests'],[('laser',(402,9138,7282))])
                m['u'].mem_write(m['info']+0x84,b'\x01') # native server LaserRun acknowledgement
                m['ctrl']();self.assertEqual(m['events'][-1][0],0)
                self.assertEqual(bytes(m['u'].mem_read(m['info']+0x84,1)),b'\x00')
                self.assertEqual(bytes(m['u'].mem_read(m['keyboard']+0xc,1)),b'\x00')
                m['dispatch']();self.assertEqual(m['requests'][-1],('abort',None))
                self.assertEqual(m['r32'](m['info']+0xa0),0)
                m['ctrl']();self.assertEqual(m['events'][-1][0],6);m['dispatch']()
                self.assertEqual([r[0] for r in m['requests']],['laser','abort','laser'])
                self.assertEqual(m['errors'],[])

    def test_original_ctrl_rejects_building_before_attack_event(self):
        m=self.machine(self.original);m['ctrl']()
        self.assertEqual(m['errors'],['invalid cast']);self.assertEqual(m['events'],[])

    def test_unit_target_keeps_native_start_stop_events(self):
        for raw in (self.original,self.modified):
            m=self.machine(raw,kind='ship',uid=199);m['ctrl']()
            self.assertEqual(m['errors'],[]);self.assertEqual(m['events'][-1][0],6)
            m['dispatch']();self.assertEqual(m['requests'],[('laser',(199,9138,7282))])
            m['ctrl']();self.assertEqual(m['events'][-1][0],0);m['dispatch']()
            self.assertEqual(m['requests'][-1],('abort',None));self.assertEqual(m['r32'](m['info']+0xa0),0)

    def test_invalid_id_keeps_native_no_attack_guard(self):
        m=self.machine(self.modified,uid=-1);m['ctrl']()
        self.assertEqual(m['events'],[]);self.assertEqual(m['requests'],[]);self.assertEqual(m['errors'],[])
    def test_patch_preserves_prior_rocket_hook_all_code_and_loader_relocations(self):
        m=self.tool
        self.assertIsNotNone(m)
        self.assertEqual(hashlib.sha256(self.original).hexdigest(),m.ORIGINAL_SHA256)
        self.assertEqual(hashlib.sha256(self.modified).hexdigest(),m.MODIFIED_SHA256)
        pe=pefile.PE(data=self.original,fast_load=True)
        restored=bytearray(self.modified[:len(self.original)])
        site=pe.get_offset_from_rva(m.ENTRY_RVA)
        restored[site:site+len(m.ORIGINAL_BYTES)]=self.original[site:site+len(m.ORIGINAL_BYTES)]
        optional=pe.DOS_HEADER.e_lfanew+24
        last_header=pe.sections[-1].get_file_offset()
        for at in (optional+4,optional+56,last_header+8,last_header+16):
            restored[at:at+4]=self.original[at:at+4]
        self.assertEqual(bytes(restored),self.original)
        with self.assertRaises(ValueError):m.patch_bytes(self.original[:-1]+b'!')

    def test_apply_restore_fingerprint_and_live_client_guards(self):
        m=self.tool
        self.assertIsNotNone(m)
        with tempfile.TemporaryDirectory() as folder:
            dll=Path(folder)/'GameAssembly.dll';dll.write_bytes(self.original)
            with patch.object(m,'native_client_running',return_value=True):
                with self.assertRaises(RuntimeError):m.apply(dll)
            self.assertEqual(dll.read_bytes(),self.original)
            with patch.object(m,'native_client_running',return_value=False):
                manifest=m.apply(dll)
                self.assertEqual(dll.read_bytes(),self.modified)
                self.assertEqual(m.apply(dll),manifest)
                damaged=bytearray(self.modified);damaged[1024]^=1;dll.write_bytes(damaged)
                with self.assertRaises(ValueError):m.restore(dll)
                self.assertEqual(dll.read_bytes(),bytes(damaged))
                dll.write_bytes(self.modified)
            with patch.object(m,'native_client_running',return_value=True):
                with self.assertRaises(RuntimeError):m.restore(dll)
            with patch.object(m,'native_client_running',return_value=False):
                m.restore(dll)
            self.assertEqual(dll.read_bytes(),self.original)
