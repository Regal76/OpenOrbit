"""Harita etkinlikleri (yol haritası Aşama 7; veri data/etkinlikler.json "harita", uzaylılar npc.json etk_* <- tools/etkinlik_uzaylilari.py).

Takvimde etkin bir etkinliğin harita bölümü bu haritanın sınıfını (X-2 … X-8, 4-4 …) kapsıyorsa:
  - etkinlik uzaylıları haritaya eklenir ('uzaylilar': tür ve adet; "{x}" harita sınıfının sürümü: etk_curcubitor_x5); ölünce yeniden
    doğarlar, etkinlik bitince doğmazlar
  - çağırma kotası ('kota'): bu kadar etkinlik uzaylısı ölünce patronlar ('patron': türler, adet, süre; 'sirayla': türler sırayla)
    doğar; süresinde öldürülmezse kaçarlar (istemcinin metni: msg_curcubitor_ran_away / npc_event_boss_ran_away)
  - gösterge ('bilgi'): NpcEventInfoCommand / AgatusEventInfoCommand {textKey (istemcinin metinleri: curcubitor, agatusbreach,
    npc_valentine, npc_chaos-protegit), npcID, bossInfo {bossCount, leftToKill}, timeInfo {timeToNextSpawn, timeToEndSpawn sn}}
  - düşmeler ('dusme': tür -> {lootId: [en az, en çok]}; etkinlik parası kaynak deposuna, ganimet günlüğünde) ve Curcubitor'un
    "Trick or Treat"i: ölünce ya Trick ('hile': olasılık; toplanamayan DDM-01 uzaylı mayını, kurulunca yakındaysan canın %20'si) ya da
    Treat (kutu_dusme'deki sandık), ikisi birden değil. 2026-10-18'e dek ikisi bağımsızdı: mayın sandığın altında kalıyor, sandığı
    toplarken patlıyordu (kullanıcı bildirimi)
  - kargo kutusu olmayan uzaylılar ('kargo_yok': temel türler; Curcubitor ve Boss Curcubitor yalnız sandıklarını düşürür) -> no_cargo
  - çağıranlar ('cagir' ya da patronun 'cagir'ı): canlıyken aralıkla yanına uzaylı çağırır (Agatus -> Spinel, Ice Meteoroid -> Icy)
  - av kutuları ('kutular': istemcinin kutu türü, adet, içerik, yeniden doğma) ve uzaylının düşürdüğü kutular ('kutu_dusme': tür ->
    {kutu türü, olasılık, içerik}; etkinlik türleri ve haritanın sıradan uzaylıları, ör. Empyrian'da Luminium); anahtarsız, P.E.T. de
    toplar; içerik açılınca: 'kesin' satırların hepsi, 'icerik'ten 'biri' ağırlıkla bir ödül ya da 'hepsi' her biri kendi olasılığıyla
    ([lootId, adet ya da [en az, en çok], olasılık %]); NPC türünün kendi 'kutu'su da (etkinlik kapıları)
  - gezgin uzaylı (etkinliğin 'gezgin'i, tek ya da liste: Hitac 2.5 ve E8'den Hitac 2.0): rotadaki haritalarda sırayla sure_sn
    kalır, oyuncu o haritadaysa belirir, süresi dolunca sonraki haritaya geçer; öldürülünce bekleme_sn sonra rotanın başından
    (oturum boyunca)
"""
import math, random, time

import harita as H
import takvim as TK
import ayar as AY
from eski_protokol import legacy
from kapi import screen

TRICK_MINE = 'ammunition_mine_ddm-01'
BOSS_TEXT = {'curcubitor': ('curcubitor_boss_spawn', 'msg_curcubitor_ran_away'), 'agatusbreach': ('agatusbreach_boss_spawn', None),
             'npc_valentine': ('npc_valentine_boss_spawn', None), 'npc_hitacAssault': ('npc_hitacAssault_boss_spawn', None)}


def mod(name, **f):
    f['_'] = name
    return f


