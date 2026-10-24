"""Etkinlik kapıları (yol haritası Aşama 7b; veri data/etkinlik_kapilari.json <- tools/etkinlik_kapilari.py).

Üreticideki kapılardan farkı: parça yok; etkinliği (takvim.py) sürerken giriş haritasında (X-1, X-4, X-8) portalı durur. Portaldan
girince kapı kurulur (canlar, dalga sırası, başlangıç zamanı); dalgalar, alt gruplar, canlar, kalıcı patronlar ve çok haritalı akış
kapi.Kosu'nunkiyle aynı (dalga biçimi kapilar.json'unki). Kurallar ('kural'):
  gunluk          günde bir giriş (aynı 'grup'taki kapılar birlikte: Gauntlet of Plutus Easy ya da Normal)
  bekleme_sn      bittikten ya da canlar tükendikten sonra bekleme (Trial of Terrors 12 saat)
  yillik          yılda bir (Birthday Gate)
  cpu             portalı yalnız CPU açar (Quarantine Zone: Immunizer CPU, X-7; pve_modlari.py)
  seviye, bir_kez en düşük seviye; bir kez tamamlanabilir (Compromising Invasion)
  rastgele        her haritanın dalgaları kendi aralarında rastgele sırayla ('sabit' dalga, Plutus, sonda; Gauntlet of Plutus)
  sure            bitiş süresi ölçülür (ölü geçen süre dahil); en iyi süreler profilde (Gauntlet of Plutus'un kişisel rekoru)
'secenek' grubundaki dalgalardan (Vortex'in "ya da" dalgaları) girişte biri seçilir. Dalga uzaylısının 'kutu'su ölünce düşer
(etkinlik_harita.py: Plutus Box, Demon Drone Box …); 'ek_turler' dalga dışı türler (Plutus'un Warhead'leri).
Ödüller ('odul'): EP, onur, kredi, uridyum ve eşyalar (mağazanın ödül işleviyle).
Profilde: etkinlik_kapilari {kapı: {hazir, dalga, can, sira, bas, tamam, son_gun, son_yil, son_bitis, en_iyi_sn, sureler}}.
Gauntlet of Plutus'un göstergesi istemcinin PlutusInfoCommand / PlutusStatusCommand'ıyla (can, mod, kalan süre, en iyi süreler).
Takvimsiz kapılar ('etkinlik' yok): Quarantine Zone ve Compromising Invasion (yol haritası Aşama 8).
Frozen Labyrinth ayrı (labirent.py); X-1'deki giriş portalı burada.
"""
import datetime, json, math, os, random, time

import harita as H
import kapi as KAPI
import siralama as SR
import takvim as TK
import ayar as AY

HERE = os.path.dirname(os.path.abspath(__file__))
D = json.load(open(os.path.join(HERE, 'data', 'etkinlik_kapilari.json'), encoding='utf8'))
GATES = D['kapilar']
DARK_MAPS = {int(m) for g in GATES.values() if g.get('karanlik') for m in g['haritalar']}      # el feneri (dunya.map_effect_msgs)
BY_MAP = {m: k for k, g in GATES.items() for m in g['haritalar']}
LAB = D['labirent']
PORTAL_BASE = 151900000                 # + kimlik (giriş), + 50 + kimlik (eve dönüş), + 100 + kimlik (sonraki harita)
LAB_ENTRY = PORTAL_BASE + 99            # X-1'deki Frozen Labyrinth portalı
# PlutusStatusCommand.mode: pencerenin durum satırı (istemci PlutusUIData.UpdateStatus): 0/1 bugün bitti ("Next Gauntlet opens in",
# geri sayım), 2 açık ("Time left to defeat Plutus", geri sayım), 3 sürüyor ("Time spent in the Gauntlet", ileri sayım), 4 etkinlik
# bitti ("Rankings will be tallied in"). Önce kolay/normal sanılıyordu: koşu sürerken "bugün bitirdin" yazıyordu (canlı test H48)
PLUTUS_DONE, PLUTUS_OPEN, PLUTUS_RUNNING = 1, 2, 3


