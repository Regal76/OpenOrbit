"""LoW (Lord of War), tek kişilik sürüm (yol haritası Aşama 4). Değerler ve kaynaklar data/low.json'da.

Akış (dünya döngüsünden, kilit altında): giriş -> eski korsanlar türlerine göre dalga dalga -> dört röle istasyonu sırayla (istemcinin
RELAY_STATION varlığı; wiki: "shoot the station until its green indicator loads": vurulunca dolar, dünyanın asset_targets'ı; yedek
olarak yanında durunca da; haritada korsan varken etkinleşmez, istemcinin metni) -> Century Falcon ve eskortu -> bitti: ortada
firmanın X-3'üne dönüş portalı. Etkin her röle haritanın ortasında (LoW HQ'su, harita.py) onarım robotunu hızlandırır (wiki "speeds
HP regeneration in the middle of the map").
İlerleme profilde (low): ölünce donus_sn içinde X-3'teki portaldan dönülürse kaldığı aşamadan sürer (dalganın uzaylıları yeniden gelir),
yoksa baştan. LoW'da tamir yalnız istasyonda (X-1); atlama CPU'su çalışmaz.
"""
import json, math, os, random, time

import harita as H
import uzayli as UZ
from eski_protokol import legacy
from kapi import screen

HERE = os.path.dirname(os.path.abspath(__file__))
L = json.load(open(os.path.join(HERE, 'data', 'low.json'), encoding='utf8'))
MAP = L['harita']
RELAY_STATION = 31                  # AssetTypeModule.AssetType (istemci)
RELAY_BASE = 152100000
EXIT_ID = H.GATE_ID_BASE + 990010


def fresh():
    return {'asama': 'dalga', 'dalga': 0, 'role': 0, 'olum': None}