def specs(now=None):
    """Etkin etkinliklerin şu an açık harita bölümleri: [(etkinlik, bölüm)] (bölümün dönemleri ve doğuş saatleri: takvim.window;
    zorla açılan etkinlikte hepsi)."""
    out = []
    for k in sorted(TK.active(now)):
        e = TK.EVENTS[k]
        for s in ([e['harita']] if 'harita' in e else []) + e.get('harita_ek', []):
            if TK.forced(k) or TK.window(s, now):
                out.append((k, s))
    return out


def roll(spec):
    """Kutu içeriği -> [(lootId, adet)]: 'kesin' satırların hepsi, 'icerik'ten 'mod'a göre."""
    rows = spec.get('icerik', [])
    amount = lambda a: random.randint(*a) if isinstance(a, list) else a
    out = [(l, amount(a)) for l, a, *c in spec.get('kesin', [])]
    if spec.get('mod', 'biri') == 'hepsi':
        return out + [(l, amount(a)) for l, a, *c in rows if random.random() * 100 < (c[0] if c and c[0] is not None else 100)]
    weights = [(c[0] if c and c[0] is not None else 1) for l, a, *c in rows]
    if not rows or sum(weights) <= 0:
        return out
    l, a, *c = random.choices(rows, weights)[0]
    return out + [(l, amount(a))]


ROVER = {}                         # gezgin (rovers) -> rotasının başlangıcı (öldürülünce bekleme sonrası)
NO_CARGO = {b for e in TK.EVENTS.values() for s in ([e['harita']] if 'harita' in e else []) + e.get('harita_ek', [])
            for b in s.get('kargo_yok', [])}          # etkinlik bitse de: o türün uzaylısı hiç kargo kutusu düşürmez


def no_cargo(n):
    """Bu uzaylı kargo kutusu düşürmez mi (etkinlik verisinin 'kargo_yok'u; Curcubitor yalnız sandığını düşürür)."""
    return base(n.tip) in NO_CARGO


def rovers(k):
    """Etkinliğin gezginleri [(ROVER anahtarı, gezgin)]: ilki etkinliğin adıyla, ötekiler 'ad#sıra'."""
    g = TK.EVENTS[k].get('gezgin') or []
    return [(k if i == 0 else '%s#%d' % (k, i), x) for i, x in enumerate(g if isinstance(g, list) else [g])]


