"""CBS integration preserves upstream map-layout protection and navigation inputs."""
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'server'))
import dunya
import harita_duzeni as HD
from profil import Profil


class UpstreamMapCbsIntegration(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.p = Profil(path=str(Path(temporary.name) / 'pilot.json'))
        self.sent = []

    def world(self, map_id):
        return dunya.World(self.p, self.sent.extend, lambda _: None, map_id)

    def test_pirate_base_safe_zone_keeps_pve_pvp_and_beacon_protection(self):
        w = self.world(92)
        w.station = None
        w.gates = []
        w.hero = dunya.Mover(10500, 6750)
        self.assertTrue(w.in_peace(10500, 6750))
        self.assertTrue(w.in_pvp_peace(10500, 6750))
        self.assertTrue(w.near_zone(10500, 6750, 0))
        w.check_gates(w.entered + 1)
        beacon = next(f for n, f in self.sent if n == 'BeaconCommand')
        self.assertTrue(beacon['inPeaceArea'])

    def test_black_light_gate_exclusion_uses_upstream_smaller_radius(self):
        w = self.world(306)
        gate = w.gates[0]
        circles = w.zone_circles()
        self.assertIn((gate['x'], gate['y'], 500), circles)
        self.assertTrue(w.path_near_zone(gate['x']-600, gate['y'], gate['x']+600, gate['y'], allow_station=True))
        self.assertFalse(w.path_near_zone(gate['x']-600, gate['y']+501, gate['x']+600, gate['y']+501, allow_station=True))

    def test_random_retry_fallback_still_excludes_upstream_map_obstacles(self):
        w = self.world(306)
        # Force random candidates into a real NO_ACCESS wall; deterministic fallback
        # must preserve the upstream wall check as well as CBS safety.
        x0, y0, x1, y1 = HD.walls(306)[0]
        x, y = (x0+x1)/2, (y0+y1)/2
        with patch.object(dunya.random, 'uniform', side_effect=[x, y]*50):
            point = w.random_spot()
        self.assertFalse(HD.blocked(306, *point, 300))
        self.assertFalse(w.near_zone(*point, 700))
