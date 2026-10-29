"""The panel's character editor (server/panel/kayit_editoru.py through kayitlar.Kayitlar).

Edits go to a draft (duzenleme.json) through the game's own hangar and reward code; Save backs the profile up and writes the draft,
Discard drops it. A save that is in the game is read-only, and a draft goes stale once the profile changes underneath it.
"""
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
import time
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'server'))
sys.path.insert(0, str(ROOT / 'server' / 'panel'))
import kayitlar as KAY  # noqa: E402


class Cfg(dict):
    def update(self, d):
        super().update(d)


class SaveEditorTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.mkdtemp(prefix='oo_editor_')
        cls.k = KAY.Kayitlar(Cfg(yedek_sayisi=5), root=os.path.join(cls.tmp, 'kayitlar'), trash=os.path.join(cls.tmp, 'silinenler'),
                             legacy=os.path.join(cls.tmp, 'profil.json'))
        cls.base = cls.k.create('Editor', 'EditorPilot', 2, kredi=1000)
        with open(cls.k.profile(cls.base), encoding='utf8') as fh:
            cls.seed = fh.read()

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def setUp(self):
        self.k.in_use = lambda slot: False
        self.k.editor_discard(self.base)
        with open(self.k.profile(self.base), 'w', encoding='utf8', newline='\n') as fh:
            fh.write(self.seed)

    def profile(self):
        with open(self.k.profile(self.base), encoding='utf8') as fh:
            return json.load(fh)

    def test_open_without_changes_makes_no_draft(self):
        v = self.k.editor_open(self.base)
        self.assertNotIn('fark', v)
        self.assertFalse(v['salt_okunur'])
        self.assertFalse(os.path.exists(self.k.draft(self.base)))
        self.assertEqual(v['pilot']['kredi'], 1000)
        self.assertTrue(any(g['aktif'] for g in v['gemiler']))

    def test_edits_stay_in_the_draft_until_saved(self):
        v = self.k.editor_apply(self.base, [{'islem': 'pilot', 'kredi': 5555, 'seviye': 10},
                                            {'islem': 'ver', 'esyalar': [['ship_goliath', 1], ['equipment_weapon_laser_lf-3', 2]]},
                                            {'islem': 'cephane', 'adetler': {'ammunition_laser_ucb-100': 777}}])
        self.assertEqual(v['pilot']['kredi'], 5555)
        self.assertEqual(v['pilot']['seviye'], 10)
        self.assertEqual(v['fark']['eklenen'].get('ship_goliath'), 1)
        self.assertEqual(next(a for a in v['fark']['adetler'] if a[0] == 'ammunition_laser_ucb-100')[2], 777)
        self.assertTrue(self.k.summary(self.base)['taslak'])
        self.assertEqual(self.profile()['pilot']['credits'], 1000)          # the save itself is untouched
        safety = self.k.editor_commit(self.base)
        self.assertTrue(safety.startswith('once_'))
        p = self.profile()
        self.assertEqual(p['pilot']['credits'], 5555)
        self.assertIn('ship_goliath', [s['lootId'] for s in p['gemiler'].values()])
        self.assertFalse(os.path.exists(self.k.draft(self.base)))
        self.assertFalse(self.k.summary(self.base)['taslak'])

    def test_equip_and_unequip_follow_the_game(self):
        v = self.k.editor_apply(self.base, [{'islem': 'ver', 'esyalar': [['equipment_weapon_laser_lf-4', 1]]}])
        ship = next(g for g in v['gemiler'] if g['aktif'])
        cfg = ship['konfigler'][ship['aktif_konfig']]['laser']['esyalar']
        lf4 = next((e for e in cfg if e['lootId'] == 'equipment_weapon_laser_lf-4'), None) or \
            next(e for e in v['envanter'] if e['lootId'] == 'equipment_weapon_laser_lf-4')
        v = self.k.editor_apply(self.base, [{'islem': 'tasi', 'yon': 'cikar', 'hedef': 'ship', 'gemi': ship['id'],
                                             'konfig': int(ship['aktif_konfig']), 'esya': lf4['id']}])
        self.assertIn(lf4['id'], [e['id'] for e in v['envanter']])
        v = self.k.editor_apply(self.base, [{'islem': 'esya_seviye', 'esya': lf4['id'], 'yukseltme': 5},
                                            {'islem': 'tasi', 'yon': 'tak', 'hedef': 'ship', 'gemi': ship['id'],
                                             'konfig': int(ship['aktif_konfig']), 'esya': lf4['id']}])
        ship = next(g for g in v['gemiler'] if g['aktif'])
        took = [e for e in ship['konfigler'][ship['aktif_konfig']]['laser']['esyalar'] if e['id'] == lf4['id']]
        self.assertEqual(took[0].get('yukseltme'), 5)
        # an equipped item can't be deleted: the operation is refused and the draft keeps its last good state
        with self.assertRaises(KAY.KayitHatasi):
            self.k.editor_apply(self.base, [{'islem': 'sil', 'esyalar': [lf4['id']]}])

    def test_grant_and_equip_into_another_ship(self):
        v = self.k.editor_apply(self.base, [{'islem': 'ver', 'esyalar': [['ship_goliath', 1]]}])
        gol = next(g for g in v['gemiler'] if g['lootId'] == 'ship_goliath')
        v = self.k.editor_apply(self.base, [{'islem': 'ver', 'esyalar': [['equipment_weapon_laser_lf-3', 20]],
                                             'tak': {'hedef': 'ship', 'gemi': gol['id'], 'konfig': 2}}])
        gol = next(g for g in v['gemiler'] if g['lootId'] == 'ship_goliath')
        lasers = gol['konfigler']['2']['laser']
        self.assertEqual(len(lasers['esyalar']), lasers['kapasite'])     # filled up to the ship's slots, the rest waits in inventory
        self.assertEqual(sum(e['lootId'] == 'equipment_weapon_laser_lf-3' for e in v['envanter']), 20 - lasers['kapasite'])
        with self.assertRaises(KAY.KayitHatasi):                      # one of each ship, as in the game
            self.k.editor_apply(self.base, [{'islem': 'ver', 'esyalar': [['ship_goliath', 1]]}])

    def test_discard_and_stale_draft(self):
        self.k.editor_apply(self.base, [{'islem': 'pilot', 'uridyum': 42}])
        self.k.editor_discard(self.base)
        self.assertNotIn('fark', self.k.editor_open(self.base))
        self.k.editor_apply(self.base, [{'islem': 'pilot', 'uridyum': 43}])
        time.sleep(0.02)
        p = self.profile()                                              # the game saved meanwhile
        p['pilot']['honourPoints'] = 9
        with open(self.k.profile(self.base), 'w', encoding='utf8', newline='\n') as fh:
            json.dump(p, fh)
        v = self.k.editor_open(self.base)
        self.assertTrue(v['atildi'])
        self.assertEqual(v['pilot']['onur'], 9)
        self.assertFalse(os.path.exists(self.k.draft(self.base)))

    def test_random_attributes_and_charges_are_editable(self):
        v = self.k.editor_apply(self.base, [{'islem': 'ver', 'esyalar': [['equipment_shipupgrade_dmg-xa01', 1], ['equipment_weapon_cannon_c-helios', 1],
                                                                         ['equipment_core_ax-10', 1], ['equipment_extra_cpu_jp-01', 1]]}])
        ids = {e['lootId']: e for e in v['envanter']}
        for g in v['gemiler']:                                          # ödül yolu boş yuvaya takmış olabilir
            for c in g['konfigler'].values():
                ids.update({e['lootId']: e for y in c.values() for e in y['esyalar']})
        mod, top, qfc = (ids[l] for l in ('equipment_shipupgrade_dmg-xa01', 'equipment_weapon_cannon_c-helios', 'equipment_core_ax-10'))
        self.assertEqual(v['havuzlar']['equipment_shipupgrade_dmg-xa01']['birim'], 'kesir')
        v = self.k.editor_apply(self.base, [
            {'islem': 'rng', 'esya': mod['id'], 'nitelik': [['damage', 0.2], ['speed', 0.05]], 'gemiler': ['ship_goliath', 'ship_sentinel'], 'hak': 2},
            {'islem': 'rng', 'esya': top['id'], 'nitelik': [['cannon_damage_thermal', 9.5]], 'yildiz': 5, 'hak': 1},
            {'islem': 'rng', 'esya': qfc['id'], 'nitelik': [['damage', 20], ['hitchance_laser', 5]], 'gemi': 'ship_sentinel', 'seviye': 12},
            {'islem': 'cpu_hak', 'lootId': 'equipment_extra_cpu_jp-01', 'hak': 99}])
        p = json.load(open(self.k.draft(self.base), encoding='utf8'))
        self.assertEqual(p['kararsiz'][str(mod['id'])]['nitelik'], [['damage', 0.2], ['speed', 0.05]])
        self.assertEqual(p['kararsiz'][str(mod['id'])]['gemiler'], ['ship_goliath', 'ship_sentinel'])
        self.assertEqual((p['parcacik'][str(top['id'])]['yildiz'], p['parcacik'][str(top['id'])]['hak']), (5, 1))
        self.assertEqual((p['qfc'][str(qfc['id'])]['gemi'], p['qfc'][str(qfc['id'])]['seviye']), ('ship_sentinel', 12))
        self.assertEqual(v['haklar']['equipment_extra_cpu_jp-01'][0], 99)
        self.assertIn('equipment_shipupgrade_dmg-xa01', v['fark']['eklenen'])      # taslakta yeni: eklenenlerde sayılır
        with self.assertRaises(KAY.KayitHatasi):                      # topun havuzunda olmayan nitelik
            self.k.editor_apply(self.base, [{'islem': 'rng', 'esya': top['id'], 'nitelik': [['damage', 5]]}])

    def test_item_info_for_tooltips(self):
        info = self.k.item_info()
        self.assertIn(['hasar', 200, 'n'], info['equipment_weapon_laser_lf-4']['dg'])
        self.assertTrue(info['equipment_weapon_laser_lf-4']['up'])
        self.assertIn('ship_cyborg', info['equipment_shipupgrade_dmg-cht01']['gm'])
        self.assertIn(['hitpoints', 0.1], info['booster_hp-b01']['m'])
        self.assertEqual(info['ship_sentinel']['yv']['lasers'], 15)

    def test_save_in_the_game_is_read_only(self):
        self.k.in_use = lambda slot: True
        v = self.k.editor_open(self.base)
        self.assertTrue(v['salt_okunur'])
        with self.assertRaises(KAY.KayitHatasi):
            self.k.editor_apply(self.base, [{'islem': 'pilot', 'kredi': 1}])


if __name__ == '__main__':
    unittest.main()