class Low:
    def __init__(self, world):
        self.w, self.p = world, world.p
        self.npcs = set()           # bu aşamanın uzaylıları
        self.relay = None           # {kimlik, x, y, ilerleme, son}
        self.boss = None
        now = time.time()
        st = self.p.d.get('low')
        returning = bool(st and st.get('asama') != 'bitti' and st.get('olum') and now - st['olum'] <= L['donus_sn'])
        with self.p.lock:
            self.p.d['low'] = dict(st, olum=None) if returning else fresh()
            self.p.dirty = True
        self.t = now + L['giris_sn']
        world.asset_targets = self             # röle seçilir ve vurulur (dunya.asset_laser)
        self.say('devam' if returning else 'giris')
        self.w.log('   LoW: %s (%s)' % ('kaldığı yerden' if returning else 'baştan', self.st['asama']))

    @property
    def st(self):
        return self.p.d['low']

    def save(self, **kw):
        with self.p.lock:
            self.st.update(kw)
            self.p.dirty = True

    def say(self, key, **kw):
        vals = dict(roleler=L['role']['adet'], toplam=len(L['dalgalar']))
        vals.update(kw)
        self.w.send([screen(L['mesajlar'][key].format(**vals))])

    # ------------------------------------------------------------ doğurma
    def spawn(self, tip, count, near=None):
        w = self.w
        hx, hy = near or w.hero_pos()
        a, r = random.uniform(0, 2 * math.pi), random.uniform(*L['dogma_uzaklik'])
        cx = min(max(hx + math.cos(a) * r, 800), w.map_w - 800)
        cy = min(max(hy + math.sin(a) * r, 800), w.map_h - 800)
        out = []
        for i in range(count):
            b, d = random.uniform(0, 2 * math.pi), random.uniform(0, 250 + 40 * count)
            n = w.spawn_npc_at(tip, cx + math.cos(b) * d, cy + math.sin(b) * d)
            n.gate, n.engaged, n.hunt, n.next_think = True, True, True, time.time()
            self.npcs.add(n.id)
            out.append(n)
        return out

    def alive(self):
        self.npcs = {i for i in self.npcs if i in self.w.npcs and self.w.npcs[i].alive}
        return self.npcs

    # ------------------------------------------------------------ adımlar
    def tick(self, now):
        w = self.w
        if w.hero_dead or w.jumping or now < self.t:
            return
        a = self.st['asama']
        if a == 'dalga':
            if self.alive():
                return
            i = self.st['dalga']
            if i >= len(L['dalgalar']):
                self.save(asama='role', role=0)
                self.place_relay(now)
                return
            tip, n = L['dalgalar'][i]
            self.spawn(tip, n)
            self.save(dalga=i + 1)
            self.t = now + L['dalga_arasi_sn']
            self.say('dalga', ad=w.alien.CFG['tipler'][tip]['ad'].strip('-=[] '), adet=n, dalga=i + 1)
            w.log('   LoW dalga %d: %s x%d' % (i + 1, tip, n))
        elif a == 'role':
            if not self.relay:
                self.place_relay(now)
            self.relay_tick(now)
        elif a == 'boss':
            if not self.alive() and self.boss is None:
                self.spawn_boss()
            elif not self.alive():
                self.finish()

    def place_relay(self, now):
        """Sıradaki röle istasyonu: oyuncudan uzakta, yanında Vagrant savunması."""
        w = self.w
        no = self.st['role'] + 1
        x, y = w.alien.far_spot(None, 3000)
        aid = RELAY_BASE + no
        self.relay = dict(kimlik=aid, x=x, y=y, ilerleme=0.0, son=now, yuzde=-1)
        w.send([UZ.asset_create(aid, RELAY_STATION, x, y, name='Relay Station %d' % no)])
        tip, n = L['role']['savunma']
        self.spawn(tip, n, near=(x, y))
        self.say('role', no=no)
        w.log('   LoW röle istasyonu %d: (%d,%d)' % (no, x, y))

    def relay_tick(self, now):
        """Röle (yedek yol): yanında yaricap içinde, haritada korsan yokken ilerler; sn saniyede etkinleşir."""
        w, r, cfg = self.w, self.relay, L['role']
        dt, r['son'] = now - r['son'], now
        hx, hy = w.hero_pos(now)
        if math.hypot(r['x'] - hx, r['y'] - hy) > cfg['yaricap'] or self.alive():
            return
        r['ilerleme'] += min(dt, 1.0)
        self.relay_step(now)

    def relay_step(self, now):
        """Rölenin ilerlemesi (saniye; vuruş hasar/hasar x sn kadar): yüzde iletisi, dolunca etkinleşir."""
        w, r, cfg = self.w, self.relay, L['role']
        pct = min(100, int(100 * r['ilerleme'] / cfg['sn']))
        no = self.st['role'] + 1
        if pct // 25 > r['yuzde'] // 25 and pct < 100:
            r['yuzde'] = pct
            self.say('role_ilerleme', no=no, yuzde=pct)
        if r['ilerleme'] < cfg['sn']:
            return
        w.send([UZ.asset_remove(r['kimlik'], RELAY_STATION), legacy('0|A|STM|msg_relaisstation_activated')])
        self.relay = None
        self.say('role_tamam', no=no)
        w.log('   LoW röle istasyonu %d etkin' % no)
        if no >= cfg['adet']:
            self.save(asama='boss', role=no)
            self.t = now + L['dalga_arasi_sn']
        else:
            self.save(role=no)
            self.place_relay(now)

    def regen(self, now):
        """Onarım robotu çarpanı: haritanın ortasında (merkez.yaricap) etkin röle başına +merkez.onarim."""
        c = L['role']['merkez']
        hx, hy = self.w.hero_pos(now)
        if math.hypot(hx - self.w.map_w / 2, hy - self.w.map_h / 2) > c['yaricap']:
            return 1.0
        return 1 + c['onarim'] * self.st.get('role', 0)

    # ------------------------------------------------------------ röleyi vurma (dunya.asset_targets)
    def charge(self):
        """Rölenin dolumu hasar biriminde: (şimdiki, gereken)."""
        cfg = L['role']
        return int(self.relay['ilerleme'] / cfg['sn'] * cfg['hasar']), cfg['hasar']

    def asset_pos(self, uid):
        r = self.relay
        return (r['x'], r['y']) if r and uid == r['kimlik'] else None

    def asset_select(self, uid):
        now, need = self.charge()
        return [('ShipSelectionCommand', dict(userId=int(uid), shipType=0, shield=0, shieldMax=0, hitpoints=now, hitpointsMax=need,
                                              nanoHull=0, maxNanoHull=0, shieldSkill=False)),
                ('AssetInfoCommand', dict(assetId=int(uid), type=UZ.mod('AssetTypeModule', typeValue=RELAY_STATION), designId=0,
                                          expansionStage=0, hitpoints=now, maxHitpoints=need, shielded=False, shieldEnergy=0,
                                          maxShieldEnergy=0))]

    def asset_attackable(self, uid):
        """Korsanlar (rölenin savunanı da) haritadayken röle etkinleşmez (istemcinin metni)."""
        return [legacy('0|A|STM|msg_groupgate_cant_activate_relay_because_npcs_are_alive')] if self.alive() else []

    def asset_hit(self, uid, dmg):
        """Vuruş röleyi doldurur (gösterge: AttackHitAssetCommand'ın canı dolum)."""
        cfg = L['role']
        self.relay['ilerleme'] = min(cfg['sn'], self.relay['ilerleme'] + dmg / float(cfg['hasar']) * cfg['sn'])
        now, need = self.charge()
        msgs = [('AttackHitAssetCommand', dict(assetId=int(uid), hitpointsNow=now, hitpointsMax=need))]
        self.relay_step(time.time())
        return msgs

    def spawn_boss(self):
        self.boss = self.spawn(L['boss'], 1)[0].id
        tip, n = L['eskort']
        self.spawn(tip, n, near=self.w.npcs[self.boss].mover.pos(time.time()))
        self.say('boss')
        self.w.log('   LoW: Century Falcon geldi')

    def finish(self):
        w = self.w
        self.save(asama='bitti')
        dest = L['cikis'].get(str(self.p.d['pilot'].get('factionId')), 7)
        w.add_gate(dict(gateId=EXIT_ID, x=w.map_w // 2, y=w.map_h // 2, hedef=dest, designId=1))
        self.say('bitti')
        w.log('   LoW tamamlandı: X-3 portalı açık')
        self.boss = -1

    # ------------------------------------------------------------ dünya olayları
    def on_death(self):
        """Ölünce: dönüş süresi başlar; aşamanın uzaylıları gider (dönünce yeniden gelir)."""
        self.save(olum=time.time())
        if self.st['asama'] == 'dalga' and self.alive():
            self.save(dalga=max(0, self.st['dalga'] - 1))      # yarım kalan dalga dönünce baştan
        elif self.st['asama'] == 'boss':
            self.boss = None

    def asset_msgs(self):
        r = self.relay
        return [UZ.asset_create(r['kimlik'], RELAY_STATION, r['x'], r['y'], name='Relay Station %d' % (self.st['role'] + 1))] if r else []

    def cleanup_msgs(self):
        return [UZ.asset_remove(self.relay['kimlik'], RELAY_STATION)] if self.relay else []
