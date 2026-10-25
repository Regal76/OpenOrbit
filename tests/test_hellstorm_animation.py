"""Hellstorm packets must match the native reader and every ammo visual lookup.

The independent wire decoder below follows HellstormAttackCommand.read in the
1.1.115 client (0x11677e10); it does not round-trip through protocol.py's decoder.
Optional native coverage executes the client's GetRocketType switch under Unicorn.
"""
import hashlib
import os
from pathlib import Path
import struct
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'server'))
import protocol
import savas_esya as SE

if os.environ.get('HELLSTORM_UNICORN_PATH'):
    sys.path.insert(0, os.environ['HELLSTORM_UNICORN_PATH'])
try:
    from unicorn import Uc, UC_ARCH_X86, UC_MODE_32, UC_HOOK_CODE
    from unicorn.x86_const import UC_X86_REG_EAX, UC_X86_REG_EIP, UC_X86_REG_ESP
except ImportError:
    Uc = None


def native_wire_fields(packet):
    command, attacker, target, hit, count, module, ammo_type = struct.unpack('>HIIBIHh', packet)
    return dict(command=command,
                attacker=((attacker << 2) | (attacker >> 30)) & 0xffffffff,
                target=((target << 16) | (target >> 16)) & 0xffffffff,
                hit=bool(hit), count=((count >> 1) | (count << 31)) & 0xffffffff,
                module=module, ammo_type=ammo_type)


class HellstormAnimation(unittest.TestCase):
    def test_every_launcher_ammo_serializes_complete_native_fields(self):
        self.assertEqual(len(SE.LAUNCHER_AMMO), 9)
        for ammo, cfg in SE.LAUNCHER_AMMO.items():
            for count in (1, 3, 5, 6, 7):
                for hit in (False, True):
                    with self.subTest(ammo=ammo, count=count, hit=hit):
                        name, fields = ('HellstormAttackCommand', dict(
                            attackerId=0x1234567, targetId=0x7654321, hit=hit,
                            currentLoad=count, rocketType=SE.mod('AmmunitionTypeModule', typeValue=cfg['tur'])))
                        actual = native_wire_fields(protocol.encode_message(name, fields))
                        self.assertEqual(actual, dict(command=287, attacker=0x1234567, target=0x7654321,
                                                      hit=hit, count=count,
                                                      module=protocol.spec().id_of('AmmunitionTypeModule'),
                                                      ammo_type=cfg['tur']))

    def test_native_salvo_keeps_full_load_for_curved_trajectories(self):
        capacities = {cfg['kapasite'] for cfg in SE.LAUNCHERS.values()}
        for cfg in SE.LAUNCHER_AMMO.values():
            for count in capacities | {1, 7}:  # Ouroboros + Tartarus Plus bonus rocket
                with self.subTest(ammo=cfg['tur'], count=count):
                    # Native count > 1 selects PlayTweenCurve; count=1 selects PlayTweenLine.
                    name, fields = SE.salvo(123, 456, True, count, cfg['tur'])
                    decoded = native_wire_fields(protocol.encode_message(name, fields))
                    self.assertEqual((decoded['count'], decoded['ammo_type']), (count, cfg['tur']))

    def test_damage_waits_for_last_native_curved_projectile(self):
        for distance in (0, 300, 500, 650):
            for count in (1, 3, 5, 6, 7):
                with self.subTest(distance=distance, count=count):
                    expected = max(1.0, distance / 500.0)
                    if count > 1:
                        expected += 0.3 + (count - 1) * 0.5 / count
                    self.assertAlmostEqual(SE.salvo_time(distance, count), expected)

    def test_player_launcher_fires_one_full_salvo_and_waits_for_impact(self):
        from profil import Profil
        from dunya import World
        with tempfile.TemporaryDirectory() as directory:
            p = Profil(path=str(Path(directory) / 'profile.json'))
            sent, delayed = [], []
            w = World(p, sent.extend, lambda *args: None, '1')
            p.d['ekipman']['rocket'] = ['equipment_weapon_rocketlauncher_hst-2']
            target = SimpleNamespace(id=42, alive=True, mover=SimpleNamespace(pos=lambda now: (650, 0)))
            w.npcs = {42: target}
            w.target = 42
            with patch.object(w, 'hero_pos', return_value=(0, 0)), \
                 patch.object(w, 'later', side_effect=lambda delay, callback: delayed.append((delay, callback))), \
                 patch.object(w, 'end_invuln'), patch.object(w, 'stop_repair'), \
                 patch.object(w.abilities, 'reveal'), patch.object(w.items, 'reveal'), \
                 patch.object(w.items, 'status', return_value=[]), patch.object(p, 'ship_row', return_value={}), \
                 patch('savas_esya.random.random', return_value=0.5), patch.object(w, 'hit_npc') as hit:
                for ammo, cfg in SE.LAUNCHER_AMMO.items():
                    with self.subTest(ammo=ammo):
                        sent.clear()
                        delayed.clear()
                        p.d['fircatici_dolu'] = [ammo, 5]
                        w.items.launcher_fire(100)
                        salvos = [fields for name, fields in sent if name == 'HellstormAttackCommand']
                        self.assertEqual(len(salvos), 1)
                        self.assertEqual(salvos[0]['currentLoad'], 5)
                        self.assertEqual(salvos[0]['rocketType']['typeValue'], cfg['tur'])
                        self.assertEqual(p.d['fircatici_dolu'], [ammo, 0])
                        self.assertEqual(len(delayed), 1)
                        self.assertAlmostEqual(delayed[0][0], 2.0)  # 650/500 + 0.3 + 4*0.5/5
                        hit.assert_not_called()


