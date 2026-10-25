"""CBS timed shield lifecycle and native 1.1.115 visual messages."""
import sys
import struct
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'server'))
import cbs
import protocol
from profil import Profil


class DeflectorLifecycle(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.p = Profil(path=str(Path(self.tmp.name) / 'pilot.json'))
        self.p.d['pilot'].update(clanId=11, factionId=1)
        self.p.d['klan'] = dict(id=11, ad='Owners', etiket='OWN', firma=1, diplomasi=[], uyeler={cbs.KL.ad(self.p): {}})
        self.c = cbs.Cbs(self.p, None, lambda text: None)
        self.a = self.c.ast(2)
        self.a.update(durum='kurulu', klan=11)
        loot = next(k for k, d in cbs.MODS.items() if d.get('silah'))
        for slot in (0, 1, 2, 3):
            iid = cbs.ITEM_BASE + slot
            self.a['yuvalar'][str(slot)] = dict(iid=iid)
            self.c.st['moduller'][str(iid)] = dict(loot=loot, seviye=0, can=0 if slot == 3 else 1000, kalkan=0)
        self.now = time.mktime((2026, 10, 25, 12, 0, 0, 0, 0, -1))
        self.a['deflector'].update(acik=True, sn=3600., son=self.now, kapali_bitis=0)
        self.c.shown_assets = [(cbs.asset_id(2), cbs.BATTLESTATION), (cbs.asset_id(2, 2), cbs.SATELLITE), (cbs.asset_id(2, 3), cbs.SATELLITE)]

    def test_rival_manual_shield_downtime_survives_prime_schedule_tick_until_deadline(self):
        self.a['yuvalar']={slot:dict(self.c.module(row['iid'])) for slot,row in self.a['yuvalar'].items()}
        self.a.update(sahip='rakip',rakip='Test Enemy')
        self.a['deflector'].update(acik=False,kapali_bitis=self.now+60)
        with patch.object(cbs,'prime_time',return_value=False), patch.dict(cbs.D['rakip'],{'deflector_prime_disinda':True}):
            self.c.rival_tick(2,self.a,self.now+1)
            self.assertFalse(self.a['deflector']['acik'])
            self.assertTrue(self.c.rival_attackable(2))
            self.c.rival_tick(2,self.a,self.now+60)
            self.assertTrue(self.a['deflector']['acik'])
            self.assertFalse(self.c.rival_attackable(2))

    @staticmethod
    def visuals(msgs, modifier):
        return [f for name, f in msgs if name == 'VisualModifierCommand' and f['modifier'] == modifier]

    def test_join_active_station_shields_hub_and_living_satellites(self):
        assets = {i: cmd[1] for i, _, cmd in self.c.map_assets(2)}
        for aid in (cbs.asset_id(2), cbs.asset_id(2, 2)):
            self.assertEqual([(m['modifier'], m['activated'], m['userId']) for m in assets[aid]['modifier']], [(34, True, aid)])
        self.assertEqual(assets[cbs.asset_id(2)]['modifier'][0]['attribute'], 3600)
        self.assertEqual(assets[cbs.asset_id(2, 3)]['modifier'], [])

    def test_join_downtime_station_has_hub_seconds_counter_only(self):
        self.a['deflector'].update(acik=False, kapali_bitis=self.now + 1800)
        with patch.object(cbs.time, 'time', return_value=self.now):
            assets = {i: cmd[1] for i, _, cmd in self.c.map_assets(2)}
        self.assertEqual([(m['modifier'], m['attribute'], m['activated']) for m in assets[cbs.asset_id(2)]['modifier']], [(35, 1800, True)])
        self.assertEqual(assets[cbs.asset_id(2, 2)]['modifier'], [])

    def test_deactivate_accounts_active_time_and_emits_visuals_outside_management_range(self):
        self.c.near = None
        with patch.object(cbs.time, 'time', return_value=self.now + 20), patch.object(self.c, 'can', return_value=True):
            msgs = self.c.deflector_off(2, 30)
        self.assertEqual(self.a['deflector']['sn'], 3580)
        self.assertEqual(self.a['deflector']['kapali_bitis'], self.now + 1820)
        self.assertEqual({(f['userId'], f['activated']) for f in self.visuals(msgs, 34)}, {(cbs.asset_id(2), False), (cbs.asset_id(2, 2), False)})
        self.assertEqual([(f['userId'], f['attribute'], f['activated']) for f in self.visuals(msgs, 35)], [(cbs.asset_id(2), 1800, True)])

    def test_deadline_reactivates_automatically_and_stops_countdown(self):
        self.a['deflector'].update(acik=False, sn=100, kapali_bitis=self.now + 10)
        with patch.object(self.c, 'deflector_rate', return_value=120):
            msgs = self.c.deflector_tick(2, self.a, self.now + 10)
        self.assertTrue(self.a['deflector']['acik'])
        self.assertEqual(self.a['deflector']['sn'], 120)
        self.assertTrue(all(f['activated'] for f in self.visuals(msgs, 34)))
        self.assertEqual([f['activated'] for f in self.visuals(msgs, 35)], [False])
        self.assertEqual({f['userId'] for f in self.visuals(msgs, 34)}, {cbs.asset_id(2), cbs.asset_id(2, 2)})
        visual_order = [(f['modifier'], f['activated']) for name, f in msgs if name == 'VisualModifierCommand']
        self.assertEqual(visual_order, [(35, False), (34, True), (34, True)])
        self.assertEqual(self.visuals(msgs, 34)[0]['attribute'], 120)

    def test_delayed_tick_only_charges_until_deadline_then_consumes(self):
        self.a['deflector'].update(acik=False, sn=100, kapali_bitis=self.now + 10)
        with patch.object(self.c, 'deflector_rate', return_value=120):
            self.c.deflector_tick(2, self.a, self.now + 40)
        self.assertTrue(self.a['deflector']['acik'])
        self.assertEqual(self.a['deflector']['sn'], 90)

    def test_exhaustion_deadline_starts_at_actual_exhaustion(self):
        self.a['deflector'].update(sn=10)
        with patch.object(self.c, 'deflector_rate', return_value=120):
            msgs = self.c.deflector_tick(2, self.a, self.now + 40)
        self.assertFalse(self.a['deflector']['acik'])
        self.assertEqual(self.a['deflector']['sn'], 60)
        self.assertEqual(self.a['deflector']['kapali_bitis'], self.now + 10 + cbs.D['deflector_bitince_dk'] * 60)
        self.assertEqual(self.visuals(msgs, 35)[0]['attribute'], cbs.D['deflector_bitince_dk'] * 60 - 30)

    def test_cannot_reactivate_early_by_pressing_deactivate_again(self):
        self.a['deflector'].update(acik=False, kapali_bitis=self.now + 1800)
        with patch.object(cbs.time, 'time', return_value=self.now), patch.object(self.c, 'can', return_value=True):
            msgs = self.c.deflector_off(2, 30)
        self.assertEqual(msgs, self.c.error('DEFLECTOR_ALREADY_OFF'))
        self.assertFalse(self.a['deflector']['acik'])

    def test_downtime_charging_splits_prime_time_boundary(self):
        start = time.mktime((2026, 10, 25, 17, 59, 50, 0, 0, -1))
        self.a['deflector'].update(acik=False, sn=0, son=start, kapali_bitis=start+1800)
        self.c.deflector_tick(2, self.a, start+20)
        self.assertEqual(self.a['deflector']['sn'], 120)

    def test_deactivation_increments_shared_version(self):
        before = self.a.get('surum', 0)
        with patch.object(cbs.time, 'time', return_value=self.now), patch.object(self.c, 'can', return_value=True):
            self.c.deflector_off(2, 30)
        self.assertGreater(self.a.get('surum', 0), before)


    def test_long_delayed_tick_recharges_and_consumes_after_full_cycle(self):
        self.a['deflector'].update(sn=10)
        with patch.object(self.c, 'deflector_rate', return_value=120):
            self.c.deflector_tick(2, self.a, self.now + 8000)
        self.assertTrue(self.a['deflector']['acik'])
        self.assertEqual(self.a['deflector']['sn'], 13610)

    def test_rival_prime_time_change_refreshes_shared_version_and_visuals(self):
        self.a['sahip'] = 'rakip'
        # Rival slots contain module values directly.
        self.a['yuvalar'] = {s: self.c.module(y['iid']) for s, y in self.a['yuvalar'].items()}
        before = self.a.get('surum', 0)
        with patch.object(cbs, 'prime_time', return_value=True), patch.object(self.c, 'rival_repair', return_value=[]):
            msgs = self.c.rival_tick(2, self.a, self.now)
        self.assertFalse(self.a['deflector']['acik'])
        self.assertGreater(self.a.get('surum', 0), before)
        self.assertEqual({(f['userId'], f['activated']) for f in self.visuals(msgs, 34)}, {(cbs.asset_id(2), False), (cbs.asset_id(2, 2), False)})

    def test_visual_packet_matches_native_reader_rotations_and_field_order(self):
        # Independent decode of VisualModifierCommand.read at .115 0x116e8d20.
        for modifier, active, seconds in ((34, True, 172800), (34, False, 0), (35, True, 1800), (35, False, 0)):
            with self.subTest(modifier=modifier, active=active):
                fields = self.c.deflector_modifier(cbs.asset_id(2), modifier, active, seconds)
                packet = protocol.encode_message('VisualModifierCommand', fields)
                command, uid, vm, attr, size, count, enabled = struct.unpack('>HIhIHIB', packet)
                uid = ((uid >> 12) | (uid << 20)) & 0xffffffff
                attr = ((attr << 7) | (attr >> 25)) & 0xffffffff
                count = ((count >> 14) | (count << 18)) & 0xffffffff
                self.assertEqual((command, uid, vm, attr, size, count, bool(enabled)), (280, cbs.asset_id(2), modifier, seconds, 0, 0, active))

if __name__ == '__main__':
    unittest.main()
