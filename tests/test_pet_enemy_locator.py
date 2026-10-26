"""P.E.T. enemy locator (G-EL): the arrow points at the alien, and is dimmed with (-1, -1) when there is none."""
import sys
import tempfile
import time
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'server'))
import dunya
import pet
from profil import Profil

STREUNER = 2


def npc(x, y, kimlik=STREUNER, alive=True):
    return SimpleNamespace(alive=alive, d={'npc_kimlik': kimlik}, mover=dunya.Mover(x, y))


class PetEnemyLocator(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.p = Profil(path=str(Path(self.tmp.name) / 'pilot.json'))
        self.sent = []
        self.w = dunya.World(self.p, self.sent.extend, lambda text: None, 1)
        self.w.hero = dunya.Mover(1000, 1000)
        self.p.d['pet'] = pet.new_pet(self.p)
        self.pet = pet.Pet(self.p, lambda text: None)
        self.w.pet = self.pet
        self.pet.attach(self.w)
        self.pet.launch()
        self.pet.d['disli'] = pet.ENEMY_LOCATOR
        self.pet.next_locate = time.time() + 100          # target list refresh is not under test
        rng = patch.object(pet.Pet, 'gear_range', return_value=5000)
        rng.start()
        self.addCleanup(rng.stop)
        self.w.npcs.clear()

    def updates(self):
        self.sent.clear()
        self.pet.each_second(time.time())
        return [(f['x'], f['y']) for name, f in self.sent if name == 'PetGearLocatorUpdate']

    def test_points_at_nearest_alien_in_range(self):
        self.pet.locate[pet.ENEMY_LOCATOR] = STREUNER
        self.w.npcs.update({1: npc(3000, 1000), 2: npc(1500, 1200), 3: npc(1100, 1100, kimlik=99)})
        self.assertEqual(self.updates(), [(1500, 1200)])

    def test_no_alien_on_map_dims_arrow(self):
        self.pet.locate[pet.ENEMY_LOCATOR] = STREUNER
        self.w.npcs.update({1: npc(1100, 1100, kimlik=99), 2: npc(1200, 1000, alive=False)})
        self.assertEqual(self.updates(), [(-1, -1)])

    def test_alien_out_of_range_dims_arrow(self):
        self.pet.locate[pet.ENEMY_LOCATOR] = STREUNER
        self.w.npcs[1] = npc(9000, 1000)
        self.assertEqual(self.updates(), [(-1, -1)])

    def test_no_target_chosen_dims_arrow(self):
        self.w.npcs[1] = npc(1500, 1000)
        self.assertEqual(self.updates(), [(-1, -1)])

    def test_target_killed_dims_arrow_instead_of_freezing(self):
        self.pet.locate[pet.ENEMY_LOCATOR] = STREUNER
        self.w.npcs[1] = npc(1500, 1000)
        self.assertEqual(self.updates(), [(1500, 1000)])
        self.w.npcs[1].alive = False
        self.assertEqual(self.updates(), [(-1, -1)])

    def test_other_gears_send_nothing(self):
        self.pet.d['disli'] = pet.GUARD
        self.assertEqual(self.updates(), [])

    def test_no_target_round_trips_as_minus_one(self):
        import protocol
        payload = protocol.encode_message('PetGearLocatorUpdate', dict(x=-1, y=-1))
        _, name, fields, left, err = protocol.decode_message(payload)
        self.assertEqual((name, fields.get('x'), fields.get('y'), left, err), ('PetGearLocatorUpdate', -1, -1, 0, None))


if __name__ == '__main__':
    unittest.main()