@unittest.skipUnless(Uc is not None and os.environ.get('HELLSTORM_NATIVE_DLL'),
                     'Set HELLSTORM_NATIVE_DLL and provide Unicorn for exact native lookup coverage')
class NativeHellstormAmmoLookup(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        sys.path.insert(0, str(ROOT / 'tools/il2cpp'))
        from pe import PE
        cls.pe = PE(os.environ['HELLSTORM_NATIVE_DLL'])

    def native_lookup(self, ammo_type):
        """Execute native switch; stub only Int32.ToString and metadata initialization."""
        u = Uc(UC_ARCH_X86, UC_MODE_32)
        entry = 0x10f11370
        for base in (0x10f11000, 0x134fd000, 0x12218000, 0x20000000):
            u.mem_map(base, 0x1000)
        off = self.pe.va2off(entry)
        # Guard the fixture identity for this exact native method, not a cached disassembly.
        code = self.pe.b[off:off + 0xd0]
        self.assertEqual(hashlib.sha256(code).hexdigest(),
                         '5f55d469a772b8f80fd76ea5c3bac231a44d467cf530e0932f802ea969ff1da6')
        u.mem_write(entry, code)
        u.mem_write(0x134fd554, b'\x01')
        stack, stop = 0x20000800, 0x20000010
        u.mem_write(stack, struct.pack('<IIII', stop, 0, ammo_type, 0))
        u.reg_write(UC_X86_REG_ESP, stack)
        def intercept(machine, address, size, _):
            if address == 0x12218390:  # Int32.ToString: retain numeric value instead of allocating a string
                esp = machine.reg_read(UC_X86_REG_ESP)
                ret, value_ptr = struct.unpack('<II', machine.mem_read(esp, 8))
                value = struct.unpack('<I', machine.mem_read(value_ptr, 4))[0]
                machine.reg_write(UC_X86_REG_EAX, value)
                machine.reg_write(UC_X86_REG_ESP, esp + 4)
                machine.reg_write(UC_X86_REG_EIP, ret)
        u.hook_add(UC_HOOK_CODE, intercept)
        u.emu_start(entry, stop, count=100)
        self.assertEqual(u.reg_read(UC_X86_REG_EIP), stop)
        return u.reg_read(UC_X86_REG_EAX)

    def test_flight_constants_match_the_native_scheduler_and_tween(self):
        def value(address):
            return struct.unpack_from('<f', self.pe.b, self.pe.va2off(address))[0]
        spread, speed, minimum, curve_extra = map(value, (0x12bea60c, 0x12bea68c, 0x12bea614, 0x12bea600))
        for count in (1, 3, 5, 6, 7):
            for distance in (0, 300, 650):
                flight = max(minimum, distance / speed)
                if count > 1:
                    flight += curve_extra + (count - 1) * spread / count
                self.assertAlmostEqual(SE.salvo_time(distance, count), flight, places=6)

    def test_all_nine_configured_ammo_types_reach_the_native_visual_id(self):
        for ammo, cfg in SE.LAUNCHER_AMMO.items():
            with self.subTest(ammo=ammo):
                self.assertEqual(self.native_lookup(cfg['tur']), cfg['kimlik'])


if __name__ == '__main__':
    unittest.main()
