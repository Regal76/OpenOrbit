"""Infiltration (yol haritası Ö3; veri data/ek_etkinlikler.json 'sizma').

İstemci: menü öğesi infiltration (pencere 87, "Infiltration Game") InfiltrationStatusCommand {currentNpcs (kalan), maxNpcs,
secondsRemaining} gösterir ("Infiltrators killed: %COUNT%"). Metinler (flashres): msg_infiltration_spawned_map_single (%MAP%),
msg_infiltration_success, msg_infiltration_defeat. Gizli gemi ShipCreateCommand.cloaked ile; görünür olması 0|n|INV|<kimlik>|0.
Kurallar (resmî SSS 2013, fandom): rastgele bir firma haritasında (X-1'de değil) gizli bir komando takımı çıkar; 10 dakikada bulunup
yok edilmeli, yoksa kaçar. Komandolar ateş etmez, mini haritada sarı nokta; vurulunca (ya da EMP'yle) görünür olurlar; olağan
uzaylıdan fazla ödül verirler (2x; kaynaklar 2x/4x diyor). Akşam saatlerinde (19-22) turlar ardı ardına; Şükran Günü haftası.
Tek oyunculu uyarlama: takım oyuncunun firmasının X-2..X-8 haritalarından birinde; oyuncu o haritadaysa (ya da sonradan gelirse)
kalan komandolar haritanın rastgele bir yerinde doğar. Takım boyu, tur arası ve uzaylı türleri veride (_uyarlama); turun
'gizli_patron' olasılığıyla komandolardan biri gizli Boss Kristallon'dur (Uber Kristallon'un ganimeti; fandom Infiltration).
Profilde tutulmaz (turlar oturumluk).
"""
import json, os, random, time

import harita as H
import takvim as TK
from eski_protokol import legacy

HERE = os.path.dirname(os.path.abspath(__file__))
_PATH = os.path.join(HERE, 'data', 'ek_etkinlikler.json')
D = (json.load(open(_PATH, encoding='utf8')) if os.path.exists(_PATH) else {}).get('sizma', {})
EVENT = 'infiltration'


def active(now=None):
    return EVENT in TK.active(now)


def in_slot(now=None):
    t = time.localtime(time.time() if now is None else now)
    h = t.tm_hour + t.tm_min / 60.0
    return any(a <= h < b for a, b in D.get('saatler', [[19, 22]]))


