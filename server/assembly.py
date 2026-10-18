"""Assembly (yol haritası Aşama 5): istemcinin kendi tarifleriyle (data/tarifler.json <- tools/il2cpp/istemci_verisi.py) üretim.

Akış (kayıtta giriş listesi var; üretim istekleri istemcinin kodundan):
  girişte                    AssemblyRecipeContentModule: tarifler ve durumları (Available {currentBuildCount, isNew} /
                             Build {buildAmount, remainingTimeMillis, prevBuildCount} / ReadyToCollect {prevBuildCount, buildAmount} /
                             Unavailable {type})
  AssemblyBuildRequest       {recipeLootId, targetItemId, amount}: malzemeler harcanır (envanter.py), süre başlar -> durum güncellemesi
                             (AssemblyRecipeStatusUpdateCommand); süre bitince ReadyToCollect
  AssemblyCollectRequest     sonuç x adet verilir (mağazanın ödül işlevi), durum Available ya da kullanım sınırıyla Unavailable
  AssemblyCollectAllRequest  hazır olanların hepsi
  AssemblySkipRequest        kalan süre uridyumla (dakikası 1 U, uyarlama)
  AssemblyRecipeSelectRequest  tarif görüldü (isNew kalkar)
  AssemblySetFilterRequest   pencerenin süzgeci profilde
Hangi tarifler: kayıttaki listede o gün açık olanlar (ALWAYS_VISIBLE ve takvimdeki ON_SCHEDULE; tek oyunculu: hepsi sürekli açık, süreli
olanlar da süresiz) ve ONLY_WHEN_OWNED olup tarifin kendisi depoda olanlar. Kullanım: ALWAYS_USABLE sınırsız, USABLE_ONCE bir kez,
USABLE_ONCE_PER_SCHEDULE / USABLE_LIMIT_PER_SCHEDULE günde bir / en_cok kez (tek oyunculu: takvim günü). CostScalingFactor: aynı gün
her üretimde malzemeler bu oranla artar. Gemi isteyen tarifler (Plus gemileri) Aşama 6'da.
Profilde: assembly {uretim: {tarif: {adet, bitis, onceki}}, sayac: {tarif: toplam}, gunluk: {tarif: [gün, adet]}, gorulen: [tarif],
suzgec: {}}.
"""
import json, math, os, time

import envanter as INV
import ayar as AY
import teknoloji as TK
import yukseltme as YK

HERE = os.path.dirname(os.path.abspath(__file__))
T = json.load(open(os.path.join(HERE, 'data', 'tarifler.json'), encoding='utf8'))['tarifler']
INGREDIENTS = {loot for r in T.values() for loot in r.get('parcalar', {})}      # girişte sayaçları gönderilenler (magaza.count_msgs)
ALREADY_OWNS, ALREADY_USED, ALREADY_USED_LIMIT = 0, 1, 2          # RecipeUnavailableType (istemci)
# koşulla açılan tarifler (wiki): Spartan dron tasarımı Kronos kapısı tamamlanınca
UNLOCK = {'recipe_blueprint-spartan': lambda p: ((p.d.get('kapilar') or {}).get('kapilar', {}).get('kronos') or {}).get('tamam', 0) > 0,
          'recipe_blueprint-immunizer-cpu': lambda p: True}        # Quarantine Zone tek oyunculuda kalıcı (Aşama 8)
SKIP_U_PER_MIN = 1                                                # uyarlama: kalan dakikası 1 uridyum
NO_LIMIT = 'ALWAYS_USABLE'


def event_recipes(p, now=None):
    """Etkinlik parasıyla yapılan tarifler (takvim.py 'para'): etkinlik sürerken ya da elde o paradan varken görünür."""
    import takvim as TKV
    cur = {l for k in TKV.active(now) for l in TKV.EVENTS[k].get('para', [])}
    cur |= {l for e in TKV.EVENTS.values() for l in e.get('para', []) if p.resource(l) > 0}
    return sorted(k for k, r in T.items() if r.get('gorunurluk') == 'ON_SCHEDULE' and cur & set(r.get('parcalar', {})))


