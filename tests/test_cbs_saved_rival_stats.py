"""Only synthetic rival capacities migrate; preserve combat progress and ownership."""
import copy, sys, tempfile, unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'server'))
import cbs
from profil import Profil

class SavedRivalStats(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.p=Profil(path=str(Path(self.tmp.name)/'pilot.json'))
        legacy=dict(loot='module_ltm-lr',seviye=0,azami=208000,can=52000,kalkan=83200)
        self.state={'moduller':{'owned':dict(legacy)},'asteroitler':{
            '2':dict(durum='kurulu',sahip='rakip',yuvalar={'2':dict(legacy),'3':dict(legacy,can=0,kalkan=0)}),
            '3':dict(durum='kurulu',sahip='oyuncu',yuvalar={'2':dict(legacy)})}}
        self.p.d['cbs']=copy.deepcopy(self.state)
        self.c=cbs.Cbs(self.p,None,lambda _:None)

    def test_existing_rival_capacity_rescales_hp_and_shield_fractions(self):
        slots=self.c.st['asteroitler']['2']['yuvalar']
        self.assertEqual((slots['2']['azami'],slots['2']['can'],slots['2']['kalkan']),(1560000,390000,624000))
        self.assertEqual((slots['3']['azami'],slots['3']['can'],slots['3']['kalkan']),(1560000,0,0))
        self.assertTrue(self.p.dirty)

    def test_migration_is_once_and_preserves_owned_data_and_other_profile_state(self):
        before=copy.deepcopy({k:v for k,v in self.p.d.items() if k!='cbs'})
        state=self.c.st
        state['asteroitler']['2']['yuvalar']['2']['can']=123
        self.assertEqual(self.c.st['asteroitler']['2']['yuvalar']['2']['can'],123)
        self.assertEqual(state['moduller'],self.state['moduller'])
        self.assertEqual(state['asteroitler']['3'],self.state['asteroitler']['3'])
        self.assertEqual({k:v for k,v in self.p.d.items() if k!='cbs'},before)
        self.assertEqual(state.get('rakip_istatistik_surumu'),1)

    def test_malformed_unknown_or_uninstalled_rival_rows_are_skipped_and_overflow_clamped(self):
        slots=self.p.d['cbs']['asteroitler']['2']['yuvalar']
        slots.update({'4':dict(slots['2'],loot='unknown'),'5':dict(slots['2'],azami=0),
                      '6':dict(slots['2'],iid=157500000),'7':dict(slots['2'],can=float('nan')),
                      '8':dict(slots['2'],can=999999,kalkan=999999),'9':dict(slots['2'],loot=['invalid'])})
        skipped=copy.deepcopy({k:slots[k] for k in ['4','5','6']})
        out=self.c.st['asteroitler']['2']['yuvalar']
        self.assertEqual({k:out[k] for k in skipped},skipped)
        self.assertEqual(out['7']['azami'],208000)
        self.assertEqual(out['9']['loot'],['invalid'])
        self.assertEqual((out['8']['can'],out['8']['kalkan']),(1560000,1248000))

    def test_shared_host_station_storage_is_migrated(self):
        host=Profil(path=str(Path(self.tmp.name)/'host.json'))
        host.d['cbs']=copy.deepcopy(self.state);host.d['cbs']['ortak']=True
        with patch.object(cbs,'ortak',return_value=host):
            self.assertEqual(self.c.asts['2']['yuvalar']['2']['azami'],1560000)
        self.assertEqual(self.p.d['cbs']['asteroitler']['2']['yuvalar']['2']['azami'],208000)
        self.assertEqual(host.d['cbs'].get('rakip_istatistik_surumu'),1)
