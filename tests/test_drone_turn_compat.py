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
if os.environ.get('DRONE_UNICORN_PATH'):
    sys.path.insert(0, os.environ['DRONE_UNICORN_PATH'])
try:
    from unicorn import Uc, UC_ARCH_X86, UC_MODE_32
    from unicorn.x86_const import *
except ImportError:
    Uc = None

class DroneTurnTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spec = importlib.util.spec_from_file_location('drone_turn_compat', ROOT/'tools/drone_turn_compat.py')
        cls.mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.mod)

    def execute(self, angle, rotation=True, base=0x10000000):
        m = self.mod
        u = Uc(UC_ARCH_X86, UC_MODE_32)
        u.mem_map(base, 0x400000)
        u.mem_map(0x20000000, 0x10000)
        u.mem_write(base+m.ENTRY_RVA, m.entry_jump())
        u.mem_write(base+m.CAVE_RVA, m.trampoline())
        esp=0x20008000
        u.mem_write(esp, struct.pack('<IIfffII', 0xabcdef, 0x1234, -7.0, 8.0, angle, int(rotation), 0))
        regs=[UC_X86_REG_EAX,UC_X86_REG_EBX,UC_X86_REG_ECX,UC_X86_REG_EDX,UC_X86_REG_ESI,UC_X86_REG_EDI,UC_X86_REG_EBP]
        for i,r in enumerate(regs):u.reg_write(r,0x11111111+i)
        for i in range(8):u.reg_write(UC_X86_REG_XMM0+i, int.from_bytes(bytes([i+1])*16,'little'))
        before=[u.reg_read(UC_X86_REG_XMM0+i) for i in range(8)]
        u.reg_write(UC_X86_REG_ESP,esp)
        # Entry flags are not contractual: the replayed SUB changes them. Compare
        # against executing the original prolog on the same initial machine.
        u.reg_write(UC_X86_REG_EFLAGS,0x246)
        u.emu_start(base+m.ENTRY_RVA,base+m.ENTRY_RVA+6,count=100)
        self.assertEqual(u.reg_read(UC_X86_REG_ESP),esp-16)
        self.assertEqual(u.reg_read(UC_X86_REG_EBP),esp-4)
        self.assertEqual([u.reg_read(r) for r in regs[:-1]], [0x11111111+i for i in range(6)])
        self.assertEqual([u.reg_read(UC_X86_REG_XMM0+i) for i in range(8)],before)
        self.assertEqual(struct.unpack('<ff',u.mem_read(esp+8,8)),(-7.,8.))
        self.assertEqual(u.reg_read(UC_X86_REG_EFLAGS)&0x8d5,0x4) # SUB result ESP-12: parity only
        return struct.unpack('<f',u.mem_read(esp+16,4))[0]

    @unittest.skipIf(Uc is None,'Install unicorn to execute x86 regression')
    def test_small_boundary_turn_uses_short_arc_and_preserves_machine_state(self):
        end=self.execute(-359.)
        self.assertEqual(end,1.)
        delta=end-359.
        if abs(delta)>180:delta-=360*(1 if delta>0 else -1)
        self.assertEqual(delta,2.)
        for angle,expected in [(-1,359),(-180,180),(-360,0),(0,0),(360,0),(359,359),(-0.,-0.)]:
            with self.subTest(angle=angle):self.assertEqual(self.execute(angle),expected)
        self.assertEqual(self.execute(-359.,base=0x30000000),1.)

    @unittest.skipIf(Uc is None,'Install unicorn to execute x86 regression')
    def test_translation_and_out_of_domain_targets_are_not_changed(self):
        for a in (-359.,-720.,720.,float('inf')):
            self.assertEqual(self.execute(a,False),a)
        for a in (-720.,720.):self.assertEqual(self.execute(a),a)

    def test_unknown_image_is_rejected(self):
        with self.assertRaises(ValueError):self.mod.patch_bytes(b'unknown build')

    @unittest.skipUnless(os.environ.get('DRONE_COMPAT_ORIGINAL'),'Set DRONE_COMPAT_ORIGINAL for exact native fixture')
    def test_native_patch_apply_restore_and_tamper_guards(self):
        m=self.mod
        original=Path(os.environ['DRONE_COMPAT_ORIGINAL']).read_bytes()
        self.assertEqual(hashlib.sha256(original).hexdigest(),m.ORIGINAL_SHA256)
        modified=m.patch_bytes(original)
        self.assertEqual(len(original),len(modified))
        self.assertNotEqual(modified,original)
        with tempfile.TemporaryDirectory() as td:
            dll=Path(td)/'GameAssembly.dll';dll.write_bytes(original)
            with patch.object(m,'native_client_running',return_value=True):
                with self.assertRaises(RuntimeError):m.apply(dll)
            self.assertEqual(dll.read_bytes(),original)
            with patch.object(m,'native_client_running',return_value=False):
                m.apply(dll);self.assertEqual(dll.read_bytes(),modified)
                m.apply(dll);self.assertEqual(dll.read_bytes(),modified)
                damaged=bytearray(modified);damaged[-1]^=1;dll.write_bytes(damaged)
                with self.assertRaises(ValueError):m.restore(dll)
                self.assertEqual(dll.read_bytes(),damaged)
                dll.write_bytes(modified);m.restore(dll);m.restore(dll)
                self.assertEqual(dll.read_bytes(),original)
                m.apply(dll);self.assertEqual(dll.read_bytes(),modified)
