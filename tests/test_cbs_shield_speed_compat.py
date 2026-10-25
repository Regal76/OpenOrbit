"""CBS-only playback rate, separate from game time and other invulnerability."""
import copy
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
    from unicorn import Uc, UC_ARCH_X86, UC_MODE_32, UC_HOOK_CODE
    from unicorn.x86_const import *
except ImportError:
    Uc = None


class CbsShieldSpeedTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spec = importlib.util.spec_from_file_location('cbs_shield_speed_compat', ROOT / 'tools/cbs_shield_speed_compat.py')
        cls.mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.mod)

    def test_unknown_artifacts_are_rejected(self):
        for kind in ('native', 'particles'):
            with self.subTest(kind=kind), self.assertRaisesRegex(ValueError, 'fingerprint'):
                self.mod.patch_bytes(b'unknown image', kind)

    def test_mutation_refuses_a_running_native_client_before_reading(self):
        with patch.object(self.mod, 'native_client_running', return_value=True):
            for function in (self.mod.apply, self.mod.restore):
                with self.assertRaises(RuntimeError):
                    function(Path('/missing/fixture'), 'native')

    def execute(self, raw, base=0x10000000, instance=True, animator=True):
        import pefile
        p = pefile.PE(data=raw, fast_load=True)
        mapped = p.get_memory_mapped_image()
        u = Uc(UC_ARCH_X86, UC_MODE_32)
        u.mem_map(base, (len(mapped) + 4095) & ~4095)
        u.mem_write(base, mapped)
        heap, stack = 0x30000000, 0x40000000
        u.mem_map(heap, 0x10000)
        u.mem_map(stack, 0x10000)
        effect, gameobject, animator_object, method_info = (heap + x for x in (0x100, 0x200, 0x300, 0x400))
        if not instance:
            gameobject = 0
        calls = []
        def helper(emu, address, length, user):
            target = address - base
            if target not in (0x1024cd0, 0x1ef640, 0x17ef440, 0x28e4630):
                return
            esp = emu.reg_read(UC_X86_REG_ESP)
            argc = {0x1024cd0: 3, 0x1ef640: 1, 0x17ef440: 2, 0x28e4630: 3}[target]
            values = struct.unpack('<' + 'I' * (argc + 1), emu.mem_read(esp, (argc + 1) * 4))
            ret, args = values[0], values[1:]
            if target == 0x1024cd0:
                self.assertEqual(args, (effect, gameobject, 0))
                emu.mem_write(effect + 0x20, struct.pack('<I', gameobject))
                result = 0xabcde
                calls.append(('initialize', args))
                xmm_value = 0x11112222333344445555666677778888
            elif target == 0x1ef640:
                self.assertEqual(args, (base + 0x340a03c,))
                emu.mem_write(args[0], struct.pack('<I', method_info))
                result = 0x5555
                calls.append(('metadata', args))
                xmm_value = 0x55556666777788889999000011112222
            elif target == 0x17ef440:
                self.assertEqual(args, (gameobject, method_info))
                result = animator_object if animator else 0
                calls.append(('get_animator', args))
                xmm_value = 0x9999aaaabbbbccccddddeeeeffff0000
            else:
                self.assertEqual(args[0], animator_object)
                self.assertEqual(args[2], 0)
                speed = struct.unpack('<f', struct.pack('<I', args[1]))[0]
                calls.append(('speed', speed))
                result = 0x7777
                xmm_value = 0xbbbbccccddddeeeeffff000011112222
            emu.reg_write(UC_X86_REG_EAX, result)
            emu.reg_write(UC_X86_REG_ECX, result + 1)
            emu.reg_write(UC_X86_REG_EDX, result + 2)
            emu.reg_write(UC_X86_REG_XMM0, xmm_value)
            emu.reg_write(UC_X86_REG_ESP, esp + 4)
            emu.reg_write(UC_X86_REG_EIP, ret)
        u.hook_add(UC_HOOK_CODE, helper)
        esp = stack + 0x6000
        registers = [UC_X86_REG_EAX, UC_X86_REG_EBX, UC_X86_REG_ECX, UC_X86_REG_EDX,
                     UC_X86_REG_ESI, UC_X86_REG_EDI, UC_X86_REG_EBP]
        for i, register in enumerate(registers):
            u.reg_write(register, 0x12340000 + i)
        u.reg_write(UC_X86_REG_ESI, gameobject)
        u.reg_write(UC_X86_REG_EDI, effect)
        u.reg_write(UC_X86_REG_ESP, esp)
        u.reg_write(UC_X86_REG_EBP, stack + 0x8000)
        u.reg_write(UC_X86_REG_EFLAGS, 0x646)
        for i in range(8):
            u.reg_write(UC_X86_REG_XMM0 + i, int.from_bytes(bytes([i + 1]) * 16, 'little'))
        u.emu_start(base + 0x7640ce, base + 0x7640de, count=500)
        state = ([u.reg_read(reg) for reg in registers], u.reg_read(UC_X86_REG_ESP),
                 [u.reg_read(UC_X86_REG_XMM0 + i) for i in range(8)],
                 bytes(u.mem_read(effect, 0x60)), u.reg_read(UC_X86_REG_EFLAGS))
        self.assertEqual(state[1], esp - 12)  # Original cdecl caller cleans these arguments.
        return calls, state

    @unittest.skipUnless(Uc is not None and os.environ.get('CBS_SHIELD_NATIVE_DLL'), 'Set native fixture and Unicorn path')
    def test_actual_cbs_initialization_slows_only_its_animator_and_preserves_context(self):
        original = Path(os.environ['CBS_SHIELD_NATIVE_DLL']).read_bytes()
        patched = self.mod.patch_bytes(original, 'native')
        for base in (0x10000000, 0x18000000):
            for instance, animator in ((True, True), (True, False), (False, False)):
                with self.subTest(base=base, instance=instance, animator=animator):
                    old_calls, old_state = self.execute(original, base, instance, animator)
                    new_calls, new_state = self.execute(patched, base, instance, animator)
                    self.assertEqual(old_calls, [('initialize', old_calls[0][1])])
                    self.assertEqual(new_state, old_state)
                    self.assertEqual([value for name, value in new_calls if name == 'speed'],
                                     [0.5] if instance and animator else [])
                    self.assertEqual(sum(name == 'initialize' for name, _ in new_calls), 1)
        # All original sections, including drone/resonator corrections, are
        # byte-identical except this one call in the CBS-only 2D initializer.
        import pefile
        p = pefile.PE(data=original, fast_load=True)
        at = p.get_offset_from_rva(self.mod.INIT_CALL_RVA)
        compared = bytearray(patched[:len(original)])
        compared[at:at + 5] = original[at:at + 5]
        for section in p.sections:
            begin, size = section.PointerToRawData, section.SizeOfRawData
            self.assertEqual(original[begin:begin + size], bytes(compared[begin:begin + size]))

    @unittest.skipUnless(os.environ.get('CBS_SHIELD_PARTICLE_BUNDLE'), 'Set particle bundle fixture')
    def test_3d_prefab_changes_only_two_simulation_speed_fields(self):
        import UnityPy
        original = Path(os.environ['CBS_SHIELD_PARTICLE_BUNDLE']).read_bytes()
        patched = self.mod.patch_bytes(original, 'particles')
        before, after = UnityPy.load(original), UnityPy.load(patched)
        old, new = self.mod.particle_targets(before), self.mod.particle_targets(after)
        self.assertEqual(set(old), {8739867819059555350, -5388967337541391338})
        for iid in old:
            a, b = old[iid].read_typetree(), new[iid].read_typetree()
            self.assertEqual(a['simulationSpeed'], 1)
            self.assertEqual(b['simulationSpeed'], 0.5)
            self.assertEqual(a['lengthInSec'] / a['simulationSpeed'], 1)
            self.assertEqual(b['lengthInSec'] / b['simulationSpeed'], 2)
            b['simulationSpeed'] = a['simulationSpeed']
            self.assertEqual(a, b)
        for obj in before.objects:
            if obj.path_id not in old:
                self.assertEqual(obj.get_raw_data(), after.file.files[obj.assets_file.name].objects[obj.path_id].get_raw_data())

    @unittest.skipUnless(os.environ.get('CBS_SHIELD_NATIVE_DLL') and os.environ.get('CBS_SHIELD_PARTICLE_BUNDLE'), 'Set both native fixtures')
    def test_temporary_apply_restore_idempotence_and_tamper_guards(self):
        import json
        m = self.mod
        for kind, variable in (('native', 'CBS_SHIELD_NATIVE_DLL'), ('particles', 'CBS_SHIELD_PARTICLE_BUNDLE')):
            original = Path(os.environ[variable]).read_bytes()
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as td:
                artifact = Path(td) / 'fixture'
                artifact.write_bytes(original)
                with patch.object(m, 'native_client_running', return_value=False):
                    m.apply(artifact, kind)
                    modified = artifact.read_bytes()
                    self.assertNotEqual(modified, original)
                    m.apply(artifact, kind)
                    self.assertEqual(artifact.read_bytes(), modified)
                    self.assertEqual(m.backup_path(artifact).read_bytes(), original)
                    changed = bytearray(modified)
                    changed[-1] ^= 1
                    artifact.write_bytes(changed)
                    with self.assertRaises(ValueError):
                        m.restore(artifact, kind)
                    self.assertEqual(artifact.read_bytes(), changed)
                    artifact.write_bytes(modified)
                    m.restore(artifact, kind)
                    m.restore(artifact, kind)
                    self.assertEqual(artifact.read_bytes(), original)
                    manifest = json.loads(m.manifest_path(artifact).read_text())
                    manifest['modified_sha256'] = '0' * 64
                    m.manifest_path(artifact).write_text(json.dumps(manifest))
                    artifact.write_bytes(modified)
                    with self.assertRaises(ValueError):
                        m.restore(artifact, kind)


if __name__ == '__main__':
    unittest.main()