def npc_type(key, wave, i):
    return 'eg_%s_%d_%d' % (key, wave, i)


def extra_type(key, name):
    return 'eg_%s_ek_%s' % (key, name)


def _tip(a, key=None, aggressive=True):
    d = dict(ad=a['gorunen_ad'], model=str(a['tur']), hp=a['hp'], kalkan=a['kalkan'], hasar=a['hasar'], hiz=a['hiz'],
             saldirgan=a.get('saldirgan', aggressive), odul=dict(a['odul']), kargo=dict(a.get('kargo', {})), npc_kimlik=a['npc_kimlik'])
    if key:
        d['kapi'] = key
    for k in ('kutu', 'davranis', 'anahtar', 'dusme', 'yeniden_sn', 'puan'):
        if a.get(k):
            d[k] = a[k]
    return d


# etkinlik puanının başarımdaki etkinlik adı (basarim.py EventScore: "bir Gauntlet of Plutus etkinliğinde 1.000 / 5.000 / 10.000 puan")
SCORE_EVENTS = {'plutus': 'GauntletOfPlutus'}


def register_npcs(tipler):
    """Kapı ve labirent uzaylılarını NPC türleri olarak ekler (kapi.register_npcs'in biçimi)."""
    for key, g in GATES.items():
        for n, w in enumerate(g['dalgalar']):
            for i, a in enumerate(w['uzaylilar']):
                tipler[npc_type(key, n, i)] = _tip(a, key)
        for name, a in g.get('ek_turler', {}).items():
            tipler[extra_type(key, name)] = _tip(a, key)
    for k, a in LAB['uzaylilar'].items():
        tipler[k] = _tip(a, aggressive='meteoroid' not in k and 'synk' not in k)


def center(map_id):
    w, h = H.map_size(map_id)
    return w // 2, h // 2


def today(now=None):
    return datetime.date.fromtimestamp(time.time() if now is None else now).isoformat()


