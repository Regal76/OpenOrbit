"""Execute the native Space rocket handler across ship/building target paths."""
import hashlib
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
sys.path.insert(0, str(ROOT / 'tools'))
try:
    import pefile
    from unicorn import Uc, UC_ARCH_X86, UC_MODE_32, UC_HOOK_CODE
    from unicorn.x86_const import UC_X86_REG_EAX, UC_X86_REG_EIP, UC_X86_REG_ESP
except ImportError:
    Uc = None

TOOL = ROOT / 'tools/cbs_manual_rocket_native_compat.py'
DEFAULT_DLL=ROOT/'DarkOrbit_Version1.1.115/GameAssembly.dll'
DEFAULT_BACKUP=Path(str(DEFAULT_DLL)+'.cbs-manual-rocket.original')
FIXTURE=Path(os.environ.get('CBS_ROCKET_NATIVE_DLL',str(DEFAULT_BACKUP if DEFAULT_BACKUP.exists() else DEFAULT_DLL)))


@unittest.skipUnless(Uc is not None and FIXTURE.exists(), 'Exact native fixture and Unicorn required')
class ManualRocketNative(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original = FIXTURE.read_bytes()
        cls.tool = None
        if TOOL.exists():
            spec = importlib.util.spec_from_file_location('cbs_manual_rocket', TOOL)
            cls.tool = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(cls.tool)
        cls.modified = cls.tool.patch_bytes(cls.original) if cls.tool else cls.original

    def execute(self, raw, kind='building', target_id=402, xy=(9137.75, 7282.25), base=0x10000000):
        pe = pefile.PE(data=raw, fast_load=True)
        image = bytearray(pe.get_memory_mapped_image())
        delta = base - pe.OPTIONAL_HEADER.ImageBase
        directory=pe.OPTIONAL_HEADER.DATA_DIRECTORY[5]
        cursor,end=directory.VirtualAddress,directory.VirtualAddress+directory.Size
        while cursor < end:
            page,size=struct.unpack_from('<II',image,cursor)
            if not size: break
            for at in range(cursor+8,cursor+size,2):
                entry,=struct.unpack_from('<H',image,at)
                if entry>>12==3:
                    rva=page+(entry&4095)
                    value,=struct.unpack_from('<I',image,rva)
                    struct.pack_into('<I',image,rva,(value+delta)&0xffffffff)
            cursor+=size
        u = Uc(UC_ARCH_X86, UC_MODE_32)
        u.mem_map(base, (len(image) + 4095) & ~4095)
        u.mem_write(base, bytes(image))
        heap, stack = 0x50000000, 0x60000000
        u.mem_map(heap, 0x10000)
        u.mem_map(stack, 0x10000)
        def w32(address, value): u.mem_write(address, struct.pack('<I', value & 0xffffffff))
        def global_ptr(rva, pointer): w32(base + rva, pointer)
        unit, build, helper, scene_type, net, log = [heap + x for x in (0x100,0x300,0x500,0x700,0x900,0xb00)]
        target, request, wrap = heap+0x2000, heap+0x3000, heap+0x4000
        for klass in (helper, scene_type, net, log):
            w32(klass + 0x74, 1)
            w32(klass + 0x5c, klass + 0x100)
        global_ptr(0x340c1f8, helper)
        global_ptr(0x340ba6c, unit)
        global_ptr(0x34050c4, build)
        global_ptr(0x33f6380, scene_type)
        global_ptr(0x33e4f7c, net)
        global_ptr(0x33d1b24, log)
        w32(helper + 0x100, 0 if kind == 'null' else target)
        w32(scene_type + 0x100 + 0xc, heap+0x4500)
        for rva in (0x34fae0d,0x34fa78b,0x34fa678): u.mem_write(base+rva,b'\x01')
        u.mem_write(unit+0xb8,b'\x01')
        u.mem_write(build+0xb8,b'\x00')
        w32(unit+0x64,heap+0x4600)
        w32(heap+0x4600,unit)
        w32(target, build if kind == 'building' else unit)
        w32(target+0x30,target_id)
        w32(target+0x34,-1 if target_id == -1 else 0)
        w32(target+0x60,wrap)
        u.mem_write(wrap+8,struct.pack('<fff',xy[0],xy[1],0))
        calls, sent, errors = [], [], []
        def finish(emu, eax=None):
            sp=emu.reg_read(UC_X86_REG_ESP)
            ret,=struct.unpack('<I',bytes(emu.mem_read(sp,4)))
            if eax is not None: emu.reg_write(UC_X86_REG_EAX,eax)
            emu.reg_write(UC_X86_REG_ESP,sp+4)
            emu.reg_write(UC_X86_REG_EIP,ret)
        def hook(emu,address,size,data):
            rva=address-base
            if rva==0x1eeac0:
                errors.append('invalid target cast');emu.emu_stop()
            elif rva==0x1ef8a0:
                errors.append('null native object');emu.emu_stop()
            elif rva==0xf66930:
                sp=emu.reg_read(UC_X86_REG_ESP)
                ret,out,obj,method=struct.unpack('<IIII',bytes(emu.mem_read(sp,16)))
                self.assertEqual(obj,target)
                self.assertEqual(kind,'building')
                emu.mem_write(out,struct.pack('<fff',xy[0],0,xy[1]))
                calls.append('BuildUnit.get_RealPosition');finish(emu,out)
            elif rva==0x1ac3a0:
                calls.append('allocate rocket request');finish(emu,request)
            elif rva==0x73be00:
                sp=emu.reg_read(UC_X86_REG_ESP)
                _,obj,uid,x,y,_=struct.unpack('<IIIIII',bytes(emu.mem_read(sp,24)))
                self.assertEqual(obj,request)
                emu.mem_write(obj+8,struct.pack('<III',uid,x,y));finish(emu)
            elif rva==0x2c8ef0:
                sp=emu.reg_read(UC_X86_REG_ESP)
                _,scene,obj,_=struct.unpack('<IIII',bytes(emu.mem_read(sp,16)))
                self.assertEqual(obj,request)
                sent.append(struct.unpack('<iii',bytes(emu.mem_read(obj+8,12))));finish(emu)
            elif rva==0x105d200:
                finish(emu)
        u.hook_add(UC_HOOK_CODE,hook)
        sp=stack+0x8000;end=stack+0xf000
        u.mem_write(sp,struct.pack('<IIII',end,heap+0x6000,0,0))
        u.reg_write(UC_X86_REG_ESP,sp)
        u.emu_start(base+0x37f980,end,count=5000)
        return sent,errors,calls

    def test_space_building_target_emits_native_rocket_request_with_map_coordinates(self):
        for base in (0x10000000,0x30000000):
            with self.subTest(base=hex(base)):
                sent,errors,calls=self.execute(self.modified,base=base)
                # Native checksum rule adds one to Y when truncated X+Y is divisible by three.
                self.assertEqual(sent,[(402,9137,7283)])
                self.assertEqual(errors,[])
                self.assertEqual(calls.count('BuildUnit.get_RealPosition'),1)

    def test_ship_target_keeps_original_request_and_coordinate_delta(self):
        for base in (0x10000000,0x30000000):
            sent,errors,calls=self.execute(self.modified,kind='ship',target_id=177,xy=(30,60),base=base)
            self.assertEqual(sent,[(177,30,61)])
            self.assertEqual(errors,[])
            self.assertNotIn('BuildUnit.get_RealPosition',calls)

    def test_null_and_invalid_id_keep_original_no_send_guards(self):
        for kind,uid in [('null',402),('building',-1),('ship',-1)]:
            sent,errors,calls=self.execute(self.modified,kind=kind,target_id=uid)
            self.assertEqual(sent,[])
            self.assertEqual(errors,[])

    def test_original_client_rejects_building_target_before_request_construction(self):
        sent,errors,calls=self.execute(self.original)
        self.assertEqual(sent,[])
        self.assertEqual(errors,['invalid target cast'])
        self.assertNotIn('allocate rocket request',calls)

    def test_patch_preserves_prior_code_and_relocations_except_declared_hook_and_section_headers(self):
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