def mod(name, **f):
    f['_'] = name
    return f


def today(now=None):
    return time.strftime('%Y-%m-%d', time.localtime(now or time.time()))


class Assembly:
    def __init__(self, profil, log=print):
        self.p, self.log = profil, log
        self.m = None                 # mağaza (ödül ve envanter güncellemeleri; oturum bağlar)
        self.send = None              # zamanlayıcıyla biten üretimin bildirimi (oturum bağlar)
        self.next_tick = 0.0
        self.up = YK.Yukseltme(profil, log)   # Upgrade ve Disassembly sekmeleri (yukseltme.py)

    @property
    def st(self):
        d = self.p.d.setdefault('assembly', {})
        for k, v in (('uretim', {}), ('sayac', {}), ('gunluk', {}), ('gorulen', []), ('suzgec', {})):
            d.setdefault(k, v)
        return d

    # ------------------------------------------------------------ tarifler
    def visible(self):
        """Pencerede görünen tarifler, kayıttaki sırayla; sonra depoda olan ONLY_WHEN_OWNED tarifler."""
        out = sorted((k for k, r in T.items() if 'kayitta' in r), key=lambda k: T[k]['kayitta'])
        out += sorted(k for k, r in T.items() if 'kayitta' not in r and r['gorunurluk'] == 'ONLY_WHEN_OWNED' and self.p.resource(k) > 0)
        out += [k for k, cond in UNLOCK.items() if k not in out and cond(self.p)]
        out += [k for k in event_recipes(self.p) if k not in out]
        return out

    def used_today(self, key):
        g = self.st['gunluk'].get(key)
        return g[1] if g and g[0] == today() else 0

    def limit_left(self, key):
        """Kalan kullanım (None: sınırsız)."""
        r = T[key]
        if r['kullanim'] == NO_LIMIT:
            return None
        if r['kullanim'] == 'USABLE_ONCE':
            return max(0, 1 - self.st['sayac'].get(key, 0))
        cap = 1 if r['kullanim'] == 'USABLE_ONCE_PER_SCHEDULE' else (r['en_cok'] or 1)
        return max(0, cap - self.used_today(key))

    def cost(self, key, amount):
        """Malzemeler x adet; CostScalingFactor: bugünkü her üretimde bir kat daha (1,1 …)."""
        r = T[key]
        f = r['olcek'] ** self.used_today(key) if r['olcek'] != 1 else 1
        return {loot: int(math.ceil(n * f * amount)) for loot, n in r['parcalar'].items()}

    def status(self, key, now=None):
        now = now or time.time()
        b = self.st['uretim'].get(key)
        if b:
            if now < b['bitis']:
                return mod('AssemblyRecipeBuildStatusModule', buildAmount=b['adet'], remainingTimeMillis=int((b['bitis'] - now) * 1000),
                           prevBuildCount=b['onceki'])
            return mod('AssemblyRecipeReadyToCollectStatusModule', prevBuildCount=b['onceki'], buildAmount=b['adet'])
        left = self.limit_left(key)
        if left == 0:
            kind = ALREADY_USED if T[key]['kullanim'] in ('USABLE_ONCE', 'USABLE_ONCE_PER_SCHEDULE') else ALREADY_USED_LIMIT
            return mod('AssemblyRecipeUnavailableStatusModule', type=kind)
        return mod('AssemblyRecipeAvailableStatusModule', currentBuildCount=self.build_count(key), isNew=key not in self.st['gorulen'])

    def build_count(self, key):
        """İstemcinin "Crafting Limit: <bu>/<MaxUses>" sayacı; MaxUses'a varınca Build'i kilitler. Sınırsız tariflerde MaxUses bir
        üretimin en çok adedi (U-LF-4, LF-P01 …): sayaç 0 (canlı test H32: bir üretimden sonra Build kilitleniyordu)."""
        r = T[key]
        if r['kullanim'] == NO_LIMIT:
            return 0
        if r['kullanim'] == 'USABLE_ONCE':
            return self.st['sayac'].get(key, 0)
        return self.used_today(key)

    def recipe(self, key, now=None):
        return mod('AssemblyRecipeModule', recipeLootId=key, targetItemId=0, type=mod('AssemblyRecipeRegularTypeModule'),
                   status=self.status(key, now))

    def content(self):
        """Girişteki tarif listesi (kayıttaki komutun yerine)."""
        return ('AssemblyRecipeContentModule', {'recipes': [self.recipe(k) for k in self.visible()] + self.up.recipes()})

    def update(self, key, target=0, now=None):
        return ('AssemblyRecipeStatusUpdateCommand', dict(targetItemId=target, status=self.status(key, now), lootId=key))

    # ------------------------------------------------------------ istekler
    def build(self, f):
        key, amount = f.get('recipeLootId', ''), max(1, int(f.get('amount') or 1))
        r = T.get(key)
        if not r or key not in self.visible() or key in self.st['uretim']:
            self.log('   Assembly: üretilemez %s (%s)' % (key, 'tarif yok' if not r else 'sürüyor' if key in self.st['uretim'] else 'görünmüyor'))
            return [self.update(key)] if r else []
        left = self.limit_left(key)
        if left is not None:
            amount = min(amount, left)
        if amount <= 0 or (not r['yigilir'] and amount > 1):
            amount = 1 if amount > 0 else 0
        if amount <= 0:
            return [self.update(key)]
        need = self.cost(key, amount)
        miss = INV.missing(self.p, need)
        if miss:
            self.log('   Assembly: malzeme yetmiyor %s x%d (eksik %s)' % (key, amount, miss))
            return [self.update(key)]
        removed = INV.spend(self.p, need, reason='buy_SPECIAL', detail=key)
        now = time.time()
        with self.p.lock:
            self.st['uretim'][key] = dict(adet=amount, bitis=now + AY.sure(r['sure_sn'] * amount), onceki=self.st['sayac'].get(key, 0))
            if key not in self.st['gorulen']:
                self.st['gorulen'].append(key)
            if r['kullanim'] != NO_LIMIT or r['olcek'] != 1:
                g = self.st['gunluk'].get(key)
                self.st['gunluk'][key] = [today(), (g[1] if g and g[0] == today() else 0) + amount]
            self.p.dirty = True
        self.p.ach('assembly_build', tarif=key, adet=amount)
        self.log('   Assembly: %s x%d başladı (%d sn; %s)' % (key, amount, r['sure_sn'] * amount, need))
        return INV.update_msgs(self.m, self.p, list(need), removed) + [self.update(key, f.get('targetItemId', 0))]

    def collect(self, f, now=None):
        key = f.get('recipeLootId', '')
        b = self.st['uretim'].get(key)
        now = now or time.time()
        if not b or now < b['bitis']:
            return [self.update(key)] if key in T else []
        with self.p.lock:
            del self.st['uretim'][key]
            self.st['sayac'][key] = self.st['sayac'].get(key, 0) + b['adet']
            self.p.dirty = True
        msgs = []
        for loot, n in T[key]['sonuc'].items():
            msgs += self.grant(loot, n * b['adet'])
        self.p.ach('assembly_collect', tarif=key, adet=b['adet'])
        self.log('   Assembly: %s x%d toplandı (%s)' % (key, b['adet'], T[key]['sonuc']))
        return msgs + [self.update(key, f.get('targetItemId', 0))]

    def grant(self, loot, n):
        """Sonuç: teknoloji eşyası sayaca, ötekiler mağazanın ödül işleviyle (cephane, ekipman, gemi, booster, kaynak …)."""
        if loot.startswith('tech_'):
            TK.add(self.p, loot, n)
            return INV.update_msgs(self.m, self.p, [loot])
        if self.m:
            return self.m.reward(loot, n)
        self.p.add_resource(loot, n)
        return []

    def collect_all(self, f):
        """AssemblyCollectAllRequest.allRequests: AssemblyRecipeKeyModule {lootId, targetId}."""
        msgs = []
        before = self.up_state()
        for c in f.get('allRequests') or []:
            g = dict(recipeLootId=c.get('lootId') or c.get('recipeLootId', ''), targetItemId=c.get('targetId') or c.get('targetItemId', 0))
            msgs += self.up.collect(g) if g['recipeLootId'] in YK.UP else self.collect(g)
        return msgs + ([self.content()] if self.up_state() != before else [])        # H61

    def skip(self, f):
        key = f.get('recipeLootId', '')
        b = self.st['uretim'].get(key)
        now = time.time()
        if not b or now >= b['bitis']:
            return [self.update(key)] if key in T else []
        price = max(1, int(math.ceil((b['bitis'] - now) / 60.0)) * SKIP_U_PER_MIN)
        if INV.missing(self.p, {'currency_uridium': price}):
            self.log('   Assembly: atlama için uridyum yetmiyor (%d)' % price)
            return [self.update(key)]
        INV.spend(self.p, {'currency_uridium': price}, reason='buy_SPECIAL', detail=key)
        with self.p.lock:
            b['bitis'] = now
            self.p.dirty = True
        self.log('   Assembly: %s süresi atlandı (%d U)' % (key, price))
        return INV.update_msgs(self.m, self.p, ['currency_uridium']) + [self.update(key)]

    def select(self, f):
        key = f.get('recipeLootId', '')
        if key not in T or key in self.st['gorulen']:
            return []
        with self.p.lock:
            self.st['gorulen'].append(key)
            self.p.dirty = True
        return [self.update(key)]

    def set_filter(self, f):
        with self.p.lock:
            self.st['suzgec'][str(f.get('filterType', 0))] = f.get('assemblyWindowSettingsModule') or {}
            self.p.dirty = True
        return []

    def up_state(self):
        return {k: b['bitis'] for k, b in self.up.st.items()}

    def handle(self, name, f):
        self.up.m, self.up.send, self.up.refresh = self.m, self.send, self.content
        if self.up.handles(name, f):
            before = self.up_state()
            msgs = self.up.handle(name, f)
            if self.up_state() != before:
                # hedefli yükseltme eklendi, atlandı ya da toplandı: istemci durum güncellemesini yalnız listesindeki (tarif, hedef)
                # satırına uygular ve Update/Upgrade panelini ancak tarif listesi gelince yeniden çizer (canlı test H39: Build'den
                # sonra yükseltme görünmüyordu; H61: Skip ve Collect'ten sonra panel eski sayaçta/"Collect"te kalıyordu)
                msgs = msgs + [self.content()]
            return msgs
        fn = {'AssemblyBuildRequest': self.build, 'AssemblyCollectRequest': self.collect, 'AssemblyCollectAllRequest': self.collect_all,
              'AssemblySkipRequest': self.skip, 'AssemblyRecipeSelectRequest': self.select,
              'AssemblySetFilterRequest': self.set_filter}.get(name)
        return fn(f) if fn else None

    # ------------------------------------------------------------ zaman
    def tick(self, now):
        """Saniyede bir: süresi biten üretimler hazır (istemciye ReadyToCollect)."""
        if now < self.next_tick:
            return
        self.next_tick = now + 1.0
        self.up.m, self.up.send, self.up.refresh = self.m, self.send, self.content
        self.up.tick(now)
        done = [k for k, b in self.st['uretim'].items() if not b.get('bildirildi') and now >= b['bitis']]
        for k in done:
            with self.p.lock:
                self.st['uretim'][k]['bildirildi'] = True
                self.p.dirty = True
        if done and self.send:
            self.send([self.update(k, now=now) for k in done])
