"""CBS hits preserve attack facing and report actual hull/shield damage."""
import unittest
from unittest.mock import patch
import test_cbs_combat as base
cbs, dunya = base.cbs, base.dunya

class CbsDamageFeedback(unittest.TestCase):
    setUp = base.CbsCombat.setUp

    def rival(self):
        self.a['sahip'] = 'rakip'
        self.a['yuvalar'] = {s: dict(self.c.module(y['iid'])) for s,y in self.a['yuvalar'].items()}
        self.a['deflector']['acik'] = False
        return cbs.asset_id(2,2), self.a['yuvalar']['2']

    def test_laser_damage_reports_actual_amount_without_reselecting_asset(self):
        uid,m = self.rival()
        self.w.select({'targetId':uid})
        self.sent.clear()
        self.w.hit_asset(uid,1000,1)
        self.assertEqual((m['can'],m['kalkan']),(9800,4200))
        hit=next(f for n,f in self.sent if n=='AttackHitCommand')
        self.assertEqual((hit['attackerId'],hit['victimId'],hit['damage']),(self.w.hid,uid,1000))
        self.assertEqual((hit['victimHitpoints'],hit['victimShield']),(9800,4200))
        self.assertEqual(hit['attackType']['attackTypeValue'],1)
        self.assertFalse(any(n=='AssetInfoCommand' for n,f in self.sent))
        self.assertTrue(any(n=='AttackHitAssetCommand' for n,f in self.sent))

    def test_shield_only_hit_is_capped_and_does_not_damage_hull(self):
        uid,m = self.rival()
        self.w.hit_asset(uid,10000,0,shield_only=True)
        self.assertEqual((m['can'],m['kalkan']),(10000,0))
        self.assertEqual(self.w.last_shield_hit,5000)
        self.assertEqual(next(f['damage'] for n,f in self.sent if n=='AttackHitCommand'),5000)

    def test_hull_only_and_overkill_feedback_use_actual_removed_health(self):
        uid,m = self.rival()
        with patch.object(self.c,'module_destroyed',return_value=[]):
            self.w.hit_asset(uid,20000,0,hull_only=True)
        self.assertEqual((m['can'],m['kalkan']),(0,5000))
        self.assertEqual(self.w.last_shield_hit,0)
        self.assertEqual(next(f['damage'] for n,f in self.sent if n=='AttackHitCommand'),10000)

    def test_blocked_stale_and_dead_hero_impacts_do_not_damage_or_show_hit(self):
        uid,m = self.rival()
        for mode in ('shield','friendly','dead','jump','stale'):
            with self.subTest(mode=mode):
                self.a['deflector']['acik']=mode=='shield'
                self.a['sahip']='oyuncu' if mode=='friendly' else 'rakip'
                self.w.hero_dead=mode=='dead';self.w.jumping=mode=='jump'
                self.sent.clear()
                self.w.last_shield_hit=999
                self.w.hit_asset(-1 if mode=='stale' else uid,1000,0)
                self.assertEqual((m['can'],m['kalkan']),(10000,5000))
                self.assertEqual(self.w.last_shield_hit,0)
                self.assertFalse(any(n=='AttackHitCommand' for n,f in self.sent))

if __name__=='__main__': unittest.main()
