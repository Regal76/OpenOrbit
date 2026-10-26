"""Player attacks use enemy diplomacy, real DMZs, and current target state."""
import sys
import threading
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'server'))
import oyuncu_savas as PVP


class Profile:
    def __init__(self, uid, faction):
        self.user_id = uid
        self.premium = False
        self.d = {'pilot': {'clanId': 0, 'factionId': faction},
                  'gemi': {'hitPoints': 10000, 'shield': 100, 'shieldMax': 1000},
                  'secili': {'roket': 'ammunition_rocket_r-310', 'lazer': 'ammunition_laser_lcb-10'}}
        self.inventory = {self.d['secili']['roket']: 10}
        self.ach = Mock()
        self.bonuses = {}
    def mods(self): return self.bonuses
    def lab_bonus(self, index): return 0
    def use_ammo(self, ammo, count):
        if self.inventory.get(ammo, 0) < count: return None
        self.inventory[ammo] -= count
        return self.inventory[ammo]
    def set_hull(self, **values):
        for key, value in values.items():
            self.d['gemi'][key] = min(self.d['gemi']['shieldMax'], value) if key == 'shield' else value


def world(uid, faction):
    w = SimpleNamespace(hid=uid, p=Profile(uid, faction), running=True, hero_dead=False,
                        jumping=False, reload_pending=False, map_id='4', invuln_until=0,
                        invulnerable=False, oyuncular={}, target=None, attacking=True,
                        rocket_ready=0, sent=[], timers=[])
    w.lock = threading.RLock()
    w.hero_pos = Mock(return_value=(5000 + uid, 5000))
    w.gizli = Mock(return_value=False)
    w.in_pvp_peace = Mock(return_value=False)
    w.grup_uyesi = Mock(return_value=False)
    w.hero_etki = SimpleNamespace(invulnerable=Mock(return_value=False))
    w.send = w.sent.extend
    w.laser_stop = Mock()
    w.side_laser = Mock()
    w.end_invuln = Mock()
    w.abilities = SimpleNamespace(reveal=Mock(), rocket_ms=lambda ms, now: ms)
    w.items = SimpleNamespace(reveal=Mock())
    w.stop_repair = Mock()
    w.ammo_msgs = Mock(return_value=[])
    w.ammo_out = Mock(return_value=(None, []))
    w.rocket_hit = Mock(return_value=1)
    w.rocket_msg = lambda uid, hit, kind, saved=False: ('RocketVisual', {'target': uid})
    w.later = lambda delay, callback: w.timers.append((delay, callback))
    w.lab_spend = Mock()
    def hurt(dmg, **kwargs):
        if kwargs.get('shield_only'):
            w.p.d['gemi']['shield'] = max(0, w.p.d['gemi']['shield'] - dmg)
        else:
            w.p.d['gemi']['hitPoints'] -= dmg
        return [('AttackHitCommand', {'damage': dmg, 'attackerId': kwargs['source_player'].hid})]
    w.hurt_hero = Mock(side_effect=hurt)
    return w


