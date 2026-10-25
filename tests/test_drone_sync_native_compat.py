"""Execute the native 2D drone orientation/translation branches and new hooks."""
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
    from unicorn.x86_const import *
except ImportError:Uc=None
TOOL=ROOT/'tools/drone_sync_native_compat.py'
DLL=ROOT/'DarkOrbit_Version1.1.115/GameAssembly.dll';BACKUP=Path(str(DLL)+'.drone-sync.original')
FIXTURE=Path(os.environ.get('DRONE_SYNC_NATIVE_DLL',str(BACKUP if BACKUP.exists() else DLL)))


@unittest.skipUnless(Uc is not None and FIXTURE.exists(),'Exact native fixture and Unicorn required')
class DroneSyncNative(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original=FIXTURE.read_bytes();cls.tool=None
        if TOOL.exists():
            spec=importlib.util.spec_from_file_location('drone_sync',TOOL);cls.tool=importlib.util.module_from_spec(spec);spec.loader.exec_module(cls.tool)
        cls.modified=cls.tool.patch_bytes(cls.original) if cls.tool else cls.original

    def machine(self,raw,base):
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
        u.mem_map(0x50000000,0x10000);u.mem_map(0x60000000,0x10000)
        return u

    def retarget(self,raw,angle,rotation=True,cached=False,base=0x10000000):
        u=self.machine(raw,base);heap=0x50000000;stack=0x60008000;end=0x6000f000
        unit,component,gameobject,transform,rotclass,movclass,tween=[heap+x for x in (0x100,0x300,0x500,0x700,0x900,0xb00,0xd00)]
        w32=lambda a,v:u.mem_write(a,struct.pack('<I',v&0xffffffff))
        r32=lambda a:struct.unpack('<I',bytes(u.mem_read(a,4)))[0]
        u.mem_write(base+0x34facd6,b'\x01')
        for rva,cl in [(0x33d04ec,rotclass),(0x33d068c,movclass)]:
            w32(base+rva,cl);u.mem_write(cl+0xb8,b'\x01');w32(cl+0x64,cl+0x100);w32(cl+0x100,cl)
        w32(tween,rotclass if rotation else movclass)
        w32(component+0x6c,heap+0xf00 if rotation else tween if cached else 0)
        w32(component+0x70,tween if cached and rotation else 0)
        calls=[];angles=[]
        def finish(emu,eax=None):
            sp=emu.reg_read(UC_X86_REG_ESP);ret=r32(sp)
            if eax is not None:emu.reg_write(UC_X86_REG_EAX,eax)
            emu.reg_write(UC_X86_REG_ESP,sp+4);emu.reg_write(UC_X86_REG_EIP,ret)
        def hook(emu,address,size,data):
            rva=address-base;sp=emu.reg_read(UC_X86_REG_ESP)
            if rva==0x17b13a0:finish(emu,component)
            elif rva==0xf7c780:finish(emu,gameobject)
            elif rva==0x2920880:finish(emu,transform)
            elif rva in (0x170a5a0,0x170a030):
                args=struct.unpack('<IffffII',bytes(emu.mem_read(sp+4,28)))
                calls.append(('rotate_tween' if rva==0x170a5a0 else 'move_tween',args[1:4],args[4]));finish(emu,tween)
            elif rva in (0x195d540,0x196d2b0):
                args=struct.unpack('<IffffII',bytes(emu.mem_read(sp+4,28)))
                calls.append(('rotate_retarget' if rva==0x195d540 else 'move_retarget',args[1:4],args[4]));finish(emu,tween)
            elif rva==0x170fce0:finish(emu,1)
            elif rva==0x1710900:calls.append(('restart',));finish(emu)
            elif rva in (0x18410b0,0x18415b0):finish(emu,r32(sp+4))
            elif rva==0x1eea70:finish(emu)
            elif rva==0x170fe80:
                self.assertEqual(r32(sp+4),tween);self.assertEqual(r32(sp+8),0);calls.append(('kill_rotation',));finish(emu)
            elif rva==0x292f6b0:
                self.assertEqual(r32(sp+4),transform)
                angles.append(struct.unpack('<fff',bytes(emu.mem_read(sp+8,12))));finish(emu)
            elif rva==0x1ef8a0:self.fail('Unexpected native null guard')
        u.hook_add(UC_HOOK_CODE,hook)
        u.mem_write(stack,struct.pack('<IIfffII',end,unit,-7.,8.,angle,int(rotation),0));u.reg_write(UC_X86_REG_ESP,stack)
        initial={UC_X86_REG_EBX:0x11223344,UC_X86_REG_ESI:0x22334455,UC_X86_REG_EDI:0x33445566,UC_X86_REG_EBP:0x44556677}
        for reg,value in initial.items():u.reg_write(reg,value)
        u.emu_start(base+0x352f80,end,count=3000)
        self.assertEqual(u.reg_read(UC_X86_REG_ESP),stack+4)
        for reg,value in initial.items():self.assertEqual(u.reg_read(reg),value)
        return dict(calls=calls,angles=angles,rotation_tween=r32(component+0x70),move_tween=r32(component+0x6c),tween=tween)

    def frame_angle(self,raw,ship_angle,parent_angle=15.,owner=True,component=True,base=0x10000000):
        u=self.machine(raw,base);heap=0x50000000;stack=0x60008000;drone,owner_unit,ship=[heap+x for x in (0x100,0x300,0x500)]
        u.mem_write(drone+0x40,struct.pack('<I',owner_unit if owner else 0));u.mem_write(ship+0x7c,struct.pack('<f',ship_angle))
        u.mem_write(stack,struct.pack('<IIfI',0x6000f000,drone,parent_angle,0));u.reg_write(UC_X86_REG_ESP,stack)
        u.reg_write(UC_X86_REG_EBP,0x11223344);u.reg_write(UC_X86_REG_EBX,0x22334455);u.reg_write(UC_X86_REG_ESI,0x33445566);u.reg_write(UC_X86_REG_EDI,0x44556677)
        def finish(emu,eax=None):
            sp=emu.reg_read(UC_X86_REG_ESP);ret,=struct.unpack('<I',bytes(emu.mem_read(sp,4)))
            if eax is not None:emu.reg_write(UC_X86_REG_EAX,eax)
            emu.reg_write(UC_X86_REG_ESP,sp+4);emu.reg_write(UC_X86_REG_EIP,ret)
        def hook(emu,address,size,data):
            rva=address-base
            if rva==0x1ef640:finish(emu)
            elif rva==0x17b13a0:
                sp=emu.reg_read(UC_X86_REG_ESP);obj,=struct.unpack('<I',bytes(emu.mem_read(sp+4,4)))
                self.assertEqual(obj,owner_unit);finish(emu,ship if component else 0)
        u.hook_add(UC_HOOK_CODE,hook);u.emu_start(base+0x34fac0,base+0x34fac6,count=3000)
        self.assertEqual(u.reg_read(UC_X86_REG_ESP),stack-20)
        for reg,value in [(UC_X86_REG_EBX,0x22334455),(UC_X86_REG_ESI,0x33445566),(UC_X86_REG_EDI,0x44556677)]:self.assertEqual(u.reg_read(reg),value)
        return struct.unpack('<f',bytes(u.mem_read(stack+8,4)))[0]

    def test_drone_local_rotation_is_applied_in_the_same_call_and_wrap_is_retained(self):
        for base in (0x10000000,0x30000000):
            for cached in (False,True):
                with self.subTest(base=hex(base),cached=cached):
                    state=self.retarget(self.modified,-359.,cached=cached,base=base)
                    self.assertEqual(state['angles'],[(-7.,8.,1.)])
                    self.assertFalse(any(row[0] in ('rotate_tween','rotate_retarget','restart') for row in state['calls']))
                    self.assertEqual(state['rotation_tween'],0)
                    self.assertEqual(state['move_tween'],0x50000f00) # concurrent movement tween is retained
                    self.assertEqual([r[0] for r in state['calls']],['kill_rotation'] if cached else [])

    def test_drone_sprite_uses_current_owner_heading_while_parent_formation_lags(self):
        for base in (0x10000000,0x30000000):
            for heading in (0.,1.,90.,179.,359.,360.,1.):
                with self.subTest(base=hex(base),heading=heading):
                    self.assertEqual(self.frame_angle(self.modified,heading,base=base),heading)

    def test_translation_keeps_native_half_second_tweens_and_cached_move_retarget(self):
        for cached in (False,True):
            state=self.retarget(self.modified,-359.,rotation=False,cached=cached)
            row=next(r for r in state['calls'] if r[0] in ('move_tween','move_retarget'))
            self.assertEqual(row[1],(-7.,8.,-359.));self.assertEqual(row[2],.5)
            self.assertEqual(state['angles'],[])

    def test_missing_owner_or_ship_component_keeps_original_sprite_input(self):
        for owner,component in [(False,True),(True,False)]:
            self.assertEqual(self.frame_angle(self.modified,90.,owner=owner,component=component),15.)

    def test_original_client_still_tweens_rotation_and_samples_lagging_parent(self):
        state=self.retarget(self.original,-359.)
        self.assertEqual(state['angles'],[])
        self.assertEqual(next(row for row in state['calls'] if row[0]=='rotate_tween')[2],.5)
        self.assertEqual(self.frame_angle(self.original,90.),15.)

    def test_patch_preserves_formation_motion_3d_prior_hooks_and_loader_relocations(self):
        m=self.tool;self.assertIsNotNone(m)
        self.assertEqual(hashlib.sha256(self.original).hexdigest(),m.ORIGINAL_SHA256)
        self.assertEqual(hashlib.sha256(self.modified).hexdigest(),m.MODIFIED_SHA256)
        pe=pefile.PE(data=self.original,fast_load=True);restored=bytearray(self.modified[:len(self.original)])
        for rva,expected in m.EXPECTED.items():
            at=pe.get_offset_from_rva(rva);restored[at:at+len(expected)]=self.original[at:at+len(expected)]
        optional=pe.DOS_HEADER.e_lfanew+24;header=pe.sections[-1].get_file_offset()
        for at in (optional+4,optional+56,header+8,header+16):restored[at:at+4]=self.original[at:at+4]
        self.assertEqual(bytes(restored),self.original)
        with self.assertRaises(ValueError):m.patch_bytes(self.original[:-1]+b'!')

    def test_apply_restore_fingerprint_and_live_client_guards(self):
        m=self.tool;self.assertIsNotNone(m)
        with tempfile.TemporaryDirectory() as folder:
            dll=Path(folder)/'GameAssembly.dll';dll.write_bytes(self.original)
            with patch.object(m,'native_client_running',return_value=True):
                with self.assertRaises(RuntimeError):m.apply(dll)
            self.assertEqual(dll.read_bytes(),self.original)
            with patch.object(m,'native_client_running',return_value=False):
                manifest=m.apply(dll);self.assertEqual(dll.read_bytes(),self.modified);self.assertEqual(m.apply(dll),manifest)
                damaged=bytearray(self.modified);damaged[1024]^=1;dll.write_bytes(damaged)
                with self.assertRaises(ValueError):m.restore(dll)
                self.assertEqual(dll.read_bytes(),bytes(damaged));dll.write_bytes(self.modified)
            with patch.object(m,'native_client_running',return_value=True):
                with self.assertRaises(RuntimeError):m.restore(dll)
            with patch.object(m,'native_client_running',return_value=False):m.restore(dll)
            self.assertEqual(dll.read_bytes(),self.original)
