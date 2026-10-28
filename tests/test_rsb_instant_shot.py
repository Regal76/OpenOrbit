"""RSB-75/RCB-140 fire as soon as they are selected during an attack, without breaking the normal fire rate."""
import sys, tempfile, time, unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'server'))
import dunya
from profil import Profil

RSB, RCB, OLD = 'ammunition_laser_rsb-75', 'ammunition_laser_rcb-140', 'ammunition_laser_lcb-10'


class InstantSlowAmmoShot(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.p = Profil(path=str(Path(tmp.name) / 'pilot.json'))
        self.p.d['ekipman']['laser'] = ['equipment_weapon_laser_lf-3']
        self.p.d['dron_ekipman'] = []
        self.sent = []
        self.w = dunya.World(self.p, self.sent.extend, lambda *_: None, 1)
        self.w.hero = dunya.Mover(1000, 1000)
        self.npc = dunya.NPC(91001, '46', 1100, 1000)
        self.w.npcs[self.npc.id] = self.npc
        for ammo in (OLD, RSB, RCB):
            self.p.d['cephane'][ammo] = 100
        self.p.d['secili']['lazer'] = OLD
        self.w.target = self.npc.id
        miss = patch.object(dunya.random, 'random', return_value=1)    # every shot misses: no damage side effects
        miss.start()
        self.addCleanup(miss.stop)

    def shots(self):
        return [m for m in self.sent if m[0] == 'AttackLaserRunCommand' and m[1]['attackerId'] == self.w.hid]   # the NPC fires back too

    def select(self, ammo, act=1):
        self.w.menu_action(dict(menuItemId=ammo, actionType=act, sourceType=1))

    def attack_after_normal_shot(self):
        """Attacking, a normal salvo has just gone out: the next tick is almost a full interval away."""
        self.w.attacking = True
        self.w.next_laser = time.time() + dunya.SAVAS['lazer_aralik_sn'] - 0.05

    def test_selection_during_attack_fires_at_once(self):
        for act in (1, 0):                      # quickslot press and item-bar click
            for ammo in (RSB, RCB):
                with self.subTest(ammo=ammo, act=act):
                    self.p.d['secili']['lazer'] = OLD
                    self.w.ammo_ready.clear()
                    self.attack_after_normal_shot()
                    self.sent.clear()
                    before = self.p.ammo(ammo)
                    t = time.time()
                    self.select(ammo, act)
                    self.assertEqual(len(self.shots()), 1)
                    self.assertEqual(self.p.ammo(ammo), before - 1)
                    self.assertEqual(self.p.d['secili']['lazer'], ammo)      # stays selected (original game)
                    timers = [m for m in self.sent if m[0] == 'MenuItemCooldownGroupTimerCommand']
                    self.assertEqual(timers[0][1]['cooldownType']['typeValue'], 10)
                    # the next normal salvo waits a full interval from the instant shot
                    self.assertGreaterEqual(self.w.next_laser, t + dunya.SAVAS['lazer_aralik_sn'] - 0.01)

    def test_no_extra_shot_before_next_interval(self):
        self.attack_after_normal_shot()
        self.select(RSB)
        self.sent.clear()
        now = time.time()
        self.w.step(now + 0.2)                   # before the next pulse volley: no salvo
        self.assertEqual(self.shots(), [])
        self.select(RSB)                         # RSB is cooling down: selecting it again does not fire
        self.assertEqual(self.shots(), [])

    def test_cooling_ammo_waits_for_the_tick(self):
        self.attack_after_normal_shot()
        self.w.ammo_ready[RSB] = time.time() + 2
        self.sent.clear()
        self.select(RSB)
        self.assertEqual(self.shots(), [])
        self.assertEqual(self.p.d['secili']['lazer'], RSB)
        self.assertEqual(self.p.ammo(RSB), 100)

    def test_no_shot_without_attack(self):
        with patch.object(self.w, 'quickslot_on', return_value=False):
            self.select(RSB)
        self.assertEqual(self.shots(), [])
        self.assertFalse(self.w.attacking)
        self.assertEqual(self.p.d['secili']['lazer'], RSB)

    def test_quickslot_press_starts_attack_and_fires(self):
        with patch.object(self.w, 'quickslot_on', return_value=True):
            self.select(RSB)
        self.assertTrue(self.w.attacking)
        self.assertEqual(len(self.shots()), 1)
        self.assertEqual(self.p.d['secili']['lazer'], RSB)


if __name__ == '__main__':
    unittest.main()
