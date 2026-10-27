"""Panel-only live grants: no chat parser and each successful grant is public."""
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
from urllib.error import HTTPError
from urllib.request import urlopen


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'server'))

import yonetim


class _Profile:
    user_id = 42
    d = {'pilot': {'userName': 'Regal'}}

    def __init__(self):
        self.saved = False

    def save(self):
        self.saved = True


class _Shop:
    def __init__(self):
        self.calls = []

    def reward(self, loot, amount):
        self.calls.append((loot, amount))
        return [('LootCommand', {'loot': loot, 'amount': amount})]

    def money_msgs(self):
        return []


class _Session:
    def __init__(self):
        self.profil = _Profile()
        self.magaza = _Shop()
        self.sent = []

    def send(self, messages, quiet=False):
        self.sent.append((messages, quiet))


class _Chat:
    def __init__(self):
        self.messages = []

    def duyuru(self, text):
        self.messages.append(text)


class _Game:
    def __init__(self):
        self.session = _Session()
        self.OTURUMLAR = [self.session]
        self.SOHBET = _Chat()

    def log(self, text):
        pass


class PanelLiveGrantTest(unittest.TestCase):
    def test_grant_rewards_connected_player_and_announces_to_everyone(self):
        game = _Game()
        with patch.object(yonetim, 'known_loots', return_value={'ammunition_laser_lcb-10': 'ammunition'}):
            result = yonetim.grant(game, '42', 'ammunition_laser_lcb-10', 25)
        self.assertEqual(game.session.magaza.calls, [('ammunition_laser_lcb-10', 25)])
        self.assertTrue(game.session.profil.saved)
        self.assertEqual(game.session.sent[0][1], True)
        self.assertEqual(len(game.SOHBET.messages), 1)
        self.assertIn('Regal', game.SOHBET.messages[0])
        self.assertEqual(result['adet'], 25)

    def test_grant_rejects_unknown_loot_before_changing_a_profile(self):
        game = _Game()
        with patch.object(yonetim, 'known_loots', return_value=set()):
            with self.assertRaisesRegex(ValueError, 'Bilinmeyen eşya'):
                yonetim.grant(game, '42', 'not-a-real-item', 1)
        self.assertEqual(game.session.magaza.calls, [])
        self.assertFalse(game.session.profil.saved)

    def test_only_connected_player_ids_are_available(self):
        game = _Game()
        self.assertEqual(yonetim.players(game), [{'id': '42', 'ad': 'Regal'}])
        with patch.object(yonetim, 'known_loots', return_value={'ammunition_laser_lcb-10': 'ammunition'}):
            with self.assertRaisesRegex(ValueError, 'artık bağlı değil'):
                yonetim.grant(game, '999', 'ammunition_laser_lcb-10', 1)

    def test_owner_endpoint_rejects_requests_without_the_panel_secret(self):
        game = _Game()
        server = yonetim.start(game, 'panel-secret', port=0)
        self.addCleanup(server.server_close)
        self.addCleanup(server.shutdown)
        url = 'http://127.0.0.1:%d/oyuncular' % server.server_address[1]
        with self.assertRaises(HTTPError) as caught:
            urlopen(url, timeout=2)
        self.assertEqual(caught.exception.code, 403)
