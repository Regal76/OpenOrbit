"""Run all three native Hangar HUD guard sites, preserving combat-area state."""
import importlib.util
import json
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
    from unicorn import Uc, UC_ARCH_X86, UC_MODE_32, UC_HOOK_CODE
    from unicorn.x86_const import *
except ImportError:
    Uc = None


def load_module():
    spec = importlib.util.spec_from_file_location('hangar_hud_compat', ROOT / 'tools/cbs_hangar_hud_compat.py')
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    return m


def relocation_directory(pe):
    directory = pe.OPTIONAL_HEADER.DATA_DIRECTORY[5]  # IMAGE_DIRECTORY_ENTRY_BASERELOC
    return pe.get_data(directory.VirtualAddress, directory.Size)


def relocation_entries(pe):
    # Walk the real relocation block bytes. pefile's object model for this DLL's
    # 1.7 million entries consumes gigabytes; the loader needs only packed words.
    data = relocation_directory(pe); pos = 0
    while pos < len(data):
        page, size = struct.unpack_from('<II', data, pos)
        if size < 8 or size % 2 or pos+size > len(data):
            raise AssertionError('Malformed native relocation block')
        for entry, in struct.iter_unpack('<H', data[pos+8:pos+size]):
            kind = entry >> 12
            if kind not in (0, 3): raise AssertionError('Unexpected native relocation type: %d' % kind)
            yield kind, page+(entry&0xfff)
        pos += size