class Sizma:
    def __init__(self, profil, magaza, log=print):
        self.p, self.m, self.log = profil, magaza, log
        self.world = None
        self.round = None                          # {harita, sinif, turler, adet, olen, bitis, dogdu}
        self.next_round = 0.0
        self.disarida = 0                          # ortak haritada öteki oyuncuların öldürdüğü komandolar (on_kill; tick sayar)

    def faction(self):
        return self.p.d['pilot'].get('factionId', 2)

    def status_cmd(self, now=None):
        r = self.round
        now = time.time() if now is None else now
        if not r:
            return ('InfiltrationStatusCommand', {'currentNpcs': 0, 'maxNpcs': 0, 'secondsRemaining': 0})
        # currentNpcs = kalan komando (istemci "killed" sayısını maxNpcs - currentNpcs yazar; canlı)
        return ('InfiltrationStatusCommand', {'currentNpcs': r['adet'] - r['olen'], 'maxNpcs': r['adet'],
                                              'secondsRemaining': max(0, int(r['bitis'] - now))})

    def map_for(self, cls):
        return next((m for m, n in H.NAMES.items() if H.map_class(m) == cls and H.company(m) == self.faction()), 0)

    def start_round(self, now):
        cls = random.choice(D.get('haritalar', ['X-2', 'X-3', 'X-4', 'X-5', 'X-6', 'X-7', 'X-8']))
        pool = D.get('turler', ['75', '73', '76', '78', '81'])
        n = D.get('adet', 6)
        kinds = [random.choice(pool) for _ in range(n)]
        boss = D.get('gizli_patron')
        if boss and random.random() < boss['olasilik']:      # gizli Boss Kristallon: bir komandonun yerine (Uber Kristallon'un ganimeti)
            kinds[random.randrange(n)] = boss['tur']
        self.round = dict(harita=self.map_for(cls), sinif=cls, turler=kinds, adet=n, olen=0,
                          bitis=now + D.get('sure_sn', 600), dogdu=False)
        self.log('   Infiltration: komando takımı %s (%d)' % (H.name(self.round['harita']), n))
        msgs = [legacy('0|A|STM|msg_infiltration_spawned_map_single|%%MAP%%|%s' % H.name(self.round['harita'])), self.status_cmd(now)]
        if self.world and int(self.world.map_id) == self.round['harita']:
            self.spawn(self.world)
        return msgs

    def spawn(self, w):
        """Takımın kalan komandoları bu haritada (dünya kilidi altında ya da attach'te)."""
        r = self.round
        if not r or r['dogdu'] or int(w.map_id) != r['harita']:
            return
        r['dogdu'] = True
        mw, mh = H.map_size(w.map_id)
        cx, cy = random.randint(int(mw * 0.15), int(mw * 0.85)), random.randint(int(mh * 0.15), int(mh * 0.85))
        r['kimlikler'] = []
        for tip in r['turler'][r['olen']:]:
            if tip not in w.CFG_TYPES:
                continue

            def prep(n):
                n.gizli = True
                n.odul_carpani = D.get('odul_carpani', 2)
                n.sizma = self                     # takımın sahibi (arkadaş sunucusunda öteki oyuncu da vurabilir)
                n.pasif = True                     # komandolar ateş etmez (resmî SSS 2013)
                n.summoned = tip == D.get('gizli_patron', {}).get('tur')       # gizli patron ölünce yeniden doğmaz (etkinlik harita kontrolü de silmez)
            n = w.spawn_npc_at(tip, cx + random.randint(-400, 400), cy + random.randint(-400, 400), prep=prep)
            if n is not None:
                n.engaged = False
                r['kimlikler'].append(n.id)

    def attach(self, world):
        self.world = world
        if self.round and active():
            self.spawn(world)
            return [self.status_cmd()]
        return []

    def login_msgs(self):
        return [self.status_cmd()] if active() else []

    def on_kill(self, w, npc, x, y):
        owner = getattr(npc, 'sizma', None)
        if owner is not self:
            if owner is not None:                # öteki oyuncunun takımı: sayaç onun, mesajları onun turunda (tick)
                owner.disarida += 1
            return []
        return self.killed()

    def killed(self):
        r = self.round
        if not r:
            return []
        r['olen'] += 1
        if r['olen'] >= r['adet']:
            r['bitis'] = time.time()             # sayaç durur, pencere son durumu (n/n) gösterir
        msgs = [self.status_cmd()]
        if r['olen'] >= r['adet']:
            self.log('   Infiltration: takım yok edildi')
            msgs.append(legacy('0|A|STM|msg_infiltration_success'))
            self.round = None
            self.next_round = time.time() + D.get('ara_sn', 120)
        return msgs

    def tick(self, now):
        msgs = []
        while self.disarida > 0:
            self.disarida -= 1
            msgs += self.killed()
        if msgs:
            return msgs
        if not active(now):
            self.round = None
            return []
        r = self.round
        if r and now >= r['bitis']:
            self.log('   Infiltration: takım kaçtı (%d/%d)' % (r['olen'], r['adet']))
            msgs = [legacy('0|A|STM|msg_infiltration_defeat')]
            w = self.world
            if w and r.get('kimlikler'):
                with w.lock:
                    for uid in r['kimlikler']:
                        n = w.npcs.get(uid)
                        if n and n.alive:
                            w.send(w.remove_npc(n))        # takım kaçtı
            self.round = None
            self.next_round = now + D.get('ara_sn', 120)
            return msgs + [self.status_cmd(now)]
        if not r and in_slot(now) and now >= self.next_round:
            return self.start_round(now)
        return []
