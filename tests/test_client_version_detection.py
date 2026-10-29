"""The panel must read the game's own version from a client whose folder name carries none (the official installer's
"DarkOrbit Unity" folder), not the Unity engine version that DarkOrbit.exe reports as its file version."""
import os
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'server'))
sys.path.insert(0, str(ROOT / 'server' / 'panel'))

import istemci


def unity_string(s):
    """Unity serialises strings as a 4-byte little-endian length, the bytes and zero padding to 4 bytes."""
    b = s.encode()
    return len(b).to_bytes(4, 'little') + b + b'\0' * (4 - len(b) % 4 if len(b) % 4 else 0)


class ClientVersionDetectionTest(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.folder = os.path.join(temporary.name, 'DarkOrbit Unity')
        os.makedirs(os.path.join(self.folder, istemci.DATA_DIR))

    def write_managers(self, data):
        with open(os.path.join(self.folder, istemci.DATA_DIR, 'globalgamemanagers'), 'wb') as fh:
            fh.write(data)

    def test_bundle_version_beats_engine_version(self):
        self.write_managers(b'\0' * 16 + unity_string('2022.3.58f1') + b'\0' * 8 + unity_string('1.0') + unity_string('1.0')
                            + unity_string('1.1.115') + b'\0' * 8 + unity_string('2022.3.58f1'))
        self.assertEqual(istemci.bundle_version(self.folder), '1.1.115')
        self.assertEqual(istemci.version_of(self.folder), '1.1.115')

    def test_folder_name_still_wins(self):
        named = os.path.join(os.path.dirname(self.folder), 'DarkOrbit_Version1.1.114')
        os.rename(self.folder, named)
        self.assertEqual(istemci.version_of(named), '1.1.114')

    def test_unknown_without_data(self):
        self.write_managers(b'\0' * 32 + unity_string('2022.3.58f1'))
        self.assertIsNone(istemci.bundle_version(self.folder))
        self.assertIsNone(istemci.version_of(self.folder))      # no DarkOrbit.exe either: nothing to report

    def test_supported_ignores_engine_version(self):
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        path = os.path.join(temp_dir.name, 'surum.txt')
        with open(path, 'w', encoding='utf8') as fh:
            fh.write('2022.3.58\n')
        orig = istemci.SURUM_DOSYASI
        istemci.SURUM_DOSYASI = path
        self.addCleanup(setattr, istemci, 'SURUM_DOSYASI', orig)
        self.assertEqual(istemci.supported(), istemci.DESTEKLENEN)


if __name__ == '__main__':
    unittest.main()
