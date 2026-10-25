"""Native .115 CBS model IDs and stage fields, tested through real server packets."""
import sys
import struct
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'server'))
import cbs
import protocol
from profil import Profil

# MapInfoComponentAwakeSystem.Awake + BattleStationConstants..cctor.
# These are separate native namespaces, not interchangeable module IDs.
MODULE_IDS = {
    'module_hulm-1': (2, 0), 'module_defm-1': (3, 0), 'module_repm-1': (4, 3),
    'module_ltm-lr': (7, 4), 'module_ltm-mr': (6, 5), 'module_ltm-hr': (5, 6),
    'module_ram-la': (9, 7), 'module_ram-ma': (8, 8), 'module_honm-1': (10, 9),
    'module_dmgm-1': (11, 10), 'module_xpm-1': (12, 11),
}


class ModuleVisualPackets(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.p = Profil(path=str(Path(self.tmp.name) / 'pilot.json'))
        self.c = cbs.Cbs(self.p, None, lambda _: None)
        self.a = self.c.ast(2)
        self.a.update(durum='kurulu', yuvalar={}, deflector={'acik': False})

    def install(self, slot, loot, level, owner='own', dead=False):
        iid = cbs.ITEM_BASE + slot
        row = dict(loot=loot, seviye=level, can=0 if dead else 1000, kalkan=0)
        if owner == 'rival':
            self.a['sahip'] = 'rakip'
            self.a['yuvalar'][str(slot)] = row
        elif owner == 'shared':
            self.a['yuvalar'][str(slot)] = dict(iid=iid, modul=row)
        else:
            self.c.st['moduller'][str(iid)] = row
            self.a['yuvalar'][str(slot)] = dict(iid=iid)
        return iid

    def test_all_eleven_families_keep_native_inventory_type_and_map_design_namespaces(self):
        self.assertEqual(set(cbs.MODS), set(MODULE_IDS))
        for loot, (inventory_type, map_design) in MODULE_IDS.items():
            with self.subTest(loot=loot):
                self.assertEqual((cbs.MODS[loot]['tur'], cbs.MODS[loot]['tasarim']), (inventory_type, map_design))
                iid = self.install(2, loot, 0)
                self.assertEqual(self.c.module_cmd(iid)['type'], inventory_type)

    def test_satellite_create_and_info_match_installed_family_at_every_native_tier_boundary(self):
        for owner in ('own', 'shared', 'rival'):
            for loot, (_, design) in MODULE_IDS.items():
                if cbs.MODS[loot]['merkez']: continue
                for level in (0, 4, 5, 9, 10, 15):
                    with self.subTest(owner=owner, loot=loot, level=level):
                        self.a.pop('sahip', None); self.a['yuvalar'] = {}
                        self.c.st['moduller'] = {}
                        self.install(2, loot, level, owner)
                        cmd = next(cmd[1] for uid, kind, cmd in self.c.map_assets(2) if uid == cbs.asset_id(2, 2))
                        info = self.c.info_cmd(2, 2)[1]
                        self.assertEqual((cmd['type']['typeValue'], cmd['designId'], cmd['expansionStage'], cmd['userName']),
                                         (37, design, level, cbs.MODS[loot]['kod']))
                        self.assertEqual((info['designId'], info['expansionStage']), (design, level))

    def test_hub_create_and_info_pack_independent_hull_high_word_and_deflector_low_byte(self):
        for owner in ('own', 'shared', 'rival'):
            for hull, deflector in ((0, 15), (15, 0), (4, 5), (5, 9), (10, 4), (15, 15)):
                with self.subTest(owner=owner, hull=hull, deflector=deflector):
                    self.a.pop('sahip', None); self.a['yuvalar'] = {}; self.c.st['moduller'] = {}
                    self.install(0, 'module_hulm-1', hull, owner)
                    self.install(1, 'module_defm-1', deflector, owner)
                    cmd = self.c.map_assets(2)[0][2][1]
                    expected = (hull << 16) | deflector
                    self.assertEqual(cmd['expansionStage'], expected)
                    # Selecting the hub calls the same native visual updater.
                    self.assertEqual(self.c.info_cmd(2, 0)[1]['expansionStage'], expected)
                    self.assertEqual(self.c.info_cmd(2, 1)[1]['expansionStage'], expected)

    def test_dead_satellite_uses_wreck_on_creation(self):
        self.install(2, 'module_ram-la', 15, dead=True)
        cmd = self.c.map_assets(2)[1][2][1]
        self.assertEqual((cmd['designId'], cmd['userName']), (0, 'wreck'))

    def test_wire_model_fields_match_native_asset_reader_rotations_and_order(self):
        # AssetCreateCommand.read .115 0x115e8280, independently of protocol_read.json.
        # Prefix: command,u32 x,UTF8 name,u8 modifiers,u32 design,bool,u16 typeID,u16 type,
        # UTF8 clanTag,u32 clanId,u32 assetId,u32 expansionStage.
        rotate = lambda v, n: ((v << n) | (v >> (32-n))) & 0xffffffff
        for design in range(3, 12):
            for stage in (0, 4, 5, 9, 10, 15, (15 << 16) | 5):
                with self.subTest(design=design, stage=stage):
                    name, fields = self.c.asset_cmd(157000202, 37, 100, 200, 'model', design, stage)
                    wire = protocol.encode_message(name, fields)
                    pos = 6
                    length, = struct.unpack_from('>H', wire, pos); pos += 2 + length
                    count = wire[pos]; pos += 1
                    self.assertEqual(count, 0)
                    raw_design, detected, type_id, kind = struct.unpack_from('>IBHH', wire, pos); pos += 9
                    length, = struct.unpack_from('>H', wire, pos); pos += 2 + length
                    clan, uid, raw_stage = struct.unpack_from('>III', wire, pos)
                    self.assertEqual((rotate(raw_design, 5), kind, rotate(raw_stage, 15)), (design, 37, stage))
                    self.assertEqual(rotate(uid, 31), 157000202)
