"""Native buy_* double-click scope and reversible PE correction."""
import importlib.util
import os
from pathlib import Path
import struct
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
sys.path.insert(0, str(ROOT/'_trial/drone-deps'))
import quick_buy_double_click_compat as compat
try:
    import pefile
    import unicorn
except ImportError:
    unicorn = None


class QuickBuyDoubleClick(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        fixture = Path(os.environ.get('QUICK_BUY_NATIVE_DLL',
                       ROOT/'_trial/quickbuy-double-click/GameAssembly.input.dll'))
        if unicorn is None or not fixture.exists():
            raise unittest.SkipTest('Exact native fixture and Unicorn required')
        cls.original = fixture.read_bytes()
        cls.modified = compat.patch_bytes(cls.original)
        import quick_buy_native_audit
        cls.native = quick_buy_native_audit

    def probe(self, raw, item, double=False, **kw):
        return self.native.probe_user_item(raw, item, double, **kw)

    def test_red_original_buys_on_single_callback_green_only_double_publishes(self):
        for bar in ('categoryBar', 'standardSlotBar', 'premiumSlotBar', 'proActionBar'):
            with self.subTest(bar=bar):
                old = self.probe(self.original, 'buy_ammunition_laser_lcb-10', bar=bar, callback=True)
                self.assertEqual(len(old['events']), 1)
                self.assertFalse(old['events'][0]['doubleClick'])
                single = self.probe(self.modified, 'buy_ammunition_laser_lcb-10', bar=bar, callback=True)
                self.assertEqual(single['events'], [])
                double = self.probe(self.modified, 'buy_ammunition_laser_lcb-10', True, bar=bar, callback=True)
                self.assertEqual(len(double['events']), 1)
                self.assertEqual(double['events'][0], dict(item=double['expected_item'],
                                 doubleClick=True, bar=double['expected_bar']))

    def test_ordinary_items_keep_actual_native_single_click_event(self):
        for item in ('ammunition_laser_lcb-10', 'ammunition_rocket_plt-2021',
                     'ammunition_mine_acm-01', 'equipment_extra_cpu', 'buyX',
                     'Buy_ammunition_laser_lcb-10', 'bu', '', None):
            for bar in ('categoryBar', 'standardSlotBar', 'premiumSlotBar', 'proActionBar'):
                with self.subTest(item=item, bar=bar):
                    old = self.probe(self.original, item, bar=bar, callback=True)
                    new = self.probe(self.modified, item, bar=bar, callback=True)
                    self.assertEqual(new['events'], old['events'])
                    self.assertEqual(len(new['events']), 1)
                    self.assertFalse(new['events'][0]['doubleClick'])

    def test_guard_preserves_context_and_bool_byte_at_relocated_image_bases(self):
        # High bool argument bytes deliberately contain nonzero garbage. Only
        # the actual native byte parameter determines single vs double.
        for image_base in (0x10000000, 0x18000000):
            for item, double, ignored in (('buy_', False, True),
                                          ('buy_future', False, True),
                                          ('buy_ammunition_laser_lcb-10', True, False),
                                          ('ammunition_laser_lcb-10', False, False),
                                          ('bu', False, False), (None, False, False)):
                with self.subTest(base=image_base, item=item, double=double):
                    out = self.probe(self.modified, item, double, base=image_base, guard_only=True)
                    self.assertEqual(out['ignored'], ignored)
                    self.assertTrue(out['context_unchanged'])
                    # Allowed path has replayed push ebp/mov ebp,esp/sub esp,40.
                    self.assertEqual(out['esp_delta'], 4 if ignored else -44)
                    self.assertEqual(out['registers'][:-1], out['initial_registers'][:-1])
                    if ignored:
                        self.assertEqual(out['registers'], out['initial_registers'])
                        self.assertEqual(out['flags'], 0x646)
                    else:
                        reference = self.probe(self.original, item, double, base=image_base, guard_only=True)
                        self.assertEqual(out['flags'], reference['flags'])
                        self.assertEqual(out['registers'], reference['registers'])
                    self.assertEqual(out['xmm'], [int.from_bytes(bytes([i+1])*16,'little') for i in range(8)])
        for null in ('this', 'item'):
            out = self.probe(self.modified, 'buy_anything', null_context=null, guard_only=True)
            self.assertFalse(out['ignored'])
            self.assertTrue(out['context_unchanged'])

    def test_all_recorded_quick_buy_ids_use_double_callback_and_existing_purchase_action(self):
        import json
        menu = next(x for x in json.loads((ROOT/'server/data/varsayilan/giris.json').read_text())['hazir']
                    if x['_m']=='MenuInitializationCommand')
        ids = [item['status']['menuItemId'] for category in menu['categories']
               for item in category['menuItems'] if item['status']['menuItemId'].startswith('buy_')]
        self.assertEqual(len(ids), 8)
        for item in ids:
            self.assertEqual(self.probe(self.modified, item, guard_only=True)['ignored'], True)
            self.assertEqual(self.probe(self.modified, item, True, guard_only=True)['ignored'], False)
        for bar in ('categoryBar', 'standardSlotBar', 'premiumSlotBar'):
            self.assertEqual(self.native.probe('oneShot', bar, True)['actionType'], 1)

    def test_pe_preserves_every_existing_section_payload_except_useritem_hook(self):
        old = pefile.PE(data=self.original, fast_load=True)
        new = pefile.PE(data=self.modified, fast_load=True)
        self.assertEqual(old.FILE_HEADER.NumberOfSections, new.FILE_HEADER.NumberOfSections)
        self.assertEqual(old.OPTIONAL_HEADER.ImageBase, new.OPTIONAL_HEADER.ImageBase)
        self.assertEqual(old.OPTIONAL_HEADER.DllCharacteristics, new.OPTIONAL_HEADER.DllCharacteristics)
        self.assertEqual(old.OPTIONAL_HEADER.DATA_DIRECTORY[5].__dict__, new.OPTIONAL_HEADER.DATA_DIRECTORY[5].__dict__)
        at = old.get_offset_from_rva(compat.ENTRY_RVA)
        for section in old.sections:
            start, size = section.PointerToRawData, section.SizeOfRawData
            actual = bytearray(self.modified[start:start+size])
            if start <= at < start+size:
                actual[at-start:at-start+6] = self.original[at:at+6]
            self.assertEqual(bytes(actual), self.original[start:start+size])
        last = new.sections[-1]
        self.assertLessEqual(last.VirtualAddress+last.Misc_VirtualSize, new.OPTIONAL_HEADER.SizeOfImage)
        self.assertEqual(last.PointerToRawData+last.SizeOfRawData, len(self.modified))

    def test_apply_restore_reject_running_client_tampering_and_unknown_input(self):
        with self.assertRaisesRegex(ValueError, 'fingerprint'):
            compat.patch_bytes(b'unknown')
        with tempfile.TemporaryDirectory() as folder:
            dll = Path(folder)/'GameAssembly.dll'
            dll.write_bytes(self.original)
            with patch.object(compat, 'native_client_running', return_value=True):
                with self.assertRaises(RuntimeError):compat.apply(dll)
            self.assertEqual(dll.read_bytes(), self.original)
            with patch.object(compat, 'native_client_running', return_value=False):
                compat.apply(dll);compat.apply(dll)
                self.assertEqual(dll.read_bytes(), self.modified)
                altered = bytearray(self.modified);altered[-1] ^= 1;dll.write_bytes(altered)
                with self.assertRaisesRegex(ValueError, 'fingerprint'):compat.restore(dll)
                self.assertEqual(dll.read_bytes(), altered)
                dll.write_bytes(self.modified)
                compat.restore(dll);compat.restore(dll)
                self.assertEqual(dll.read_bytes(), self.original)


if __name__ == '__main__':
    unittest.main()
