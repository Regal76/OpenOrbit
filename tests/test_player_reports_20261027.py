"""Player reports 2026-10-27: repair bot menu item, auction listing and Iris price, other companies' pirate portals."""
import copy
import json
from pathlib import Path
import sys
import tempfile
import time
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'server'))
import harita as H
from profil import Profil
from magaza import Magaza
import muzayede as MZ

REPBOT = 'equipment_extra_repbot_rep'


class PlayerReports(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.profile = Profil(path=str(Path(temporary.name) / 'profil.json'))
        with (ROOT / 'server/data/varsayilan/giris.json').open(encoding='utf8') as stream:
            defaults = json.load(stream)
        template = next(row for row in defaults['hazir'] if row['_m'] == 'MenuInitializationCommand')
        self.profile.patch_template('MenuInitializationCommand', template)
        with (ROOT / 'server/data/varsayilan/yanitlar.json').open(encoding='utf8') as stream:
            replies = json.load(stream)
        self.shop = Magaza(self.profile, copy.deepcopy(replies), lambda *args: None)
        self.auction = MZ.Muzayede(self.profile)
        self.auction.m = self.shop

    def set_extras(self, extras):
        self.profile.d['ekipman']['extra'] = list(extras)

    def test_repair_bot_item_follows_equipped_bot(self):
        self.set_extras(['equipment_extra_repbot_rep-4'])
        st = self.profile.menu_status(REPBOT)
        self.assertEqual(st['iconLootId'], 'equipment_extra_repbot_rep-4')
        self.assertTrue(st['available'] and st['activatable'])
        replacements = st['toolTipSlotBar']['commandList'][0]['wildCardReplacements']
        self.assertEqual(replacements[0]['replacement'], 'equipment_extra_repbot_rep-4')

    def test_repair_bot_item_disabled_without_bot(self):
        self.set_extras([])
        st = self.profile.menu_status(REPBOT)
        self.assertFalse(st['available'])
        self.assertFalse(st['activatable'])

    def test_other_company_pirate_portals_are_usable_but_own_first(self):
        gates = H.gates(91, 2)
        own = [g for g in gates if g.get('yalniz_firma') == 2]
        foreign = [g for g in gates if g.get('yalniz_firma') not in (None, 2)]
        self.assertTrue(own and foreign)
        self.assertTrue(all(g in gates[:len(gates) - len(foreign)] for g in own))

    def test_iris_instant_price_follows_owned_drones(self):
        lot = MZ.LOTS[('hour', 'drone_iris')]
        first = self.auction.unit_price(lot)
        self.profile.d['dronlar'].append({'lootId': 'drone_iris', 'kimlik': 990001})
        self.assertGreater(self.auction.unit_price(lot), first)
        self.assertEqual(self.auction.data(lot, time.time())['price'], self.auction.unit_price(lot))

    def listed(self):
        cmd = self.auction.list_cmd()[1]
        return {row['id'] for row in cmd['auctionList']}

    def test_owned_ship_and_design_leave_the_auction_list(self):
        listed = self.listed()
        self.assertNotIn('ship_goliath', listed)          # the default profile owns a Goliath
        self.assertIn('ship_leonov', listed)
        self.assertIn('ship_goliath_design_jade', listed)
        next(iter(self.profile.d['gemiler'].values())).setdefault('tasarimlar', []).append('ship_goliath_design_jade')
        listed = self.listed()
        self.assertNotIn('ship_goliath_design_jade', listed)
        self.assertIn('ship_goliath_design_amber', listed)
        self.profile.d['gemiler']['777'] = {'lootId': 'ship_leonov', 'hangarId': 777, 'konfigler': {'1': {}, '2': {}},
                                            'aktif_konfig': 1, 'favori': False, 'dron_konfig': {'1': {}, '2': {}}}
        self.assertNotIn('ship_leonov', self.listed())

    def test_iris_leaves_the_list_at_the_drone_limit(self):
        self.assertIn('drone_iris', self.listed())
        self.profile.d['dronlar'] = [{'lootId': 'drone_iris', 'kimlik': 990000 + i} for i in range(8)]
        self.assertNotIn('drone_iris', self.listed())
        reply = self.auction.quick({'lootId': 'drone_iris', 'type': 'hour'}, time.time())
        self.assertFalse(reply[0][1]['success'])


class CloakedPilot(unittest.TestCase):
    """An alien already attacking keeps at it after the pilot cloaks, until EMP-01 resets its target; cloaking alone also
    stops new aliens from noticing the pilot."""

    def setUp(self):
        import dunya
        self.dunya = dunya
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.p = Profil(path=str(Path(tmp.name) / 'pilot.json'))
        self.p.d['konum'].update(mapId=17, x=10000, y=6000)
        self.sent = []
        self.w = dunya.World(self.p, self.sent.extend, lambda text: None, 17)
        self.w.hero = dunya.Mover(10000, 6000)
        tip = next(t for t, d in dunya.CFG['tipler'].items() if d.get('hiz', 0) > 0 and not d.get('dost'))
        self.n = dunya.NPC(91001, tip, 10400, 6000)
        self.n.d = dict(self.n.d, hasar=0)
        self.n.next_think = 0
        self.w.npcs[self.n.id] = self.n

    def cloak(self):
        self.p.d['cpu_gizli'] = True

    def test_engaged_alien_keeps_attacking_cloaked_pilot(self):
        self.n.engaged = True
        self.cloak()
        self.w.think(self.n, time.time())
        self.assertTrue(self.n.engaged)

    def test_idle_aggressive_alien_ignores_cloaked_pilot(self):
        self.cloak()
        from unittest.mock import patch
        with patch.object(self.w, 'aggressive', return_value=True):
            self.w.think(self.n, time.time())
        self.assertFalse(self.n.engaged)


if __name__ == '__main__':
    unittest.main()
