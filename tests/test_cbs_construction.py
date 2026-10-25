"""CBS construction uses the native constructing effect, not only a UI timer."""
import sys,tempfile,time,unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'server'))
import cbs
from profil import Profil

class Construction(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.p=Profil(path=str(Path(self.tmp.name)/'pilot.json'))
        self.c=cbs.Cbs(self.p,None,lambda *_:None)
        self.a=self.c.ast(2)
        self.a.update(durum='bos',yuvalar={})
        self.c.world=SimpleNamespace(map_id=cbs.AST[2]['harita'])
        self.c.shown_assets=[(cbs.asset_id(2),cbs.ASTEROID)]

    def test_map_entry_recreates_construction_effect_only_while_building(self):
        for state in ('bos','kurma','kurulu'):
            with self.subTest(state=state):
                self.a['durum']=state
                uid,kind,cmd=self.c.map_assets(2)[0]
                effects=cmd[1]['modifier']
                building=[m for m in effects if m['modifier']==37 and m['activated']]
                self.assertEqual(len(building),int(state=='kurma'))
                if state=='kurma':
                    self.assertEqual((uid,kind,cmd[1]['designId']),(cbs.asset_id(2),cbs.ASTEROID,1))
                    self.assertEqual((building[0]['userId'],building[0]['attribute']),(uid,0))

    def test_successful_build_starts_animation_on_existing_asteroid_immediately(self):
        with patch.object(self.c,'own_progress',return_value=1),patch.object(self.c,'can',return_value=True):
            msgs=self.c.build(2,5)
        self.assertEqual(self.a['durum'],'kurma')
        effects=[f for n,f in msgs if n=='VisualModifierCommand' and f['modifier']==37]
        self.assertEqual(len(effects),1)
        self.assertTrue(effects[0]['activated'])
        self.assertEqual(effects[0]['userId'],cbs.asset_id(2))
        self.assertTrue(any(n=='BattleStationBuildingStateCommand' for n,_ in msgs))

    def test_rejected_build_does_not_start_effect(self):
        with patch.object(self.c,'own_progress',return_value=0):
            msgs=self.c.build(2,5)
        self.assertEqual(self.a['durum'],'bos')
        self.assertFalse(any(n=='VisualModifierCommand' for n,_ in msgs))

    def test_finish_replaces_constructing_asteroid_with_station_and_no_build_effect(self):
        self.a.update(durum='kurma',kurma_bitis=time.time()-1,kurma_sn=300)
        msgs=self.c.finish_build(2,time.time())
        remove=[f for n,f in msgs if n=='AssetRemoveCommand']
        create=[f for n,f in msgs if n=='AssetCreateCommand']
        self.assertTrue(any(f['uid']==cbs.asset_id(2) for f in remove))
        self.assertTrue(any(f['type']['typeValue']==cbs.BATTLESTATION for f in create))
        self.assertFalse(any(m['modifier']==37 for f in create for m in f['modifier']))
