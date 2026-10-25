"""QFC hangar tooltips use percent values and numeric bound-ship IDs."""
import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'server'))
from profil import Profil
from magaza import Magaza
from gemi_modul import ITEMS

class QfcTooltip(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.profile = Profil(path=str(Path(temporary.name) / 'profil.json'))
        with (ROOT / 'server/data/varsayilan/yanitlar.json').open(encoding='utf8') as stream:
            replies = json.load(stream)
        self.shop = Magaza(self.profile, copy.deepcopy(replies), lambda *args: None)

    def test_hangar_contains_percent_bonuses_and_numeric_bound_ship(self):
        item = self.profile.new_item('equipment_core_ax-40')
        self.profile.d.setdefault('qfc', {})[str(item)] = {
            'gemi': 'ship_goliath-plus', 'seviye': 12,
            'nitelikler': [['damage_factions', 34.28], ['shield_penetration', 16.14], ['experience', 10.07]],
        }
        fields = self.shop.hangar_item(item, 'equipment_core_ax-40', 1)
        self.assertEqual(fields['modifiers'], 'DAMAGE_FACTIONS,34.28;SHIELD_PENETRATION,16.14;EXPERIENCE,10.07')
        self.assertEqual(fields['ships'], str(ITEMS['ship_goliath-plus']['kimlik']))

    def test_missing_record_does_not_invent_bonuses(self):
        item = self.profile.new_item('equipment_core_df-40')
        fields = self.shop.hangar_item(item, 'equipment_core_df-40', 1)
        self.assertFalse(fields['modifiers'])

if __name__ == '__main__':
    unittest.main()
