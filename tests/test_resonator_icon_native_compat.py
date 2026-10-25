"""Execute shipped icon methods with missing ItemDataProvider definitions."""
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


class ResonatorIconNativeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spec = importlib.util.spec_from_file_location('resonator_icon_native_compat', ROOT / 'tools/resonator_icon_native_compat.py')
        cls.mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.mod)
        cls._mapped_images = {}

    def test_unknown_dll_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'fingerprint'):
            self.mod.patch_bytes(b'unknown DLL')

    def test_allowlist_contains_exactly_the_existing_server_items_and_sources(self):
        import json
        d = json.loads((ROOT / 'server/data/esyalar_o6.json').read_text())['rezonator']
        self.assertEqual(set(self.mod.LOOT_IDS), set(d['esyalar']) | set(d['kaynaklar']))
        self.assertEqual(len(self.mod.LOOT_IDS), 25)

    def execute(self, raw, loot, unknown, size, base=0x10000000):
        import pefile
        key = (raw, base)
        if key not in self._mapped_images:
            p = pefile.PE(data=raw, fast_load=True)
            mapped = bytearray(p.get_memory_mapped_image())
            if base != p.OPTIONAL_HEADER.ImageBase:
                # Apply the shipped PE relocation records for the native methods
                # we execute. Other application code is never entered; the new
                # guard has no absolute addresses or relocation records.
                directory = p.OPTIONAL_HEADER.DATA_DIRECTORY[5]
                relocations = p.get_data(directory.VirtualAddress, directory.Size)
                delta = base - p.OPTIONAL_HEADER.ImageBase
                ranges = [(spec['entry'], spec['entry'] + 80) for spec in self.mod.METHODS.values()]
                pages = {start & ~4095 for start, _ in ranges}
                cursor = 0
                while cursor < len(relocations):
                    page, block_size = struct.unpack_from('<II', relocations, cursor)
                    if not block_size:
                        break
                    if page in pages:
                        for (entry,) in struct.iter_unpack('<H', relocations[cursor + 8:cursor + block_size]):
                            rva = page + (entry & 4095)
                            if entry >> 12 == 3 and any(start <= rva < end for start, end in ranges):
                                value = struct.unpack_from('<I', mapped, rva)[0]
                                struct.pack_into('<I', mapped, rva, value + delta)
                    cursor += block_size
            self._mapped_images[key] = bytes(mapped)
        mapped = self._mapped_images[key]
        u = Uc(UC_ARCH_X86, UC_MODE_32)
        u.mem_map(base, (len(mapped) + 4095) & ~4095)
        u.mem_write(base, mapped)
        heap, stack = 0x30000000, 0x40000000
        u.mem_map(heap, 0x10000)
        u.mem_map(stack, 0x10000)
        current = heap + 0x1000
        def string(text):
            nonlocal current
            ptr = current
            raw_text = text.encode('utf-16le')
            u.mem_write(ptr, b'\0' * 8 + struct.pack('<I', len(raw_text) // 2) + raw_text + b'\0\0')
            current += len(raw_text) + 32
            return ptr
        loot_pointer = string(loot) if loot is not None else 0
        suffix = string('_' + size)
        fallback = string('unknown_' + size)
        obj = heap + 0x100
        u.mem_write(obj, b'\0' * 0x60)
        u.mem_write(obj + 8, struct.pack('<I', loot_pointer))
        u.mem_write(obj + 0x50, bytes([int(unknown)]))
        spec = self.mod.METHODS[size]
        for rva, value in ((spec['initialized'], 1),):
            u.mem_write(base + rva, bytes([value]))
        u.mem_write(base + spec['suffix_global'], struct.pack('<I', suffix))
        u.mem_write(base + spec['unknown_global'], struct.pack('<I', fallback))
        def read_string(ptr):
            length = struct.unpack('<I', u.mem_read(ptr + 8, 4))[0]
            return bytes(u.mem_read(ptr + 12, length * 2)).decode('utf-16le')
        calls = []
        def fake_getloot(emu, address, instruction_size, user):
            if address != base + self.mod.GET_LOOT_RVA:
                return
            esp = emu.reg_read(UC_X86_REG_ESP)
            ret, item, ending, faction, method = struct.unpack('<IIIII', emu.mem_read(esp, 20))
            actual_loot = struct.unpack('<I', emu.mem_read(item + 8, 4))[0]
            result = read_string(actual_loot).rsplit('_', 1)[-1] + read_string(ending)
            calls.append((read_string(actual_loot), faction))
            emu.reg_write(UC_X86_REG_EAX, string(result))
            emu.reg_write(UC_X86_REG_ESP, esp + 4)
            emu.reg_write(UC_X86_REG_EIP, ret)
        u.hook_add(UC_HOOK_CODE, fake_getloot)
        esp = stack + 0x8000
        sentinel = heap
        u.mem_write(esp, struct.pack('<IIII', sentinel, obj, 0x12345678, 0))
        u.reg_write(UC_X86_REG_ESP, esp)
        u.reg_write(UC_X86_REG_EFLAGS, 0x646)  # preserve a caller's direction flag
        registers = [UC_X86_REG_EBX, UC_X86_REG_ECX, UC_X86_REG_EDX, UC_X86_REG_ESI, UC_X86_REG_EDI, UC_X86_REG_EBP]
        values = [0x11110000 + i for i in range(len(registers))]
        for reg, value in zip(registers, values):
            u.reg_write(reg, value)
        for i in range(8):
            u.reg_write(UC_X86_REG_XMM0 + i, int.from_bytes(bytes([i + 1]) * 16, 'little'))
        xmm = [u.reg_read(UC_X86_REG_XMM0 + i) for i in range(8)]
        before = bytes(u.mem_read(obj, 0x60))
        u.emu_start(base + spec['entry'], sentinel, count=10000)
        self.assertEqual(u.reg_read(UC_X86_REG_ESP), esp + 4)
        self.assertEqual([u.reg_read(reg) for reg in registers], values)
        self.assertEqual([u.reg_read(UC_X86_REG_XMM0 + i) for i in range(8)], xmm)
        self.assertEqual(bytes(u.mem_read(obj, 0x60)), before)
        self.assertEqual(u.reg_read(UC_X86_REG_EFLAGS) & 0x400, 0x400)
        return read_string(u.reg_read(UC_X86_REG_EAX)), calls

    @unittest.skipUnless(Uc is not None and os.environ.get('RESONATOR_NATIVE_DLL'), 'Set fixture and Unicorn path')
    def test_shipped_unknown_item_methods_use_alias_for_exact_allowlist_only(self):
        m = self.mod
        original = Path(os.environ['RESONATOR_NATIVE_DLL']).read_bytes()
        for size in m.METHODS:
            # Reproduce the real native failure before checking the correction.
            result, calls = self.execute(original, m.LOOT_IDS[0], True, size)
            self.assertEqual(result, 'unknown_' + size)
            self.assertEqual(calls, [])
        modified = m.patch_bytes(original)
        for size in m.METHODS:
            for loot in m.LOOT_IDS:
                with self.subTest(size=size, loot=loot):
                    result, calls = self.execute(modified, loot, True, size)
                    self.assertEqual(result, loot.rsplit('_', 1)[-1] + '_' + size)
                    self.assertEqual(calls, [(loot, 0x12345678)])
            for loot in ('equipment_xenoresonator_future-strike-resonator',
                         'equipment_xenoresonator_c-strike-resonator-extra',
                         'equipment_xenoresonator_c-strike-resonatoR',
                         'resource_attack-future', 'resource_defensive-future', 'resource_attack-adhesionx', '', None):
                with self.subTest(size=size, rejected=loot):
                    self.assertEqual(self.execute(modified, loot, True, size), ('unknown_' + size, []))
            for loot in ('equipment_weapon_c-nidhogg', 'resource_micro-transistors'):
                self.assertEqual(self.execute(modified, loot, False, size), self.execute(original, loot, False, size))
            result, _ = self.execute(modified, m.LOOT_IDS[-1], True, size, base=0x18000000)
            self.assertEqual(result, m.LOOT_IDS[-1].rsplit('_', 1)[-1] + '_' + size)

    def execute_tooltip(self, raw, key, template, value, prefix='', base=0x10000000, unit='% '):
        import pefile
        mapped_key = ('tooltip', raw, base)
        if mapped_key not in self._mapped_images:
            p = pefile.PE(data=raw, fast_load=True)
            mapped = bytearray(p.get_memory_mapped_image())
            # Local EBP pointers and the relative CALL need no relocation.
            self._mapped_images[mapped_key] = bytes(mapped)
        mapped = self._mapped_images[mapped_key]
        u = Uc(UC_ARCH_X86, UC_MODE_32)
        u.mem_map(base, (len(mapped) + 4095) & ~4095)
        u.mem_write(base, mapped)
        heap, stack = 0x30000000, 0x40000000
        u.mem_map(heap, 0x20000)
        u.mem_map(stack, 0x10000)
        current = heap + 0x1000
        def string(text):
            nonlocal current
            ptr = current
            data = text.encode('utf-16le')
            u.mem_write(ptr, b'\0' * 8 + struct.pack('<I', len(data) // 2) + data + b'\0\0')
            current += len(data) + 32
            return ptr
        def read(ptr):
            if not ptr:
                return ''
            length = struct.unpack('<I', u.mem_read(ptr + 8, 4))[0]
            return bytes(u.mem_read(ptr + 12, 2 * length)).decode('utf-16le')
        token = string('%VALUE%')
        percent_token = string('%')
        calls = []
        targets = {0x208b800: ('concat4', 4), 0x208be80: ('concat2', 2),
                   0x2092560: ('substring', 2), 0x2091090: ('replace', 3),
                   0x1ef640: ('metadata', 1)}
        def helpers(emu, address, instruction_size, user):
            target = targets.get(address - base)
            if target is None:
                return
            name, count = target
            esp = emu.reg_read(UC_X86_REG_ESP)
            values = struct.unpack('<' + 'I' * (count + 1), emu.mem_read(esp, 4 * (count + 1)))
            ret, args = values[0], values[1:]
            calls.append(name)
            if name == 'metadata':
                self.assertIn(args[0], (base + 0x33e6550, base + 0x33e082c))
                emu.mem_write(args[0], struct.pack('<I', token if args[0] == base + 0x33e6550 else percent_token))
                result = 0
            elif name == 'substring':
                result = string(read(args[0])[args[1]:])
            elif name == 'replace':
                result = string(read(args[0]).replace(read(args[1]), read(args[2])))
            else:
                result = string(''.join(read(arg) for arg in args))
            emu.reg_write(UC_X86_REG_EAX, result)
            emu.reg_write(UC_X86_REG_ESP, esp + 4)
            emu.reg_write(UC_X86_REG_EIP, ret)
        u.hook_add(UC_HOOK_CODE, helpers)
        esp, ebp = stack + 0x6000, stack + 0x8000
        u.mem_write(ebp - 0x10, struct.pack('<III', string(unit), string(str(value) if str(value).startswith('-') else '+' + str(value)), string(prefix)))
        # The native locals are -0x10 unit, -0xc numeric prefix, -4 accumulator.
        u.mem_write(ebp - 4, struct.pack('<I', string(prefix)))
        u.reg_write(UC_X86_REG_ESP, esp)
        u.reg_write(UC_X86_REG_EBP, ebp)
        u.reg_write(UC_X86_REG_ESI, string(key))
        u.reg_write(UC_X86_REG_EAX, string(template))
        u.reg_write(UC_X86_REG_EBX, 0x11223344)
        u.reg_write(UC_X86_REG_EDI, 0x55667788)
        original_esi = u.reg_read(UC_X86_REG_ESI)
        u.emu_start(base + 0x57dbbf, base + 0x57dbd0, count=10000)
        self.assertEqual(u.reg_read(UC_X86_REG_ESP), esp - 20)
        self.assertEqual(u.reg_read(UC_X86_REG_EBP), ebp)
        self.assertEqual(u.reg_read(UC_X86_REG_ESI), original_esi)
        self.assertEqual(u.reg_read(UC_X86_REG_EBX), 0x11223344)
        self.assertEqual(u.reg_read(UC_X86_REG_EDI), 0x55667788)
        return read(u.reg_read(UC_X86_REG_EAX)), calls

    @unittest.skipUnless(Uc is not None and os.environ.get('RESONATOR_NATIVE_DLL'), 'Set fixture and Unicorn path')
    def test_native_modifier_callsite_substitutes_actual_tr_en_templates_and_keeps_other_items(self):
        import UnityPy
        path = ROOT / 'DarkOrbit_Version1.1.115/DarkOrbit_Data/StreamingAssets/aa/BuildTarget/localizations_assets_all.bundle'
        if not path.exists():
            self.skipTest('Native localization bundle is absent')
        original = Path(os.environ['RESONATOR_NATIVE_DLL']).read_bytes()
        modified = self.mod.patch_bytes(original)
        key_prefix = 'items_equipment_shipupgrade_modifiertype_'
        names = ('expansion', 'collapse', 'evernight', 'aftershock', 'stagnation', 'adhesion',
                 'grav_tolerance', 'entry_buffer', 'zone_adaptation', 'slowing_resistance', 'detachment')
        bundle = UnityPy.load(str(path))
        for language in ('tr', 'en'):
            asset = next(obj for name, obj in bundle.container.items() if '/' + language + '/data/resource_items.asset' in name)
            texts = {entry['key']: entry['value'] for entry in asset.read_typetree()['data']}
            for name in names:
                key = key_prefix + name
                template = texts[key]
                value = '2.4' if name == 'adhesion' else '1.2' if name == 'entry_buffer' else '6.5'
                with self.subTest(language=language, modifier=name):
                    bad, _ = self.execute_tooltip(original, key, template, value)
                    self.assertEqual(bad, '+' + value + '% ' + template)
                    actual, calls = self.execute_tooltip(modified, key, template, value, prefix='Prior modifier, ')
                    self.assertEqual(actual, 'Prior modifier, ' + template.replace('%VALUE%', value if name in ('adhesion', 'entry_buffer') else value + '%'))
                    self.assertNotIn('%VALUE%', actual)
                    self.assertIn('replace', calls)
                    self.assertNotIn('concat4', calls)
                    self.assertEqual(calls.count('concat2'), 1 if name in ('adhesion', 'entry_buffer') else 2)
            template = texts[key_prefix + 'adhesion']
            expected = template.replace('%VALUE%', '2.4')
            self.assertEqual(self.execute_tooltip(modified, key_prefix + 'adhesion', template, '2.4', base=0x18000000)[0], expected)
        for name in ('damage', 'cannon_ignore_def_thermal', 'drive_ignore_def', 'adhesion_extra', 'future'):
            key = key_prefix + name
            for value in ('12', '-5'):
                # The generic method removes '+' for negative SafeInt values.
                # This boundary tests that unrelated prepared fragments remain
                # byte-for-byte unchanged through the native callsite.
                unit = ' ' if name in ('cannon_ignore_def_thermal', 'drive_ignore_def') else '% '
                expected = self.execute_tooltip(original, key, 'Other modifier', value, prefix='Previous, ', unit=unit)
                actual = self.execute_tooltip(modified, key, 'Other modifier', value, prefix='Previous, ', unit=unit)
                self.assertEqual(actual, expected)

    @unittest.skipUnless(os.environ.get('RESONATOR_NATIVE_DLL'), 'Set RESONATOR_NATIVE_DLL for exact native fixture')
    def test_temporary_apply_restore_preserve_drone_patch_and_reject_tampering(self):
        m = self.mod
        original = Path(os.environ['RESONATOR_NATIVE_DLL']).read_bytes()
        modified = m.patch_bytes(original)
        import pefile
        a, b = pefile.PE(data=original, fast_load=True), pefile.PE(data=modified, fast_load=True)
        # Every original section byte remains identical except the two 6-byte
        # icon checks and one 5-byte modifier formatting call. In particular, all prior drone correction bytes survive.
        changed = {a.get_offset_from_rva(s['check']) + i for s in m.METHODS.values() for i in range(6)}
        changed |= {a.get_offset_from_rva(self.mod.TOOLTIP_CALL_RVA) + i for i in range(5)}
        for section in a.sections:
            start, end = section.PointerToRawData, section.PointerToRawData + section.SizeOfRawData
            compared = bytearray(modified[start:end])
            for at in changed:
                if start <= at < end:
                    compared[at - start] = original[at]
            self.assertEqual(original[start:end], bytes(compared))
        with tempfile.TemporaryDirectory() as td:
            dll = Path(td) / 'GameAssembly.dll'
            dll.write_bytes(original)
            with patch.object(m, 'native_client_running', return_value=True):
                with self.assertRaises(RuntimeError):
                    m.apply(dll)
            self.assertEqual(dll.read_bytes(), original)
            with patch.object(m, 'native_client_running', return_value=False):
                m.apply(dll)
                applied = dll.read_bytes()
                m.apply(dll)
                self.assertEqual(dll.read_bytes(), applied)
                altered = bytearray(applied)
                altered[-1] ^= 1
                dll.write_bytes(altered)
                with self.assertRaises(ValueError):
                    m.restore(dll)
                self.assertEqual(dll.read_bytes(), altered)
                dll.write_bytes(applied)
                m.restore(dll)
                m.restore(dll)
                self.assertEqual(dll.read_bytes(), original)


    @unittest.skipUnless(os.environ.get('RESONATOR_NATIVE_DLL'), 'Set RESONATOR_NATIVE_DLL for exact native fixture')
    def test_legacy_v1_requires_exact_restore_before_v2_and_keeps_original_backup(self):
        import hashlib
        import json
        import pefile
        m = self.mod
        original = Path(os.environ['RESONATOR_NATIVE_DLL']).read_bytes()
        current = bytearray(m.patch_bytes(original))
        pe = pefile.PE(data=current, fast_load=True)
        section = pe.sections[-1]
        # Reconstruct the precise prior icon-only artifact from its unchanged
        # first two guards, then verify the recorded v1 fingerprint explicitly.
        payload = bytearray()
        for spec in m.METHODS.values():
            payload.extend(m.trampoline(section.VirtualAddress + len(payload), spec))
        align = lambda n, unit: (n + unit - 1) // unit * unit
        raw_size = align(len(payload), pe.OPTIONAL_HEADER.FileAlignment)
        old_size = section.SizeOfRawData
        start = section.PointerToRawData
        current[start:] = payload + b'\0' * (raw_size - len(payload))
        header = section.get_file_offset()
        struct.pack_into('<I', current, header + 8, len(payload))
        struct.pack_into('<I', current, header + 16, raw_size)
        optional = pe.DOS_HEADER.e_lfanew + 24
        struct.pack_into('<I', current, optional + 4, pe.OPTIONAL_HEADER.SizeOfCode - old_size + raw_size)
        struct.pack_into('<I', current, optional + 56,
                         align(section.VirtualAddress + len(payload), pe.OPTIONAL_HEADER.SectionAlignment))
        call = pe.get_offset_from_rva(m.TOOLTIP_CALL_RVA)
        native_call = b'\xe8' + struct.pack('<i', m.CONCAT4_RVA - m.TOOLTIP_CALL_RVA - 5)
        current[call:call + 5] = native_call
        legacy = bytes(current)
        self.assertEqual(hashlib.sha256(legacy).hexdigest(), m.PREVIOUS_SHA256)
        manifest = {'original_sha256': m.ORIGINAL_SHA256,
                    'modified_sha256': m.PREVIOUS_SHA256, 'loot_ids': list(m.LOOT_IDS)}
        with tempfile.TemporaryDirectory() as td:
            dll = Path(td) / 'GameAssembly.dll'
            dll.write_bytes(legacy)
            m.backup_path(dll).write_bytes(original)
            m.manifest_path(dll).write_text(json.dumps(manifest))
            with patch.object(m, 'native_client_running', return_value=False):
                with self.assertRaisesRegex(ValueError, 'Restore.*v1'):
                    m.apply(dll)
                self.assertEqual(dll.read_bytes(), legacy)
                self.assertEqual(m.backup_path(dll).read_bytes(), original)
                corrupted_manifest = dict(manifest, modified_sha256='0' * 64)
                m.manifest_path(dll).write_text(json.dumps(corrupted_manifest))
                with self.assertRaisesRegex(ValueError, 'legacy'):
                    m.restore(dll)
                self.assertEqual(dll.read_bytes(), legacy)
                m.manifest_path(dll).write_text(json.dumps(manifest))
                m.restore(dll)
                self.assertEqual(dll.read_bytes(), original)
                result = m.apply(dll)
                self.assertEqual(result['format_version'], 2)
                self.assertEqual(m.backup_path(dll).read_bytes(), original)
                m.restore(dll)
                self.assertEqual(dll.read_bytes(), original)


if __name__ == '__main__':
    unittest.main()