class PlayerCombat(unittest.TestCase):
    def setUp(self):
        relation = patch.object(PVP.KL, 'iliski', return_value=0)
        relation.start(); self.addCleanup(relation.stop)
        self.reset_pair()

    def reset_pair(self):
        PVP.KL.iliski.return_value = 0
        self.a, self.b = world(1, 1), world(2, 2)
        shared = SimpleNamespace(uyeler=[self.a, self.b])
        self.a.ortak = self.b.ortak = shared
        self.a.oyuncular[self.b.hid] = ()
        self.b.oyuncular[self.a.hid] = ()
        self.a.oyuncu = lambda uid: self.b if uid == self.b.hid and uid in self.a.oyuncular else None
        self.b.oyuncu = lambda uid: self.a if uid == self.a.hid and uid in self.b.oyuncular else None

    def test_enemy_at_cbs_can_be_attacked(self):
        self.assertEqual(PVP.attack_error(self.a, self.b, 100), [])

    def test_same_faction_warned_but_blocked_only_on_own_start_maps(self):
        # Turkish board FAQ 127509: attacking your own company is allowed (penalised on kill), except on its first two maps
        self.b.p.d['pilot']['factionId'] = 1
        self.assertEqual(PVP.attack_error(self.a, self.b, 100), [])
        self.assertTrue(any('friendlyfire' in str(m) for m in self.a.sent))
        self.a.map_id = self.b.map_id = '1'
        self.assertIn('no_attack_on_start_maps', str(PVP.attack_error(self.a, self.b, 100)))

    def test_friendly_group_clan_allies_nap_are_blocked(self):
        for mode in ['clan', 'ally', 'nap', 'group']:
            with self.subTest(mode=mode):
                self.reset_pair()
                if mode == 'clan':
                    self.a.p.d['pilot']['clanId'] = self.b.p.d['pilot']['clanId'] = 7
                elif mode in ('ally', 'nap'):
                    PVP.KL.iliski.return_value = 1 if mode == 'ally' else 2
                else: self.a.grup_uyesi.return_value = True
                self.assertTrue(PVP.attack_error(self.a, self.b, 100))

    def test_explicit_war_allows_same_faction(self):
        self.b.p.d['pilot']['factionId'] = 1
        PVP.KL.iliski.return_value = 3
        self.assertEqual(PVP.attack_error(self.a, self.b, 100), [])

    def test_state_visibility_and_both_dmzs_are_rechecked(self):
        for side, field in [('a', 'jumping'), ('b', 'jumping'), ('a', 'reload_pending'),
                            ('b', 'reload_pending'), ('a', 'hero_dead'), ('b', 'hero_dead'),
                            ('b', 'running'), ('b', 'hidden'), ('a', 'peace'), ('b', 'peace'),
                            ('b', 'invuln_until'), ('b', 'immune'), ('b', 'map_id'), ('b', 'visibility')]:
            with self.subTest(side=side, field=field):
                self.reset_pair(); w = getattr(self, side)
                if field == 'hidden': w.gizli.return_value = True
                elif field == 'peace': w.in_pvp_peace.return_value = True
                elif field == 'immune': w.hero_etki.invulnerable.return_value = True
                elif field == 'visibility': self.a.oyuncular.clear()
                else: setattr(w, field, False if field == 'running' else 101 if field == 'invuln_until' else '5' if field == 'map_id' else True)
                self.assertTrue(PVP.attack_error(self.a, self.b, 100))

    def test_laser_uses_pvp_damage_path_and_actual_shield_leech(self):
        self.a.side_laser.side_effect = lambda now, uid, pos, hit, pvp: hit(300, 500)
        PVP.laser(self.a, self.b, 100)
        self.assertTrue(self.a.side_laser.call_args.kwargs['pvp'])
        self.assertEqual(self.b.p.d['gemi']['hitPoints'], 9700)
        self.assertEqual(self.a.p.d['gemi']['shield'], 200)  # only 100 shield actually existed
        self.assertEqual(self.b.hurt_hero.call_args.kwargs['source_player'], self.a)
        self.assertTrue(self.b.sent)

    def test_incoming_spectrum_laser_reduction_applies_to_normal_and_shield_components(self):
        self.b.p.bonuses={'alinan_lazer': -.8}
        self.b.p.d['gemi']['shield']=1000
        self.a.side_laser.side_effect=lambda now,uid,pos,hit,pvp:hit(1000,500)
        PVP.laser(self.a,self.b,100)
        self.assertEqual(self.b.p.d['gemi']['hitPoints'],9800)
        self.assertEqual(self.b.p.d['gemi']['shield'],900)

    def test_laser_stops_without_spending_ammo_if_target_becomes_friendly(self):
        self.a.grup_uyesi.return_value = True
        PVP.laser(self.a, self.b, 100)
        self.a.laser_stop.assert_called_once()
        self.a.side_laser.assert_not_called()

    @patch('oyuncu_savas.random.uniform', return_value=1)
    @patch('oyuncu_savas.random.random', return_value=0)
    def test_normal_rocket_spends_ammo_and_delayed_hit_excludes_npc_bonus(self, *unused):
        self.a.p.bonuses = {'npc': 20}
        self.assertTrue(PVP.rocket(self.a, self.b, 100))
        self.assertEqual(self.a.p.inventory[self.a.p.d['secili']['roket']], 9)
        self.assertGreater(self.a.rocket_ready, 100)
        self.b.hurt_hero.assert_not_called()
        with patch.object(PVP.time, 'time', return_value=101):
            self.a.timers[0][1]()
        self.assertEqual(self.b.hurt_hero.call_args.args[0], 1000)
        self.assertEqual(self.b.hurt_hero.call_args.kwargs['atype'], 0)

    def test_rocket_cannot_launch_through_dmz_or_cooldown(self):
        for mode in ['peace', 'cooldown']:
            self.reset_pair()
            if mode == 'peace': self.b.in_pvp_peace.return_value = True
            else: self.a.rocket_ready = 150
            self.assertTrue(PVP.rocket(self.a, self.b, 100))
            self.assertEqual(self.a.p.inventory[self.a.p.d['secili']['roket']], 10)
            self.assertEqual(self.a.timers, [])

    def test_rocket_range_and_unavailable_ammo_do_not_spend_or_schedule(self):
        for mode in ['range', 'ammo']:
            self.reset_pair()
            if mode == 'range': self.b.hero_pos.return_value = (100000, 100000)
            else: self.a.p.inventory.clear()
            PVP.rocket(self.a, self.b, 100)
            self.assertEqual(self.a.timers, [])
            self.b.hurt_hero.assert_not_called()

    @patch('oyuncu_savas.random.random', return_value=0)
    def test_rocket_revalidates_protection_at_impact(self, *unused):
        PVP.rocket(self.a, self.b, 100)
        self.b.in_pvp_peace.return_value = True
        with patch.object(PVP.time, 'time', return_value=101): self.a.timers[0][1]()
        self.b.hurt_hero.assert_not_called()

    def test_special_rocket_is_explicitly_rejected_without_consumption(self):
        self.a.p.d['secili']['roket'] = 'ammunition_specialammo_emp-01'
        PVP.rocket(self.a, self.b, 100)
        self.assertEqual(self.a.timers, [])
        self.assertTrue(any(name == 'MessageCommand' for name, fields in self.a.sent))


if __name__ == '__main__': unittest.main()
