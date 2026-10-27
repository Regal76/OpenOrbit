"""P.E.T. Cargo Trader (G-TRA): unlimited sales while the trade window is open; closing it hides the P.E.T., selects Passive
mode and starts the cooldown with the "Trade buff" icon (client game.xml petBuffs 3), locking the P.E.T. window."""
import sys
import tempfile
import time
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'server'))
import dunya
import pet
from profil import Profil


class CargoTrader(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.p = Profil(path=str(Path(tmp.name) / 'pilot.json'))
        self.sent = []
        self.w = dunya.World(self.p, self.sent.extend, lambda text: None, 1)
        self.w.hero = dunya.Mover(1000, 1000)
        self.p.d['pet'] = pet.new_pet(self.p)
        self.pet = pet.Pet(self.p, lambda text: None)
        self.w.pet = self.pet
        self.pet.attach(self.w)
        self.pet.launch()
        self.pet.d['yakit'] = 100000
        self.pet.gear = lambda t, *a: {'bekleme_sn': 300, 'ticaret_yakit': 50} if t == pet.TRADE_POD else {}
        self.pet.gear_list = lambda: [(pet.PASSIVE, 1, True), (pet.GUARD, 1, True), (pet.TRADE_POD, 1, True)]
        self.pet.select(pet.TRADE_POD)

    def names(self):
        return [m[0] for m in self.sent]

    def test_fuel_is_paid_once_per_session(self):
        before = self.pet.d['yakit']
        self.pet.trade_charge()
        self.pet.trade_charge()
        self.assertEqual(before - self.pet.d['yakit'], 50)
        self.assertTrue(self.pet.trading)

    def test_closing_the_window_hides_pet_selects_passive_and_starts_cooldown(self):
        self.sent.clear()
        now = time.time()
        self.pet.trade_close(now)
        self.assertFalse(self.pet.active)
        self.assertEqual(self.pet.d['disli'], pet.PASSIVE)
        buff = next(f for n, f in self.sent if n == 'PetBuffCommand')
        self.assertEqual((buff['effectAction'], buff['effectId'], buff['addingParameters']), (0, 3, [300]))
        self.assertIn(('PetBlockUICommand', dict(blocked=True, blockAll=True)), self.sent)
        self.pet.launch()
        self.assertFalse(self.pet.active)                     # locked until the cooldown ends

    def test_selecting_another_gear_ends_the_session(self):
        self.pet.select(pet.GUARD)
        self.assertFalse(self.pet.active)
        self.assertTrue(self.pet.trade_wait)
        self.assertEqual(self.pet.d['disli'], pet.PASSIVE)

    def test_cooldown_end_unlocks_the_window(self):
        self.pet.trade_close(time.time() - 301)
        self.sent.clear()
        self.pet.tick(time.time())
        self.assertIn(('PetBlockUICommand', dict(blocked=False, blockAll=False)), self.sent)
        self.assertTrue(any(n == 'PetBuffCommand' and f['effectAction'] == 1 for n, f in self.sent))
        self.pet.launch()
        self.assertTrue(self.pet.active)
