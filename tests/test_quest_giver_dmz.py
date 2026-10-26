"""Demilitarized zone around the pilot's own Mission Control (quest giver), with temporary real pilot profiles."""
import math
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'server'))
import dunya
import harita as H
from profil import Profil

MAP_1_5, MAP_BL_1 = 17, 306
GIVER = (19000, 11100)          # corner of 1-5 far from every portal (harita.structure picks such a corner)


class QuestGiverDmz(unittest.TestCase):
    def world(self, faction=1, map_id=MAP_1_5, giver=GIVER, station=None):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        p = Profil(path=str(Path(tmp.name) / 'pilot.json'))
        p.d['pilot'].update(factionId=faction)
        p.d['konum'].update(mapId=map_id, x=giver[0], y=giver[1])
        sent = []
        w = dunya.World(p, sent.extend, lambda text: None, map_id)
        w.sent = sent
        w.station = station
        w.map_msgs = lambda: [('AssetCreateCommand', dict(assetId=151001790, posX=giver[0], posY=giver[1], factionId=0,
                                                          type=dict(typeValue=H.QUEST_GIVER)))]
        w.load_assets()
        w.hero = dunya.Mover(*giver)
        return w

    def npc(self, w, x, y):
        tip = next(t for t, d in dunya.CFG['tipler'].items() if d.get('hiz', 0) > 0 and not d.get('dost'))
        n = dunya.NPC(91001, tip, x, y)
        n.d = dict(n.d, hasar=0)
        n.next_think = 0
        w.npcs[n.id] = n
        return n

    def beacons(self, w):
        return [f for name, f in w.sent if name == 'BeaconCommand']

    def test_own_x5_mission_control_is_a_demilitarized_zone(self):
        w = self.world()
        x, y = GIVER
        r = H.GIVER_PEACE_RADIUS
        self.assertTrue(w.in_peace(x, y))
        self.assertTrue(w.in_peace(x - r + 10, y))
        self.assertFalse(w.in_peace(x - r - 10, y))
        self.assertTrue(w.in_pvp_peace(x, y))       # protects from enemy pilots too, like a portal

    def test_client_shows_demilitarized_zone_and_clears_it_on_leaving(self):
        w = self.world()
        now = time.time()
        w.check_gates(now)
        beacon = self.beacons(w)[-1]
        self.assertTrue(beacon['inPeaceArea'])
        self.assertFalse(beacon['inStation'])        # not a station: no repair, hangar or equipment change
        w.hero = dunya.Mover(GIVER[0] - H.GIVER_PEACE_RADIUS - 300, GIVER[1])
        w.check_gates(now + 1)
        self.assertFalse(self.beacons(w)[-1]['inPeaceArea'])
        self.assertFalse(w.gate_peace)

    def test_foreign_mission_control_is_neither_usable_nor_protected(self):
        w = self.world(faction=2)
        self.assertEqual(w.givers, [])
        self.assertIn(151001790, w.foreign_assets)
        self.assertFalse(w.in_peace(*GIVER))
        w.check_gates(time.time())
        self.assertFalse(self.beacons(w)[-1]['inPeaceArea'])

    def test_black_light_mission_control_has_no_demilitarized_zone(self):
        # darkorbit.fandom.com/wiki/Demilitarized_zone: BL portals have one, the mission control centre does not
        w = self.world(map_id=MAP_BL_1, giver=(9750, 7300))
        self.assertTrue(w.givers)
        self.assertFalse(w.in_peace(9750, 7300))

    def test_giver_inside_home_station_adds_no_extra_zone(self):
        station = dict(posX=GIVER[0] + 1080, posY=GIVER[1], peaceRadius=1800, type=1)
        w = self.world(station=station)
        self.assertEqual(w.giver_zones(), [])
        self.assertTrue(w.in_peace(*GIVER))           # the station still protects it

    def test_aggressive_alien_does_not_attack_pilot_at_mission_control(self):
        w = self.world()
        n = self.npc(w, GIVER[0] - H.GIVER_PEACE_RADIUS - 400, GIVER[1])
        with patch.object(w, 'aggressive', return_value=True):
            w.think(n, time.time())
        self.assertFalse(n.engaged)
        w.hero = dunya.Mover(GIVER[0] - H.GIVER_PEACE_RADIUS - 150, GIVER[1])   # just outside: it attacks
        n.next_think, n.blocked = 0, 0
        with patch.object(w, 'aggressive', return_value=True):
            w.think(n, time.time())
        self.assertTrue(n.engaged)

    def test_chasing_alien_gives_up_when_pilot_reaches_mission_control(self):
        w = self.world()
        n = self.npc(w, GIVER[0] - H.GIVER_PEACE_RADIUS - 400, GIVER[1])
        n.engaged, n.firing = True, True
        w.think(n, time.time())
        self.assertFalse(n.engaged)
        self.assertIn(('AttackAbortLaserCommand', dict(uid=n.id)), w.sent)
        # it waits at the zone edge, never inside it
        self.assertGreater(math.hypot(n.mover.x1 - GIVER[0], n.mover.y1 - GIVER[1]), H.GIVER_PEACE_RADIUS)

    def test_aliens_do_not_spawn_or_roam_inside_the_zone(self):
        w = self.world()
        self.assertTrue(w.near_zone(*GIVER, 0))
        with patch.object(dunya.random, 'uniform', side_effect=[GIVER[0], GIVER[1], 10000, 6000]):
            x, y = w.random_spot()
        self.assertGreater(math.hypot(x - GIVER[0], y - GIVER[1]), H.GIVER_PEACE_RADIUS)


if __name__ == '__main__':
    unittest.main()
