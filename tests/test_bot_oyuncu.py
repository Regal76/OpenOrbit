"""Unit tests for opt-in Bot Players (server/bot_oyuncu.py)."""
import os
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'server'))

import ayar as AY
import bot_oyuncu as BOT_P
import dunya
import protocol
from profil import Profil


class TestBotPlayers(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.p = Profil(path=str(Path(self.tmp.name) / 'pilot.json'))
        self.sent = []
        self.now = 1000.0

    def make_world(self, map_id='16'):  # Map 16 is 4-4
        return dunya.World(self.p, self.sent.extend, lambda *_: None, map_id)

    def test_bots_are_disabled_by_default(self):
        self.assertFalse(AY.get('bot_oyuncular'))
        w = self.make_world('16')
        self.assertFalse(w.can_have_bots())
        w.start()
        self.assertEqual(len(w.bots), 0)

    def test_starter_maps_never_spawn_bots(self):
        with patch.object(AY, 'get', side_effect=lambda k, *d: True if k == 'bot_oyuncular' else AY.DEFAULTS.get(k, *d)):
            w = self.make_world('1')  # 1-1
            self.assertFalse(w.can_have_bots())
            bot = w.spawn_bot()
            self.assertIsNone(bot)
            self.assertEqual(len(w.bots), 0)

    def test_battle_maps_spawn_bots_when_opted_in(self):
        def mock_get(key, *default):
            if key == 'bot_oyuncular':
                return True
            if key == 'bot_oyuncu_sayisi':
                return 3
            return AY.DEFAULTS.get(key, *default)

        with patch.object(AY, 'get', side_effect=mock_get):
            w = self.make_world('16')  # 4-4
            self.assertTrue(w.can_have_bots())
            self.assertEqual(w.bot_count(), 4)  # base (3) + 1 on battle maps
            w.spawn_initial_bots()
            self.assertEqual(len(w.bots), 4)

            hero_fac = self.p.d['pilot'].get('factionId', 1)
            for b in w.bots.values():
                self.assertNotEqual(b.faction_id, hero_fac)
                self.assertGreater(b.hp, 0)
                self.assertGreater(b.shield, 0)
                self.assertTrue(b.alive)

                # Verify all initialization packets serialize cleanly
                for name, fields in b.create_msgs(self.now):
                    if name != 'LegacyModule':
                        encoded = protocol.encode_message(name, fields)
                        self.assertGreater(len(encoded), 0)

    def test_select_and_attack_bot(self):
        def mock_get(key, *default):
            if key == 'bot_oyuncular':
                return True
            if key == 'bot_oyuncu_sayisi':
                return 1
            return AY.DEFAULTS.get(key, *default)

        with patch.object(AY, 'get', side_effect=mock_get):
            w = self.make_world('16')
            bot = w.spawn_bot(announce=False)
            self.assertIsNotNone(bot)

            # Test selection
            self.sent.clear()
            w.select({'targetId': bot.id})
            self.assertEqual(w.target, bot.id)
            sels = [f for n, f in self.sent if n == 'ShipSelectionCommand']
            self.assertEqual(len(sels), 1)
            self.assertEqual(sels[0]['userId'], bot.id)

            # Test laser attack
            self.sent.clear()
            w.laser_start({'targetId': bot.id})
            self.assertTrue(w.attacking)
            self.assertEqual(w.target, bot.id)

            # Test dealing damage to bot
            initial_hp, initial_shield = bot.hp, bot.shield
            self.sent.clear()
            w.hit_bot(bot.id, 50000, 1)
            self.assertTrue(bot.engaged)
            self.assertEqual(bot.target, w.hid)
            self.assertLess(bot.shield, initial_shield)
            hits = [f for n, f in self.sent if n == 'AttackHitCommand']
            self.assertEqual(len(hits), 1)
            self.assertEqual(hits[0]['victimId'], bot.id)

    def test_bot_special_abilities(self):
        w = self.make_world('16')
        bot = BOT_P.BotPlayer(BOT_P.BOT_UID_BASE + 999, 'TestSolace', 'WAR', 9101, 2, 'ship_solace-plus', 1000, 1000)
        w.bots[bot.id] = bot

        # Trigger Solace heal below 50% HP
        bot.hp = int(bot.max_hp * 0.45)
        self.sent.clear()
        w.hit_bot(bot.id, 1000, 1)
        self.assertTrue(bot.used_heal)
        self.assertTrue(any('HEALING' in str(f) for n, f in self.sent))

        # Trigger Insta-Shield below 28% HP
        bot.hp = int(bot.max_hp * 0.25)
        self.sent.clear()
        w.hit_bot(bot.id, 1000, 1)
        self.assertTrue(bot.used_ish)
        self.assertTrue(any('ISH' in str(f) for n, f in self.sent))

    def test_kill_bot_drops_cargo_and_pvp_rewards(self):
        w = self.make_world('16')
        bot = BOT_P.BotPlayer(BOT_P.BOT_UID_BASE + 888, 'TestTarget', 'PVP', 9102, 3, 'ship_cyborg', 2000, 2000)
        w.bots[bot.id] = bot
        w.target = bot.id
        w.attacking = True

        uri_before = self.p.d['pilot'].get('uridium', 0)
        self.sent.clear()
        w.hit_bot(bot.id, bot.max_hp + bot.max_shield + 100000, 1)

        # Bot is dead and removed
        self.assertFalse(bot.alive)
        self.assertNotIn(bot.id, w.bots)
        self.assertIsNone(w.target)
        self.assertFalse(w.attacking)

        # Cargo box dropped
        self.assertTrue(len(w.boxes) > 0)

        # Destruction commands emitted
        destroyed = [f for n, f in self.sent if n == 'ShipDestroyedCommand']
        removed = [f for n, f in self.sent if n == 'ShipRemoveCommand']
        self.assertEqual(len(destroyed), 1)
        self.assertEqual(destroyed[0]['destroyedUserId'], bot.id)
        self.assertTrue(any(r['userId'] == bot.id for r in removed))

        # PvP rewards credited
        self.assertGreater(self.p.d['pilot'].get('uridium', 0), uri_before)

        # Respawn scheduled
        pending_bots = [p for p in w.pending if p[1] == 'bot']
        self.assertEqual(len(pending_bots), 1)

    def test_bot_ai_respects_peace_zone_and_attacks_when_hostile(self):
        w = self.make_world('16')
        bot = BOT_P.BotPlayer(BOT_P.BOT_UID_BASE + 777, 'AIBot', 'PVP', 9103, 2, 'ship_goliath-plus', 1000, 1000)
        w.bots[bot.id] = bot

        # Hero inside peace zone: bot must not engage
        with patch.object(w, 'hero_pos', return_value=(1000, 1000)), \
             patch.object(w, 'in_peace', return_value=True):
            bot.think(w, self.now)
            self.assertFalse(bot.engaged)

        # Hero in combat area: bot engages on spot, then attacks when engaged
        with patch.object(w, 'hero_pos', return_value=(1000, 1000)), \
             patch.object(w, 'in_peace', return_value=False), \
             patch.object(w, 'invuln_until', 0.0), \
             patch.object(w, 'hero_dead', False), \
             patch.object(w, 'jumping', False), \
             patch.object(w, 'gizli', return_value=False):
            bot.next_shot = 0.0
            self.sent.clear()
            bot.think(w, self.now)
            self.assertTrue(bot.engaged)
            # Second tick while engaged fires weapon
            bot.think(w, self.now)
            lasers = [f for n, f in self.sent if n == 'AttackLaserRunCommand']
            self.assertTrue(len(lasers) >= 1)

    def test_hero_death_by_bot_registers_player_destruction(self):
        w = self.make_world('16')
        bot = BOT_P.BotPlayer(BOT_P.BOT_UID_BASE + 666, 'KillerBot', 'WAR', 9104, 2, 'ship_goliath-plus', 1000, 1000)
        w.bots[bot.id] = bot

        msgs = []
        w.hero_death(msgs, killer=bot)
        self.assertTrue(w.hero_dead)

        kills = [f for n, f in msgs if n == 'KillScreenPostCommand']
        self.assertEqual(len(kills), 1)
        self.assertEqual(kills[0]['killerName'], bot.d['ad'])
        self.assertEqual(kills[0]['cause']['cause'], 0)  # DestructionCause.PLAYER


if __name__ == '__main__':
    unittest.main()
