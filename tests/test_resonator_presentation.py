"""Resonator tooltip values retain the same precision as their rolled effects."""
from pathlib import Path
import sys
import tempfile
from unittest.mock import patch
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'server'))
from profil import Profil
import rezonator as RZ


class ResonatorPresentationTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.profile = Profil(path=str(Path(temporary.name) / 'profil.json'))

    def test_fractional_seconds_and_percent_match_actual_effects(self):
        iid = RZ.create(self.profile, 'equipment_xenoresonator_c-strike-resonator',
                        [['adhesion', 2.4], ['expansion', 6.5], ['aftershock', 12.0]])
        self.assertEqual(RZ.modifiers_str(self.profile, iid),
                         'ADHESION,2.4;EXPANSION,6.5;AFTERSHOCK,12')
        self.assertEqual(RZ.strike_mods(self.profile)['adhesion'], 2.4)

    def test_aegis_entry_buffer_keeps_fractional_seconds(self):
        iid = RZ.create(self.profile, 'equipment_xenoresonator_c-aegis-resonator',
                        [['entry_buffer', 1.2]])
        self.assertEqual(RZ.modifiers_str(self.profile, iid), 'ENTRY_BUFFER,1.2')

    def test_duration_and_damage_modifiers_match_packaged_descriptions(self):
        from parcacik import DR, Atis
        # resonate only needs p. Exercise the actual source calculation directly.
        from types import SimpleNamespace
        system = SimpleNamespace(p=self.profile)
        initial = dict(hasar=100.0, alan=500.0, bitis=100 + DR['sure_sn'])
        for name, factor in (('collapse', 0.75), ('evernight', 1.25)):
            with self.subTest(attribute=name), patch.object(RZ, 'strike_mods', return_value={name: 10}):
                result = Atis.resonate(system, dict(initial), 100)
                duration = result['bitis'] - 100
                self.assertEqual(duration, DR['sure_sn'] * factor)
                self.assertAlmostEqual(result['hasar'] * duration, 100 * DR['sure_sn'] * 1.10)
        with patch.object(RZ, 'strike_mods', return_value={
                'expansion': 10, 'aftershock': 20, 'adhesion': 2.4, 'stagnation': 25}):
            result = Atis.resonate(system, dict(initial), 100)
            self.assertEqual(result['alan'], 550)
            self.assertEqual(result['artci_alan'], 660)
            self.assertEqual(result['hasar'], 75)
            self.assertEqual(result['artci'], 25 * DR['sure_sn'])
            self.assertEqual(result['izle'], 102.4)
            self.assertEqual(result['yavas'], 0.25)


if __name__ == '__main__':
    unittest.main()