def route_at(k, g, now):
    """Gezginin şu an bulunduğu harita (bekleme sürerken None)."""
    start = ROVER.setdefault(k, now)
    if now < start:
        return None
    return g['rota'][int((now - start) // g['sure_sn']) % len(g['rota'])]


def fmt(t, mc):
    return t.replace('{x}', mc.lower().replace('-', ''))


def base(tip):
    """etk_curcubitor_x5 -> etk_curcubitor."""
    head, _, tail = tip.rpartition('_')
    return head if tail[:1] == 'x' and tail[1:].isdigit() else tip


class HaritaEtkinlik:
    def __init__(self, w):
        self.w = w
        self.mc = H.map_class(w.map_id)
        self.st = {}                   # etkinlik -> {sayac, patron [kimlik], bitis, sira}
        self.calls = {}                # çağıran uzaylı kimliği -> sonraki çağırma
        self.next_tick = 0.0

    def here(self, now=None):
        return [(k, s) for k, s in specs(now) if self.mc in s['haritalar']]

    def state(self, k):
        return self.st.setdefault(k, dict(sayac=0, patron=[], bitis=None, sira=0))

    def minion_types(self, s):
        return [fmt(u['tur'], self.mc) for u in s.get('uzaylilar', [])]

    def active_type(self, tip, now=None):
        """Bu etkinlik türü şu an doğabilir mi (etkinlik sürüyor ve bu haritada)."""
        return any(tip in self.minion_types(s) for k, s in self.here(now))

    # ------------------------------------------------------------ kurulum ve gösterge
    def box_spec(self, tip, now=None):
        return next((b for k, s in self.here(now) for b in s.get('kutular', []) if b['tur'] == tip), None)

    def spawn_box(self, tip):
        """Av kutusu: rastgele yerde, süresiz; toplanınca yeniden_sn sonra yenisi (etkinlik sürüyorsa)."""
        spec = self.box_spec(tip)
        if not spec:
            return None
        x, y = self.w.random_spot()
        h = self.w.drop_box(tip, x, y, None, None)
        self.w.boxes[h]['etk'] = spec
        return h

    def setup(self):
        """Harita açılınca (ya da etkinlik başlayınca): eksik etkinlik uzaylıları ve av kutuları."""
        w = self.w
        for k, s in self.here():
            for b in s.get('kutular', []):
                have = sum(1 for x in w.boxes.values() if x['tip'] == b['tur'] and x.get('etk'))
                for _ in range(max(0, AY.adet('kutu_bolluk', b.get('adet', 1)) - have)):
                    self.spawn_box(b['tur'])
            for u in s.get('uzaylilar', []):
                tip = fmt(u['tur'], self.mc)
                if tip not in w.CFG_TYPES:
                    continue
                have = sum(1 for n in w.npcs.values() if n.alive and n.tip == tip)
                for _ in range(max(0, AY.adet('npc_sayi', u['adet']) - have)):
                    w.spawn_npc(tip, announce=True)

    def info_msgs(self, now=None):
        now = time.time() if now is None else now
        msgs = []
        for k, s in self.here(now):
            b = s.get('bilgi')
            if not b:
                continue
            st = self.state(k)
            kota = s.get('kota', {}).get(self.mc, 0)
            alive = [i for i in st['patron'] if i in self.w.npcs and self.w.npcs[i].alive]
            agatus = b['komut'] == 'AgatusEventInfoCommand'
            pre = 'AgatusEvent' if agatus else 'NpcEvent'
            msgs.append((b['komut'], dict(
                textKey=b['metin'], type=0, npcID=b['npc'],
                bossInfoCommand=mod(pre + 'BossInfoCommand', bossCount=len(alive), leftToKill=max(0, kota - st['sayac']) if kota else 0),
                timeInfoCommand=mod(pre + 'TimeInfoCommand', timeToNextSpawn=0, timeToEndSpawn=TK.time_left(k, now)))))
        # etkinliğin olmadığı haritada da gösterge (Ö1, canlı test): patron ve kalan öldürme 0 -> istemci "There are no %NPC% on this
        # map" yazar (NpcEventUIData.UpdateDescriptions); göndermeyince pencere boş açılıyordu
        sent = {(c, f['textKey']) for c, f in msgs}
        for k, s in specs(now):
            b = s.get('bilgi')
            if not b or (b['komut'], b['metin']) in sent:
                continue
            sent.add((b['komut'], b['metin']))
            pre = 'AgatusEvent' if b['komut'] == 'AgatusEventInfoCommand' else 'NpcEvent'
            msgs.append((b['komut'], dict(textKey=b['metin'], type=0, npcID=b['npc'],
                                          bossInfoCommand=mod(pre + 'BossInfoCommand', bossCount=0, leftToKill=0),
                                          timeInfoCommand=mod(pre + 'TimeInfoCommand', timeToNextSpawn=0,
                                                              timeToEndSpawn=TK.time_left(k, now)))))
        return msgs

    # ------------------------------------------------------------ olaylar
    def on_kill(self, n, x, y, now=None, w=None, pay=None):
        """w: öldüren dünya (ortak haritada self.w lider; düşmeler ve ek ödüller öldürenin). pay: ödülü paylaşanların dünyaları
        (öldüren dahil; grup: dunya.paydaslar): düşen kutular ve ek ödüller her birine kendi şansıyla, grupta kutu sahibinin."""
        w = w or self.w
        pay = pay or [w]
        sahip = lambda v: v.hid if len(pay) > 1 else None
        kt = n.d.get('kutu')                   # türün kutusu (etkinlik kapıları: dalga kutusu, Plutus'un paketi, Synk'in kutusu)
        for v in pay:
            if kt and random.random() < AY.chance('dusme', kt.get('olasilik', 1.0)):
                h = v.drop_box(kt['tur'], x, y, None, kt.get('omur_sn', 300), sahip(v))
                v.boxes[h]['etk'] = kt
        now = time.time() if now is None else now
        b, msgs = base(n.tip), []
        trick = (n.tip.startswith('etk_') and w.items is not None
                 and random.random() < max([s.get('hile', {}).get(b, 0) for k, s in self.here(now)] or [0]))
        if trick:                                                       # Trick: sandık yerine toplanamayan mayın
            w.items.alien_mine(TRICK_MINE, x, y, n.id, now)
        for k, s in self.here(now):
            kd = s.get('kutu_dusme', {}).get(b)
            for v in pay if kd and not trick else ():
                if random.random() < AY.chance('dusme', kd.get('olasilik', 1.0)):    # uzaylının kutusu (Treat …)
                    h = v.drop_box(kd['tur'], x, y, None, kd.get('omur_sn', 300), sahip(v))
                    v.boxes[h]['etk'] = kd
        for rk, g in [r for k in sorted(TK.active(now)) for r in rovers(k)]:
            if n.tip == g['tur']:
                ROVER[rk] = now + g.get('bekleme_sn', 1800)
                msgs.append(screen('key:msg_summoning_boss_killed', big=True, NPC_NAME=n.d['ad']))      # "… Another will arrive soon!"
                w.log('   gezgin %s yok edildi (%s)' % (n.d['ad'], rk))
        if not n.tip.startswith('etk_'):
            return msgs
        for k, s in self.here(now):
            st = self.state(k)
            drops = s.get('dusme', {}).get(b)
            if drops:
                msgs += w.extra_loot(n, drops)
                for v in pay:
                    if v is not w:
                        v.send(v.extra_loot(n, drops))
            if n.id in st['patron']:
                st['patron'].remove(n.id)
                if not st['patron']:
                    st['bitis'] = None
                    w.log('   etkinlik patronları yok edildi (%s)' % k)
                msgs += self.info_msgs(now)
            elif n.tip in self.minion_types(s) and s.get('kota', {}).get(self.mc) and not st['patron']:
                st['sayac'] += 1
                if st['sayac'] >= s['kota'][self.mc]:
                    msgs += self.summon(k, s, now)
                msgs += self.info_msgs(now)
        self.calls.pop(n.id, None)
        return msgs

    def rover(self, now):
        """Gezgin uzaylı bu haritada mı: gelince doğar, rotada ilerleyince ayrılır."""
        w, out = self.w, []
        name = H.name(w.map_id)
        for k, rk, g in [(k, rk, g) for k in sorted(TK.EVENTS) for rk, g in rovers(k)]:
            st = self.state(k).setdefault('gezgin', {})
            alive = [i for i in st.get(rk, []) if i in w.npcs and w.npcs[i].alive]
            at = route_at(rk, g, now) if TK.is_active(k, now) else None
            if at == name and not alive and g['tur'] in w.CFG_TYPES:
                x, y = w.random_spot()
                n = w.spawn_npc_at(g['tur'], x, y)
                n.summoned = True                        # dünya yeniden doğurmaz, etkinlik bitince kalkmaz (rota yönetir)
                alive = [n.id]
                out.append(screen('key:msg_npc_spawned_map', big=True, NPC_NAME=n.d['ad'], MAP=name))
                w.log('   gezgin %s geldi (%s)' % (n.d['ad'], name))
            elif alive and at != name:
                for i in alive:
                    n = w.npcs[i]
                    for c in [c for c in n.children if c in w.npcs]:
                        w.alien.expire(w.npcs[c])
                    w.alien.expire(n)
                    out.append(screen('%s jumped to %s.' % (n.d['ad'], at or '?')))
                    w.log('   gezgin %s ayrıldı -> %s' % (n.d['ad'], at))
                alive = []
            st[rk] = alive
        return out

    def summon(self, k, s, now):
        w, st, p = self.w, self.state(k), s['patron']
        st['sayac'] = 0
        kinds = [fmt(t, self.mc) for t in p['turler']]
        if p.get('sirayla'):
            kinds = [kinds[st['sira'] % len(kinds)]]
            st['sira'] += 1
        hx, hy = w.hero_pos(now)
        for i in range(p.get('adet', 1)):
            tip = kinds[i % len(kinds)]
            if tip not in w.CFG_TYPES:
                continue
            a = random.uniform(0, 2 * math.pi)
            r = random.uniform(900, 1400)
            x = min(max(600, hx + math.cos(a) * r), w.map_w - 600)
            y = min(max(600, hy + math.sin(a) * r), w.map_h - 600)
            c = w.spawn_npc_at(tip, x, y)
            c.summoned = True
            st['patron'].append(c.id)
        st['bitis'] = now + p.get('sure_sn', 1800)
        w.log('   etkinlik patronu çağrıldı (%s): %s x%d' % (k, ', '.join(kinds), len(st['patron'])))
        first = w.npcs.get(st['patron'][0]) if st['patron'] else None
        if first:
            w.cinematic(*first.mover.pos(now))                       # sinematik giriş (Ö2; panelden kapatılabilir)
        text = BOSS_TEXT.get((s.get('bilgi') or {}).get('metin'), (None, None))[0]
        return [legacy('0|A|STM|%s' % text)] if text else []

    def tick(self, now):
        if now < self.next_tick:
            return
        self.next_tick = now + 1.0
        w, msgs = self.w, []
        here = self.here(now)
        for k, s in here:
            st = self.state(k)
            if st['patron'] and st['bitis'] and now >= st['bitis']:          # süre doldu: patronlar kaçar
                for i in st['patron']:
                    n = w.npcs.get(i)
                    if n and n.alive:
                        w.alien.expire(n)
                st['patron'], st['bitis'] = [], None
                ran = BOSS_TEXT.get((s.get('bilgi') or {}).get('metin'), (None, None))[1] or 'npc_event_boss_ran_away'
                msgs += [legacy('0|A|STM|%s' % ran)] + self.info_msgs(now)
                w.log('   etkinlik patronları kaçtı (%s)' % k)
            callers = {b: (c, False) for b, c in s.get('cagir', {}).items()}           # her zaman (Ice Meteoroid)
            if s.get('patron', {}).get('cagir'):
                for t in s['patron']['turler']:                                       # patron: saldırı altındayken (Agatus)
                    callers[base(fmt(t, self.mc))] = (s['patron']['cagir'], True)
            for n in list(w.npcs.values()):
                c, need_fight = callers.get(base(n.tip), (None, False)) if n.alive and n.tip.startswith('etk_') else (None, False)
                if not c or (need_fight and not n.engaged):
                    continue
                if now < self.calls.setdefault(n.id, now + c['aralik_sn']):
                    continue
                self.calls[n.id] = now + c['aralik_sn']
                kids = [i for i in n.children if i in w.npcs and w.npcs[i].alive]
                tip = fmt(c['tur'], self.mc)
                if tip not in w.CFG_TYPES:
                    continue
                nx, ny = n.mover.pos(now)
                for j in range(min(c['adet'], c['en_cok'] - len(kids))):
                    a = random.uniform(0, 2 * math.pi)
                    ch = w.spawn_npc_at(tip, nx + math.cos(a) * 150, ny + math.sin(a) * 150)
                    ch.summoned = True
                    ch.engaged = n.engaged
                    n.children.add(ch.id)
        msgs += self.rover(now)
        if here != getattr(self, 'last_here', None):        # etkinlik başladı/bitti: uzaylılar ve gösterge
            self.last_here = here
            keep = {fmt(u['tur'], self.mc) for k, s in here for u in s.get('uzaylilar', [])}
            for n in list(w.npcs.values()):                  # biten etkinliğin uzaylıları (saklanan harita durumundan) kalkar
                if n.alive and n.tip.startswith('etk_') and not n.summoned and n.tip not in keep and not n.engaged:
                    w.alien.expire(n)
            boxes = {b['tur'] for k, s in here for b in s.get('kutular', [])}
            for h, b in list(w.boxes.items()):                 # biten etkinliğin av kutuları
                if b.get('etk') and b['etk'].get('yeniden_sn') and b['tip'] not in boxes:
                    del w.boxes[h]
                    msgs.append(('RemoveCollectableCommand', {'collected': False, 'hash': h}))
            self.setup()
            msgs += self.info_msgs(now)
        if msgs:
            w.send(msgs)