class HangarHudCompatibility(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.m = load_module(); cls.images = {}
        fixture = os.environ.get('CBS_HUD_NATIVE_DLL')
        cls.original = Path(fixture).read_bytes() if fixture else None
        cls.modified = cls.m.patch_bytes(cls.original) if fixture else None

    def test_unknown_binary_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'fingerprint'):
            self.m.patch_bytes(b'unknown')

    def execute(self, raw, base, site, peace, station, initial_flags):
        import pefile
        key = (self.m.digest(raw), base)
        if key not in self.images:
            pe = pefile.PE(data=raw, fast_load=True)
            # Model the Windows loader: map sections, then add the relocation
            # delta at every real HIGHLOW target, including any stale hook entry.
            mapped = bytearray(pe.get_memory_mapped_image())
            delta = base-pe.OPTIONAL_HEADER.ImageBase
            if delta:
                for kind, rva in relocation_entries(pe):
                    if kind == 3:
                        value, = struct.unpack_from('<I', mapped, rva)
                        struct.pack_into('<I', mapped, rva, (value+delta)&0xffffffff)
            self.images[key] = bytes(mapped)
        image = self.images[key]; u = Uc(UC_ARCH_X86, UC_MODE_32)
        u.mem_map(base, (len(image)+4095)&~4095); u.mem_write(base, image)
        heap, stack = 0x30000000, 0x40000000
        u.mem_map(heap, 0x10000); u.mem_map(stack, 0x10000)
        settings, bindable = heap+0x100, heap+0x400
        u.mem_write(settings+0xd0, bytes([int(peace)]))
        u.mem_write(settings+0xd4, struct.pack('<I', 0 if station is None else bindable))
        u.mem_write(bindable+0xc, bytes([int(bool(station))]))
        memory_before = bytes(u.mem_read(heap, 0x10000))
        registers = [UC_X86_REG_EAX, UC_X86_REG_EBX, UC_X86_REG_ECX, UC_X86_REG_EDX,
                     UC_X86_REG_ESI, UC_X86_REG_EDI, UC_X86_REG_EBP, UC_X86_REG_ESP]
        values = [settings, 0x11111111, 0x22222222, 0x33333333, 0x44444444,
                  0x55555555, stack+0x8000, stack+0x6000]
        u.mem_write(values[-1], b'\xa5'*0x1000)
        for r, v in zip(registers, values): u.reg_write(r, v)
        for i in range(8): u.reg_write(UC_X86_REG_XMM0+i, int.from_bytes(bytes([i+1])*16, 'little'))
        xmm = [u.reg_read(UC_X86_REG_XMM0+i) for i in range(8)]
        u.reg_write(UC_X86_REG_EFLAGS, initial_flags)
        destinations = ([site+7] if site in self.m.VISIBILITY_RVAS else
                        [self.m.CLOSE_RVA, self.m.KEEP_OPEN_RVA])
        observed = []
        def stop(emu, address, size, data):
            if address-base in destinations:
                observed.append(address-base); emu.emu_stop()
        u.hook_add(UC_HOOK_CODE, stop)
        u.emu_start(base+site, base+max(destinations)+1, count=300)
        final_values = [u.reg_read(r) for r in registers]
        expected_values = list(values)
        if site in self.m.VISIBILITY_RVAS:
            expected_values[0] = int(bool(peace or station)) if raw == self.modified else int(peace)
        self.assertEqual(final_values, expected_values)
        self.assertEqual([u.reg_read(UC_X86_REG_XMM0+i) for i in range(8)], xmm)
        self.assertEqual(bytes(u.mem_read(heap, 0x10000)), memory_before)
        self.assertEqual(bytes(u.mem_read(values[-1], 0x1000)), b'\xa5'*0x1000)
        self.assertEqual(len(observed), 1)
        return observed[0], u.reg_read(UC_X86_REG_EFLAGS)

    @unittest.skipUnless(Uc is not None and os.environ.get('CBS_HUD_NATIVE_DLL'), 'Unicorn and exact native fixture required')
    def test_all_three_actual_sites_every_boolean_null_path_aslr_and_cpu_context(self):
        for site in self.m.EXPECTED:
            for base in (0x10000000, 0x18000000):
                for peace in (False, True):
                    for station in (None, False, True):
                        for flags in (0xad7, 0xed7):
                            with self.subTest(site=hex(site), base=hex(base), peace=peace, station=station, flags=hex(flags)):
                                old, old_flags = self.execute(self.original, base, site, peace, station, flags)
                                new, new_flags = self.execute(self.modified, base, site, peace, station, flags)
                                if site == self.m.CLOSE_GUARD_RVA:
                                    self.assertEqual(old, self.m.KEEP_OPEN_RVA if peace else self.m.CLOSE_RVA)
                                    self.assertEqual(new, self.m.KEEP_OPEN_RVA if peace or station else self.m.CLOSE_RVA)
                                else:
                                    self.assertEqual((old, new), (site+7, site+7))
                                self.assertEqual(new_flags, old_flags)

    @unittest.skipUnless(os.environ.get('CBS_HUD_NATIVE_DLL'), 'Exact native fixture required')
    def test_no_original_highlow_relocation_overlaps_a_replaced_instruction_or_new_trampoline(self):
        import pefile
        before = pefile.PE(data=self.original, fast_load=True)
        after = pefile.PE(data=self.modified, fast_load=True)
        self.assertEqual(relocation_directory(after), relocation_directory(before))
        highlow_count = 0
        overlaps = {site:[] for site in self.m.EXPECTED}
        section = after.sections[-1]
        new_section_overlaps = []
        for kind, rva in relocation_entries(before):
            if kind != 3: continue
            highlow_count += 1
            for site, instruction in self.m.EXPECTED.items():
                if rva < site+len(instruction) and rva+4 > site: overlaps[site].append(rva)
            if section.VirtualAddress <= rva < section.VirtualAddress+section.Misc_VirtualSize:
                new_section_overlaps.append(rva)
        self.assertGreater(highlow_count, 0, 'Inspect the actual native relocation table')
        self.assertEqual(overlaps, {site:[] for site in self.m.EXPECTED})
        self.assertEqual(new_section_overlaps, [])

    @unittest.skipUnless(os.environ.get('CBS_HUD_NATIVE_DLL'), 'Exact native fixture required')
    def test_pe_only_changes_three_sites_and_new_section_and_exact_reversible_application(self):
        import pefile
        m = self.m; original = self.original; modified = self.modified
        p = pefile.PE(data=original, fast_load=True); patched = pefile.PE(data=modified, fast_load=True)
        self.assertEqual(len(patched.sections), len(p.sections)+1)
        self.assertEqual(patched.sections[-1].Name.rstrip(b'\0'), b'.cbshud')
        mutable = set()
        for site, expected in m.EXPECTED.items():
            at = p.get_offset_from_rva(site)
            self.assertEqual(original[at:at+len(expected)], expected)
            self.assertEqual(modified[at], 0xe9)
            mutable.update(range(at, at+len(expected)))
        # Every existing section, including all previous compatibility layers, stays exact.
        for section in p.sections:
            start = section.PointerToRawData; end = start+section.SizeOfRawData
            self.assertEqual(bytes(b for i,b in enumerate(original[start:end], start) if i not in mutable),
                             bytes(b for i,b in enumerate(modified[start:end], start) if i not in mutable))
        # Existing PE headers differ only in documented size/count fields and new section header.
        pe = struct.unpack_from('<I', original, 0x3c)[0]; opt = pe+24
        header = p.sections[-1].get_file_offset()+40
        for start, count in ((pe+6,2), (opt+4,4), (opt+56,4), (header,40)):
            mutable.update(range(start,start+count))
        self.assertEqual(bytes(b for i,b in enumerate(original) if i not in mutable),
                         bytes(b for i,b in enumerate(modified[:len(original)]) if i not in mutable))
        with tempfile.TemporaryDirectory() as directory:
            dll = Path(directory)/'GameAssembly.dll'; dll.write_bytes(original)
            with patch.object(m, 'native_client_running', return_value=True):
                with self.assertRaises(RuntimeError): m.apply(dll)
            self.assertEqual(dll.read_bytes(), original)
            with patch.object(m, 'native_client_running', return_value=False):
                m.apply(dll); m.apply(dll); self.assertEqual(dll.read_bytes(), modified)
                corrupt = bytearray(modified); corrupt[-1] ^= 1; dll.write_bytes(corrupt)
                with self.assertRaises(ValueError): m.restore(dll)
                self.assertEqual(dll.read_bytes(), corrupt)
                dll.write_bytes(modified); m.restore(dll); m.restore(dll)
                self.assertEqual(dll.read_bytes(), original)

    @unittest.skipUnless(os.environ.get('CBS_HUD_NATIVE_DLL'), 'Exact native fixture required')
    def test_changed_hook_and_corrupted_backup_are_rejected_without_dll_mutation(self):
        import pefile
        m = self.m
        changed = bytearray(self.original)
        changed[pefile.PE(data=self.original, fast_load=True).get_offset_from_rva(m.CLOSE_GUARD_RVA)] ^= 1
        with self.assertRaisesRegex(ValueError, 'fingerprint'): m.patch_bytes(bytes(changed))
        with tempfile.TemporaryDirectory() as directory:
            dll = Path(directory)/'GameAssembly.dll'; dll.write_bytes(self.original)
            with patch.object(m, 'native_client_running', return_value=False):
                m.apply(dll)
                m.backup_path(dll).write_bytes(b'bad backup')
                with self.assertRaisesRegex(ValueError, 'backup fingerprint'): m.restore(dll)
                self.assertEqual(dll.read_bytes(), self.modified)


    @unittest.skipUnless(os.environ.get('CBS_HUD_NATIVE_DLL'), 'Exact native fixture required')
    def test_forged_manifest_cannot_authorize_an_unsupported_current_image(self):
        m = self.m
        with tempfile.TemporaryDirectory() as directory:
            dll = Path(directory)/'GameAssembly.dll'; dll.write_bytes(self.original)
            with patch.object(m, 'native_client_running', return_value=False):
                m.apply(dll)
                corrupt = bytearray(self.modified); corrupt[-1] ^= 1; corrupt = bytes(corrupt)
                dll.write_bytes(corrupt)
                manifest = json.loads(m.manifest_path(dll).read_text())
                manifest['modified_sha256'] = m.digest(corrupt)
                m.manifest_path(dll).write_text(json.dumps(manifest))
                with self.assertRaisesRegex(ValueError, 'manifest'): m.restore(dll)
                self.assertEqual(dll.read_bytes(), corrupt)
                with self.assertRaisesRegex(ValueError, 'manifest'): m.apply(dll)
                self.assertEqual(dll.read_bytes(), corrupt)


if __name__ == '__main__': unittest.main()
