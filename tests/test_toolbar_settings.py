"""Toolbar preferences must reach the live client and survive profile reloads."""
import copy
import itertools
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'server'))

from profil import Profil
import protocol


BAR_SETTINGS = ('showSecondQuickslotBar', 'proActionBarEnabled',
                'proActionBarKeyboardInputEnabled', 'proActionBarAutohideEnabled')


class ToolbarSettingsTest(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.path = Path(temporary.name) / 'profil.json'
        with (ROOT / 'server/data/varsayilan/giris.json').open(encoding='utf8') as source:
            self.defaults = json.load(source)
        self.profile = Profil(self.defaults['tohum'], path=str(self.path))
        self.template = next(row for row in self.defaults['hazir']
                             if row['_m'] == 'MenuInitializationCommand')
        self.original = copy.deepcopy(self.template)

    def menu(self, profile=None):
        return (profile or self.profile).patch_template('MenuInitializationCommand', self.template)

    def test_all_toolbar_switches_round_trip_independently_through_wire_save_and_login(self):
        for values in itertools.product((False, True), repeat=len(BAR_SETTINGS)):
            with self.subTest(values=values):
                expected = dict(zip(BAR_SETTINGS, values))
                request = dict(self.defaults['tohum']['UserSettingsCommand']['displaySettingsModule'], **expected)
                _, name, fields, left, error = protocol.decode_message(
                    protocol.encode_message('DisplaySettingsRequest', request))
                self.assertEqual((name, left, error), ('DisplaySettingsRequest', 0, None))
                self.assertTrue(self.profile.apply(name, fields))
                self.profile.save()
                reloaded = Profil(self.defaults['tohum'], path=str(self.path))
                name, settings = reloaded.generate('@ayarlar')
                _, _, received, left, error = protocol.decode_message(protocol.encode_message(name, settings))
                self.assertEqual((left, error), (0, None))
                display = received['displaySettingsModule']
                self.assertFalse(display['notSet'])
                self.assertEqual({key: display[key] for key in BAR_SETTINGS}, expected)

    def test_premium_and_pro_slots_survive_hide_show_and_relogin(self):
        item = self.template['slotBars'][0]['slots'][0]['menuItemId']
        for bid, slot in (('premiumSlotBar', 4), ('proActionBar', 7)):
            self.assertTrue(self.profile.slot_bar_set(dict(menuItemId=item, slotBarIdFrom='',
                slotIdFrom=0, slotBarIdTo=bid, slotIdTo=slot), self.template['slotBars']))
        for visible in (False, True):
            self.profile.apply('DisplaySettingsRequest', dict(zip(BAR_SETTINGS, (visible,) * 4)))
            self.profile.save()
            reloaded = Profil(self.defaults['tohum'], path=str(self.path))
            menu = self.menu(reloaded)
            bars = {bar['slotBarId']: bar for bar in menu['slotBars']}
            self.assertEqual(bars['premiumSlotBar']['slots'],
                [dict(_='SlotInfoCommand', menuItemId=item, slotId=4)])
            self.assertEqual(bars['proActionBar']['slots'],
                [dict(_='SlotInfoCommand', menuItemId=item, slotId=7)])
            self.assertCountEqual(bars['standardSlotBar']['slots'], self.original['slotBars'][0]['slots'])
        self.assertEqual(self.template, self.original)

    def test_live_display_save_refreshes_the_menu_after_persisting_preferences(self):
        # game has import-time globals; a separate interpreter and explicit temporary
        # profile/log paths keep the real account and running server out of this test.
        script = r'''
import copy, json, sys
from types import SimpleNamespace
root, fixture = sys.argv[1:]
sys.path.insert(0, root + '/server')
sys.argv = ['game.py', fixture, '--profil=' + fixture + '/session-profile.json']
import game
session = game.Session.__new__(game.Session)
session.profil = game.PROFIL
session.world = None
session.secrets = set()
session.ek = SimpleNamespace(handles=lambda name: False)
session.magaza = SimpleNamespace(handles=lambda name, fields: False)
sent = []
session.send = lambda messages, *args, **kwargs: sent.extend(messages)
template = next(row for row in game.SABLON.giris['hazir'] if row['_m'] == 'MenuInitializationCommand')
original = copy.deepcopy(template)
item = template['slotBars'][0]['slots'][0]['menuItemId']
session.profil.slot_bar_set(dict(menuItemId=item, slotBarIdFrom='', slotIdFrom=0,
    slotBarIdTo='premiumSlotBar', slotIdTo=4), template['slotBars'])
results = []
for enabled in (False, True):
    sent.clear()
    request = dict(session.profil.d['ayarlar']['displaySettingsModule'],
        showSecondQuickslotBar=enabled, proActionBarEnabled=enabled,
        proActionBarKeyboardInputEnabled=not enabled, proActionBarAutohideEnabled=enabled)
    session.on_packet('DisplaySettingsRequest', 0, request, None)
    results.append(dict(settings=copy.deepcopy(session.profil.d['ayarlar']['displaySettingsModule']),
        messages=copy.deepcopy(sent)))
print(json.dumps(dict(results=results, template_unchanged=(template == original))))
'''
        result = subprocess.run([sys.executable, '-c', script, str(ROOT), str(self.path.parent)],
                                cwd=self.path.parent, text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        observed = json.loads(result.stdout)
        self.assertTrue(observed['template_unchanged'])
        for enabled, row in zip((False, True), observed['results']):
            with self.subTest(enabled=enabled):
                self.assertEqual(row['settings']['showSecondQuickslotBar'], enabled)
                menus = [fields for name, fields in row['messages'] if name == 'MenuInitializationCommand']
                self.assertEqual(len(menus), 1, 'Saved toolbar preferences need a live UIBag refresh')
                bars = {bar['slotBarId']: bar for bar in menus[0]['slotBars']}
                self.assertEqual(bars['premiumSlotBar']['slots'][0]['slotId'], 4)
                self.assertCountEqual(bars['standardSlotBar']['slots'], self.original['slotBars'][0]['slots'])


if __name__ == '__main__':
    unittest.main(verbosity=2)