def fmt_time(secs):
    m, s = divmod(int(secs), 60)
    return '%d:%02d:%02d' % (m // 60, m % 60, s) if m >= 60 else '%d:%02d' % (m, s)


class EtkinlikKapilari:
    """kapi.Kapilar'ın arayüzü (gate, finish, exit_portal, next_portal, home, p) etkinlik kapıları için."""

    def __init__(self, profil, log=print):
        self.p, self.log = profil, log
        self.m = None                       # mağaza (eşya ödülleri)
        self.finish_hooks = []              # kapı bitince (anahtar) -> mesajlar (Fiesta Gate'in AP'si: fiesta.py)
        self.wave_hooks = []                # dalga bitince (anahtar, toplam dalga) -> mesajlar (eski Invasion: istila.py)

    @property
    def d(self):
        return self.p.d.setdefault('etkinlik_kapilari', {})

    def gate(self, key):
        return self.d.setdefault(key, dict(hazir=False, dalga=0, can=GATES[key]['can'], tamam=0))

    def home(self):
        return KAPI.HOME_MAP.get(self.p.d['pilot'].get('factionId'), 5)

    # ------------------------------------------------------------ giriş
    def allowed(self, key, now=None):
        """-> (girilebilir mi, neden)."""
        now = time.time() if now is None else now
        g, G = GATES[key], self.gate(key)
        if G.get('hazir'):
            return True, 'sürüyor'
        if g.get('etkinlik') and not TK.is_active(g['etkinlik'], now):
            return False, 'etkinlik yok'
        kural = g.get('kural', {})
        if AY.get('giris_siniri_yok'):                       # panel: günlük/yıllık/bir kez ve bekleme süresi yok
            kural = {k: v for k, v in kural.items() if k not in ('bir_kez', 'gunluk', 'yillik', 'bekleme_sn')}
        if kural.get('cpu'):
            return False, 'CPU ile açılır'            # Quarantine Zone: Immunizer CPU kapıyı kurar (pve_modlari.py)
        if kural.get('seviye') and self.p.d['pilot'].get('level', 1) < kural['seviye']:
            return False, 'seviye %d gerekli' % kural['seviye']
        if kural.get('azami_seviye') and self.p.d['pilot'].get('level', 1) > kural['azami_seviye']:
            return False, 'seviye en çok %d' % kural['azami_seviye']          # eski Invasion: seviye aralığına göre kapı
        if kural.get('firma') and kural['firma'] != self.p.d['pilot'].get('factionId'):
            return False, 'başka firmanın kapısı'
        if kural.get('bir_kez') and G.get('tamam', 0) > 0:
            return False, 'tamamlandı'
        if kural.get('gunluk'):
            group = [k for k, x in GATES.items() if x.get('kural', {}).get('grup', k) == kural.get('grup', key)]
            if any(self.gate(k).get('son_gun') == today(now) for k in group):
                return False, 'bugün girildi'
        if kural.get('yillik') and G.get('son_yil') == today(now)[:4]:
            return False, 'bu yıl girildi'
        if kural.get('bekleme_sn') and now < G.get('son_bitis', 0) + kural['bekleme_sn']:
            return False, 'bekleme %d sn' % (G['son_bitis'] + kural['bekleme_sn'] - now)
        return True, ''

    def here(self, want, map_id):
        if want == 'X-1':
            return int(map_id) == self.home()
        return H.map_class(map_id) == want and H.company(map_id) == self.p.d['pilot'].get('factionId')

    def entry_portals(self, map_id, station, now=None):
        """Bu haritadaki etkinlik kapısı portalları (etkinlik sürerken ve girilebilirken) ve X-1'de Frozen Labyrinth'inki."""
        now = time.time() if now is None else now
        out = []
        sx, sy = (station['posX'], station['posY']) if station else (KAPI.MAP_W // 2, KAPI.MAP_H // 2)
        cx, cy = KAPI.MAP_W // 2, KAPI.MAP_H // 2
        base = math.atan2(cy - sy, cx - sx) + math.pi        # üretici kapılarının karşı yanında, yay üzerinde
        dist = KAPI.K['portal_uzaklik'] + 600
        slots = sorted(GATES) + ['labirent']
        spot = lambda key: (int(sx + math.cos(base + (slots.index(key) - len(slots) / 2.0) * 0.4) * dist),
                            int(sy + math.sin(base + (slots.index(key) - len(slots) / 2.0) * 0.4) * dist))
        for key in sorted(GATES):
            g = GATES[key]
            if g.get('kural', {}).get('pencere'):
                continue                    # pencereli giriş (Fiesta Gate: tek portal, zorluğu pencere seçer; fiesta.py)
            if not self.here(g['giris'], map_id) or not self.allowed(key, now)[0]:
                continue
            G = self.gate(key)
            order = self.order(key)
            dest = g['dalgalar'][order[min(G['dalga'], len(order) - 1)]]['harita'] if G.get('hazir') else g['dalgalar'][0]['harita']
            x, y = spot(key)
            out.append(dict(gateId=PORTAL_BASE + g['kimlik'], x=x, y=y, hedef=dest, designId=g['portal'], kapi=key,
                            etkinlik_kapisi=True, varis=center(dest)))
        if self.here(LAB['giris'], map_id) and TK.is_active(LAB['etkinlik'], now):
            import labirent as LB
            dest = random.choice(LAB['baslangic'])
            x, y = spot('labirent')
            out.append(dict(gateId=LAB_ENTRY, x=x, y=y, hedef=dest, designId=LAB['portal'], kapi='labirent',
                            varis=LB.arrival_spot(dest)))
        return out

    def enter(self, key, now=None):
        """Portaldan girildi: kurulu değilse kapı kurulur (canlar, dalga sırası, süre)."""
        now = time.time() if now is None else now
        g, G = GATES[key], self.gate(key)
        if G.get('hazir'):
            return
        waves = g['dalgalar']
        groups = {}
        for i, w in enumerate(waves):
            if w.get('secenek'):
                groups.setdefault(w['secenek'], []).append(i)
        pick = {s: random.choice(v) for s, v in groups.items()}       # "ya da" dalgalarından biri
        sira = [i for i, w in enumerate(waves) if not w.get('secenek') or pick[w['secenek']] == i]
        if g.get('kural', {}).get('rastgele'):        # aynı haritanın dalgaları kendi aralarında karışır
            by_map = {}
            for i in sira:
                by_map.setdefault(waves[i]['harita'], []).append(i)
            sira = []
            for m in sorted(by_map, key=lambda m: min(by_map[m])):
                part = by_map[m]
                rest = [i for i in part if not waves[i].get('sabit')]
                random.shuffle(rest)
                sira += rest + [i for i in part if waves[i].get('sabit')]
        with self.p.lock:
            G.update(hazir=True, dalga=0, can=AY.adet('kapi_can', g['can']), sira=sira, bas=now, son_gun=today(now),
                     son_yil=today(now)[:4])                   # panel: kapı canı
            self.p.dirty = True
        self.log('   %s kuruldu (%d dalga, %d can)' % (g['ad'], len(sira), G['can']))

    def order(self, key):
        G = self.gate(key)
        return G.get('sira') or list(range(len(GATES[key]['dalgalar'])))

    # ------------------------------------------------------------ portallar
    def exit_portal(self, key, map_id, side=False):
        x, y = center(map_id)
        return dict(gateId=PORTAL_BASE + 50 + GATES[key]['kimlik'], x=x - 1500 if side else x, y=y, hedef=self.home(), designId=1,
                    kapi=key, cikis=True)

    def next_portal(self, key, map_id, dest):
        x, y = center(map_id)
        return dict(gateId=PORTAL_BASE + 100 + GATES[key]['kimlik'], x=x, y=y, hedef=dest, designId=GATES[key]['portal'], kapi=key,
                    varis=center(dest))

    # ------------------------------------------------------------ bitiş
    def end(self, key, now=None):
        now = time.time() if now is None else now
        with self.p.lock:
            G = self.gate(key)
            G.update(hazir=False, dalga=0, can=GATES[key]['can'], son_bitis=now)
            G.pop('sira', None)
            self.p.dirty = True

    def finish(self, key, reward_msgs=None):
        """Son dalga bitti: ödüller, süre (en iyi), kapı kapanır -> (mesajlar, bilgi)."""
        g, G, now = GATES[key], self.gate(key), time.time()
        o = g.get('odul', {})
        msgs = []
        para = {k: AY.miktar(k, o[k], 'kapi') for k in ('ep', 'onur', 'kredi', 'uridyum') if o.get(k)}      # panelin çarpanları
        if para:
            tot = self.p.gain(neden='galaxy_gate_done', **para)
            msgs += reward_msgs(tot, **para) if reward_msgs else []
        for loot, n in o.get('esyalar', []):
            n = random.randint(*n) if isinstance(n, list) else n          # aralık (Indoctrine Oil 0-20)
            if n > 0 and self.m:
                msgs += self.m.prize(loot, n, 'kapi')        # panel: kapı/mod ödülü çarpanı
        if o.get('biri') and self.m:                       # olasılık ağırlıklı biri (Quarantine Box'ın mühimmat paketi)
            loot, n, _ = random.choices(o['biri'], weights=[w for _, _, w in o['biri']])[0]
            msgs += self.m.prize(loot, random.randint(*n) if isinstance(n, list) else n, 'kapi')
        for loot, n, chance in o.get('sans', []):          # şanslı ödül (Quarantine Box'ın LF-4'ü)
            if random.random() < AY.chance('dusme', chance, 'kapi') and self.m:
                msgs += self.m.prize(loot, n, 'kapi')
        secs = int(now - G.get('bas', now))
        best = G.get('en_iyi_sn')
        with self.p.lock:
            G['tamam'] = G.get('tamam', 0) + 1
            if g.get('kural', {}).get('sure'):
                if best is None or secs < best:
                    G['en_iyi_sn'] = secs
                G['sureler'] = sorted(G.get('sureler', []) + [secs])[:5]
            self.p.dirty = True
        self.end(key, now)
        for fn in self.finish_hooks:
            msgs += fn(key)
        self.p.ach('gate', tur=g.get('kapi_turu') or '%s_GATE' % key.upper())    # istemcinin GalaxyGateType'ı (Birthday: BIRTHDAY)
        record = G.get('en_iyi_sn') == secs and best != secs
        if record:
            self.p.ach('rekor_plutus')               # şampiyon başarımı (Gauntlet of Plutus; süreli tek kapı): kişisel rekor
        self.log('   %s tamamlandı: %s%s' % (g['ad'], fmt_time(secs), ' (yeni rekor)' if record else ''))
        return msgs, dict(yeni={'parcalar': []}, kronos=None, sure=secs)

    # ------------------------------------------------------------ etkinlik puanı (Gauntlet of Plutus)
    def score(self, key, now=None):
        """Bu etkinlik dönemindeki puan kaydı {donem, puan}: Easy ve Normal birlikte; yeni dönemde sıfırdan."""
        ev = GATES[key].get('etkinlik') or key
        p = TK.period(ev, now) if ev in TK.EVENTS else None
        donem = int(p[0]) if p else 0
        rec = self.d.setdefault('puan', {}).get(ev)
        if not rec or rec.get('donem') != donem:
            rec = self.d['puan'][ev] = {'donem': donem, 'puan': 0}
        return rec

    def add_points(self, key, n, now=None):
        """Uzaylının etkinlik puanı (kaynak: uzaylı başına aralık, forum 2019) -> PlutusPointsUpdateCommand; başarım olayı."""
        with self.p.lock:
            rec = self.score(key, now)
            rec['puan'] += n
            self.p.dirty = True
        ev = GATES[key].get('etkinlik')
        if ev in SCORE_EVENTS:
            self.p.ach('event_score', etkinlik=SCORE_EVENTS[ev], deger=rec['puan'])
        G = self.gate(key)
        entries = [dict(_='PlutusScoreEntryModule', score=i + 1, timeInSeconds=int(s)) for i, s in enumerate(G.get('sureler', []))]
        return [('PlutusPointsUpdateCommand', dict(scoreEntriesList=entries, score=rec['puan']))]

    # ------------------------------------------------------------ Gauntlet of Plutus göstergesi
    def plutus_cmds(self, key, now=None):
        g = GATES.get(key, {})
        if not g.get('kural', {}).get('sure'):
            return []
        now = time.time() if now is None else now
        G = self.gate(key)
        group = [k for k, x in GATES.items() if x.get('kural', {}).get('grup') == g.get('kural', {}).get('grup')] or [key]
        done_today = any(self.gate(k).get('son_gun') == today(now) and not self.gate(k).get('hazir') for k in group)
        if G.get('hazir') and G.get('bas'):
            mode, t = PLUTUS_RUNNING, now - G['bas']                     # geçen süre
        elif done_today:
            tomorrow = datetime.datetime.combine(datetime.date.fromtimestamp(now) + datetime.timedelta(days=1), datetime.time())
            mode, t = PLUTUS_DONE, tomorrow.timestamp() - now            # yarına kalan
        else:
            mode, t = PLUTUS_OPEN, TK.time_left(g['etkinlik'], now)      # etkinliğin kalan süresi
        status = dict(_='PlutusStatusCommand', lifes=int(G.get('can', g['can'])), mode=mode, timeLeft=int(max(0, t)))
        entries = [dict(_='PlutusScoreEntryModule', score=i + 1, timeInSeconds=int(s)) for i, s in enumerate(G.get('sureler', []))]
        return [('PlutusInfoCommand', dict(playerPoints=int(self.score(key, now)['puan']), scoreEntriesList=entries, status=status,
                                           playerRanges=SR.ranges(SR.PLUTUS),          # ödül sekmesinin aralıkları (Ö1)
                                           filename=''))]


class Kosu(KAPI.Kosu):
    """Etkinlik kapısı haritasında dalgalar: kapi.Kosu, EtkinlikKapilari'nın dalga sırası, bitişi ve canlarıyla."""

    def __init__(self, ekapi, world, key):
        self.k, self.w, self.key = ekapi, world, key
        self.g = GATES[key]
        self.map = int(world.map_id)
        G = ekapi.gate(key)
        self.npcs, self.keep = set(), set()
        self.guards = set()           # kalıcı patronu koruyanlar (dalganın doğan uzaylıları; çağrılanlar değil: Plutus'un Warhead'leri)
        self.sub, self.counted, self.left, self.exposed, self.boss = 0, None, None, False, ''
        now = time.time()
        if not G['hazir'] or G['can'] <= 0:
            self.phase, self.t = 'void', now
            world.add_gate(ekapi.exit_portal(key, self.map))
        elif self.cur_map() != self.map:
            self.phase, self.t = 'void', now
            world.add_gate(ekapi.next_portal(key, self.map, self.cur_map()))
            world.add_gate(ekapi.exit_portal(key, self.map, side=True))
        else:
            self.phase, self.t = 'intro', now + KAPI.pace('giris_bekleme_sn')
            world.send(self.say('devam' if G['dalga'] else 'giris') + self.k.plutus_cmds(key, now))
        world.log('   %s: dalga %d/%d, can %d (%s)' % (self.g['ad'], G['dalga'] + 1, self.wave_count(), G['can'], self.phase))

    def messages(self):
        return dict(KAPI.K['mesajlar'], **self.g.get('mesajlar', {}))

    def points(self, n):
        """Bu kapının uzaylısı öldü (dunya.kill): türün puan aralığından etkinlik puanı (Plutus)."""
        if n.d.get('kapi') != self.key or not n.d.get('puan'):
            return []
        return self.k.add_points(self.key, random.randint(*n.d['puan']))

    def wave_count(self):
        return len(self.k.order(self.key))

    def say(self, event, **extra):
        """kapi.Kosu.say, dalga sayısı seçilen sırayla (giriş ve devamda kalan can: lifes_left)."""
        G = self.k.gate(self.key)
        n = min(G['dalga'], self.wave_count() - 1)
        vals = dict(kapi=self.g['ad'], dalga=n + 1, toplam=self.wave_count(), can=G['can'], anahtar=self.key,
                    gruplar=len(self.wave()['gruplar']), sure='')
        vals.update(extra)
        m = self.messages().get(event, {})
        out = [KAPI.screen(m[kind].format(**vals), big=kind == 'buyuk', NAME=self.g['ad'], WAVE='%d/%d' % (vals['dalga'], vals['toplam']))
               for kind in ('buyuk', 'kisa') if kind in m]
        return out + ([KAPI.stm('lifes_left', '%!', vals['can'])] if event in ('giris', 'devam') else [])

    def cur_map(self):
        return self.wave()['harita']

    def wave(self):
        G = self.k.gate(self.key)
        order = self.k.order(self.key)
        return self.g['dalgalar'][order[min(G['dalga'], len(order) - 1)]]

    def wave_msgs(self):
        return self.k.plutus_cmds(self.key)

    def sub_msgs(self):
        return []

    def spawn(self):
        """kapi.Kosu.spawn'ın etkinlik kapısı türleriyle (eg_*) olanı."""
        w, G = self.w, self.k.gate(self.key)
        wave = self.wave()
        idx = self.k.order(self.key)[G['dalga']]
        hx, hy = w.hero_pos()
        for i, count in wave['gruplar'][self.sub]:
            a = wave['uzaylilar'][i]
            ang, dist = random.uniform(0, 2 * math.pi), random.uniform(*KAPI.K['dogma_uzaklik'])
            cx = min(max(hx + math.cos(ang) * dist, 500), w.map_w - 500)
            cy = min(max(hy + math.sin(ang) * dist, 500), w.map_h - 500)
            if not a.get('kalici'):
                count = AY.adet('dalga_npc', count)            # panel: dalgalardaki uzaylı sayısı
            for x, y in KAPI.spread(cx, cy, count, w.map_w, w.map_h):
                n = w.spawn_npc_at(npc_type(self.key, idx, i), x, y, dalga=True)
                n.gate, n.engaged, n.hunt = True, True, True
                n.next_think = time.time()
                self.npcs.add(n.id)
                if a.get('kalici'):
                    self.keep.add(n.id)
                    n.invulnerable = lambda: any(j in self.w.npcs for j in self.guards)
                    self.boss = a['gorunen_ad']
                    w.send(self.say('koruma', ad=a['gorunen_ad']))
                else:
                    self.guards.add(n.id)

    def wave_done(self, now):
        G = self.k.gate(self.key)
        label = self.wave()['ad']
        with self.k.p.lock:
            G['dalga'] += 1
            self.k.p.dirty = True
        self.npcs.clear()
        self.keep.clear()
        self.guards.clear()
        with self.k.p.lock:
            G['toplam_dalga'] = G.get('toplam_dalga', 0) + 1
            self.k.p.dirty = True
        for fn in self.k.wave_hooks:
            self.w.send(fn(self.key, G['toplam_dalga']))
        if G['dalga'] >= self.wave_count() and self.g.get('kural', {}).get('sonsuz'):
            with self.k.p.lock:
                G['dalga'] = 0                      # sonsuz kapı (eski Invasion): son dalgadan sonra baştan
                self.k.p.dirty = True
        if G['dalga'] >= self.wave_count():
            self.complete()
            return
        nxt = self.cur_map()
        if nxt != self.map:
            self.w.add_gate(self.k.next_portal(self.key, self.map, nxt))
            self.w.add_gate(self.k.exit_portal(self.key, self.map, side=True))
            self.w.send(self.say('sonraki_harita', dalga=G['dalga']) + self.k.plutus_cmds(self.key))
            self.phase = 'move'
            self.w.log('   %s: dalga %s bitti; sonraki harita %s' % (self.g['ad'], label, nxt))
            return
        self.counted = None
        self.w.add_gate(self.k.exit_portal(self.key, self.map))
        self.w.send(self.say('dalga_bitti', dalga=G['dalga'], sn=KAPI.pace('dalga_molasi_sn')) + self.k.plutus_cmds(self.key))
        self.phase, self.t = 'break', now + KAPI.pace('dalga_molasi_sn')
        self.w.log('   %s: dalga %s bitti' % (self.g['ad'], label))

    def complete(self):
        k, w = self.k, self.w
        msgs, info = k.finish(self.key, w.reward_msgs)
        w.add_gate(k.exit_portal(self.key, self.map))
        msgs += self.say('tamam', sure=fmt_time(info['sure'])) + k.plutus_cmds(self.key)
        w.send(msgs)
        self.phase = 'done'

    def on_death(self):
        """Can 1 azalır; kalmazsa kapı kapanır (bekleme süresi başlar)."""
        if self.phase in ('void', 'done'):
            return None
        k, G = self.k, self.k.gate(self.key)
        with k.p.lock:
            if not AY.get('sonsuz_can'):                    # panel: kapıda can harcanmaz
                G['can'] = max(0, G['can'] - 1)
            left = G['can']
            k.p.dirty = True
        if left <= 0:
            k.end(self.key)
        self.w.send([KAPI.screen('%s: you lost a life.' % self.g['ad']), KAPI.stm('lifes_left', '%!', left)] + k.plutus_cmds(self.key))
        self.w.log('   %s: can kaybedildi, kalan %d%s' % (self.g['ad'], left, ' (kapı kapandı)' if left <= 0 else ''))
        self.before_death = self.phase
        self.phase = 'void' if left <= 0 else 'dead'
        return left
