"""Shortcut laser activation follows the same target validation as map attacks."""
import unittest
from types import SimpleNamespace
from unittest.mock import patch
import test_cbs_combat as base

cbs, dunya = base.cbs, base.dunya


class ShortcutTargetCombat(unittest.TestCase):
    setUp = base.CbsCombat.setUp

    def rival(self):
        self.a.update(sahip='rakip')
        self.a['yuvalar'] = {slot: dict(self.c.module(row['iid']))
                            for slot, row in self.a['yuvalar'].items()}
        self.a['deflector']['acik'] = False
        return cbs.asset_id(2, 2)

    def test_selected_enemy_station_starts_from_laser_shortcut(self):
        uid = self.rival()
        self.w.select({'targetId': uid})
        ammo = self.p.d['secili']['lazer']
        self.p.d['ayarlar'].setdefault('gameplaySettingsModule', {})['quickslotStopAttack'] = True
        with patch.object(self.p, 'ammo', return_value=1000):
            self.w.menu_action(dict(menuItemId=ammo, actionType=1, sourceType=1))
        self.assertEqual(self.w.target, uid)
        self.assertTrue(self.w.attacking)
        self.assertTrue(any(n == 'UIItemAddHighlightCommand' for n, f in self.sent))

    def test_shortcut_preserves_friendly_and_deflector_attack_denials(self):
        uid = cbs.asset_id(2, 2)
        self.w.select({'targetId': uid})
        self.w.quickslot_start()
        self.assertFalse(self.w.attacking)
        self.assertTrue(any('msg_station_not_atackable' in str(f) for n, f in self.sent))
        self.sent.clear()
        uid = self.rival()
        self.a['deflector']['acik'] = True
        self.w.select({'targetId': uid})
        self.w.quickslot_start()
        self.assertFalse(self.w.attacking)
        self.assertTrue(any('msg_station_not_atackable' in str(f) for n, f in self.sent))

    def test_shortcut_ignores_missing_dead_cross_map_assets_and_dead_hero(self):
        uid = self.rival()
        for target in (None, -1, cbs.asset_id(3, 2)):
            self.w.target = target
            self.w.quickslot_start()
            self.assertFalse(self.w.attacking)
        self.a['yuvalar']['2']['can'] = 0
        self.w.target = uid
        self.w.quickslot_start()
        self.assertFalse(self.w.attacking)
        self.a['yuvalar']['2']['can'] = 10000
        self.w.hero_dead = True
        self.w.quickslot_start()
        self.assertFalse(self.w.attacking)

    def test_shortcut_starts_for_own_pet_and_reuses_pvp_denial(self):
        self.w.pet = SimpleNamespace(owned=True, active=True, pid=170000001)
        self.w.target = self.w.pet.pid
        self.w.quickslot_start()
        self.assertTrue(self.w.attacking)
        self.w.attacking = False
        other = SimpleNamespace(hid=100000002)
        self.w.target = other.hid
        denied = [('LegacyModule', {'message': 'blocked'})]
        with patch.object(self.w, 'oyuncu', return_value=other), patch.object(dunya.PVP, 'attack_error', return_value=denied) as check:
            self.w.quickslot_start()
            check.assert_called_once()
        self.assertFalse(self.w.attacking)
        self.assertIn(denied[0], self.sent)
        with patch.object(self.w, 'oyuncu', return_value=other), patch.object(dunya.PVP, 'attack_error', return_value=[]) as check:
            self.w.quickslot_start()
            check.assert_called_once()
        self.assertTrue(self.w.attacking)

    def test_shortcut_keeps_normal_npc_start(self):
        tip = next(t for t, d in dunya.CFG['tipler'].items() if not d.get('dost'))
        npc = dunya.NPC(91001, tip, self.x, self.y)
        self.w.npcs[npc.id] = npc
        self.w.select({'targetId': npc.id})
        self.w.quickslot_start()
        self.assertTrue(self.w.attacking)
        self.assertEqual(self.w.target, npc.id)


if __name__ == '__main__':
    unittest.main()
