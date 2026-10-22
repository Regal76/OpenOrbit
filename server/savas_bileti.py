"""Battle Pass ve anahtar değişimi (yol haritası Aşama 7; veri data/biletler.json "savas_bileti" <- tools/biletler.py: kayıttaki
Halloween 2026 Battle Pass'i ve CDN'deki xml/events/battlepass/pass_halloween2026.xml).

Mesajlar (istemcinin kodu ve kayıt):
  giriş       BattlePassInfoCommand {filename, statusCommand BattlePassUpdateStatusCommand {questsToCollectReward [görev],
              purchased}, battlePassQuestModuleList [BattlePassQuestModule {acceptabilityStatus 2 sürüyor / 3 bitti, questDefinition}]},
              BattlePassKeyExchangeInfoCommand {rewardList, numOfKeys, exchangeType}, BattlePassWindowSettingsModule
  ilerleme    QuestConditionUpdateCommand; bitince QuestCompletedCommand ve toplanacaklar listesi (BattlePassUpdateStatusCommand)
  toplama     BattlePassCollectRequest: biten görevlerin ödülü (XML'in questReward'ı) ve Battle Pass alındıysa anahtarları (bpReward)
  değişim     BattlePassKeyExchangeRequest {exchangeReward}: anahtar (resource_battle-pass-key) harcanır, ödül verilir ->
              BattlePassKeyExchangeUpdateCommand {numOfKeys, claimCount, exchangeReward, lootId}; anahtar sayısı değişince de (kayıt)
  süzgeç      BattlePassSetFilterRequest {battlePassWindowSettingsModule}
Battle Pass etkinliğin (takvim.py: 'BattlePass' türü olan etkinlik, Halloween) süresince; anahtar değişimi de. Battle Pass mağazada
(resource_battle-pass 200.000 U): alınınca o ana dek toplanan görevlerin anahtarları da verilir (uyarlama).
Profilde: savas_bileti {donem, satin, deger, tamam, toplanacak, toplandi, degisim, suzgec}.
"""
import json, os, time

import envanter as INV
import gorev_takip as GT
import takvim as TK

HERE = os.path.dirname(os.path.abspath(__file__))
B = json.load(open(os.path.join(HERE, 'data', 'biletler.json'), encoding='utf8'))['savas_bileti']
QUESTS = {int(k): v for k, v in B['gorevler'].items()}
REWARDS = {int(k): v for k, v in B['oduller'].items()}
EXCHANGE = {r['exchangeReward']: r for r in B['anahtar_degisimi']}
KEY, PASS_ITEM = 'resource_battle-pass-key', 'resource_battle-pass'
RUNNING, DONE = 2, 3


def mod(name, **f):
    f['_'] = name
    return f


def event_key(now=None):
    """Battle Pass'i açan etkinlik ve dönemi ('halloween-2026') ya da None."""
    for k in sorted(TK.active(now)):
        if 'BattlePass' in TK.EVENTS[k].get('turler', []):
            p = TK.period(k, now)
            year = time.localtime(p[0]).tm_year if p else time.localtime(now).tm_year
            return '%s-%d' % (k, year)
    return None


class SavasBileti:
    def __init__(self, profil, log=print):
        self.p, self.log = profil, log
        self.m = None
        self.send = None
        self.map_id = None
        # istemcinin bildiği anahtar sayısı: giriş demeti (login_msgs) gönderir; None olsaydı LoginRequest sırasındaki ilk olay
        # anahtar güncellemesini giriş demetinden önce gönderiyordu
        self.keys_sent = profil.resource(KEY)

    @property
    def st(self):
        return self.p.d.setdefault('savas_bileti', {})

    def active(self, now=None):
        return event_key(now) is not None

    def ensure(self, now=None):
        ek = event_key(now)
        st = self.st
        if ek and st.get('donem') != ek:
            with self.p.lock:
                st.clear()
                st.update(donem=ek, satin=False, deger={}, tamam=[], toplanacak=[], toplandi=[], degisim={},
                          suzgec=B['ayarlar'].get('battlePassItemFilters', []))
                self.p.dirty = True
            if self.p.resource(PASS_ITEM) > 0:                       # önceden alınmış Battle Pass bu döneme
                self.p.add_resource(PASS_ITEM, -1)
                st['satin'] = True
        return ek

    # ------------------------------------------------------------ mesajlar
    def status_cmd(self):
        st = self.st
        return mod('BattlePassUpdateStatusCommand', questsToCollectReward=list(st.get('toplanacak', [])), purchased=bool(st.get('satin')))

    def info_cmd(self):
        st = self.st
        rows = [mod('BattlePassQuestModule', acceptabilityStatus=mod('QuestAcceptabilityStatusModule', type=DONE if q in st['tamam'] else RUNNING),
                    questDefinition=GT.with_state(QUESTS[q], st['deger'].get(str(q), {}), q in st['tamam'])) for q in QUESTS]
        return ('BattlePassInfoCommand', dict(filename=B['dosya'], statusCommand=self.status_cmd(), battlePassQuestModuleList=rows))

    def exchange_cmd(self):
        rows = [dict(r, claimCount=self.st.get('degisim', {}).get(k, 0)) for k, r in EXCHANGE.items()]
        return ('BattlePassKeyExchangeInfoCommand', dict(rewardList=rows, numOfKeys=self.p.resource(KEY), exchangeType=0))

    def key_update(self, reward='', count=0):
        self.keys_sent = self.p.resource(KEY)
        return ('BattlePassKeyExchangeUpdateCommand', dict(spcId=0, numOfKeys=self.keys_sent, claimCount=count, exchangeReward=reward,
                                                           lootId=KEY))

    def login_msgs(self):
        """Etkinlik süresince Battle Pass pencereleri; değilse hiçbiri (istemci Battle Pass düğmesini göstermez)."""
        if not self.ensure():
            return []
        self.keys_sent = self.p.resource(KEY)
        return [self.info_cmd(), self.exchange_cmd(), ('BattlePassWindowSettingsModule', {'battlePassItemFilters': list(self.st['suzgec'])})]

    # ------------------------------------------------------------ görevler
    def event(self, kind, **kw):
        if not self.p.d.get('savas_bileti') or not self.active():
            return []
        st, msgs, done = self.st, [], []
        for q, d in QUESTS.items():
            if q in st['tamam']:
                continue
            m, fin = GT.advance(self.p, d['rootCase'], st['deger'].setdefault(str(q), {}), kind, kw, self.map_id)
            msgs += m
            if fin:
                done.append(q)
        for q in done:
            with self.p.lock:
                st['tamam'].append(q)
                st['toplanacak'].append(q)
                self.p.dirty = True
            msgs.append(('QuestCompletedCommand', {'id': q, 'rating': 0}))
            self.p.ach('quest', id=q)
            self.log('   Battle Pass görevi bitti: %d' % q)
        if done:
            msgs.append(('BattlePassInfoCommand', self.info_cmd()[1]))
            for q in done:                                            # "N görev bitir" (Battle Pass ve Season Pass)
                msgs += self.event('objective') if kind != 'objective' else []
        if kind == 'objective':
            return msgs
        if self.p.resource(KEY) != self.keys_sent:
            msgs.append(self.key_update())
        if msgs and self.send:
            self.send(msgs)
        return msgs

    # ------------------------------------------------------------ istekler
    def keys_for(self, q):
        return REWARDS.get(q, {}).get('anahtar', 0)

    def collect(self, f=None):
        st = self.st
        if not self.ensure() or not st['toplanacak']:
            return [('BattlePassInfoCommand', self.info_cmd()[1])] if self.p.d.get('savas_bileti') else []
        msgs, keys = [], 0
        for q in list(st['toplanacak']):
            for loot, n in REWARDS.get(q, {}).get('odul', []):
                msgs += self.m.reward(loot, n) if self.m else []
            if st.get('satin'):
                keys += self.keys_for(q)
        with self.p.lock:
            st['toplandi'] += st['toplanacak']
            st['toplanacak'] = []
            self.p.dirty = True
        if keys:
            self.p.add_resource(KEY, keys)
        self.log('   Battle Pass ödülleri toplandı%s' % (' (+%d anahtar)' % keys if keys else ''))
        return msgs + [self.info_cmd(), self.key_update()]

    def grant_pass(self, n=1):
        """Mağazadan Battle Pass: bu dönem için; toplanmış görevlerin anahtarları verilir."""
        if not self.ensure():
            self.p.add_resource(PASS_ITEM, n)                        # etkinlik yokken alınırsa sonraki Battle Pass'e
            return []
        st = self.st
        if st.get('satin'):
            self.p.add_resource(PASS_ITEM, n)
            return []
        keys = sum(self.keys_for(q) for q in st['toplandi'])
        with self.p.lock:
            st['satin'] = True
            self.p.dirty = True
        if keys:
            self.p.add_resource(KEY, keys)
        self.log('   Battle Pass alındı (+%d anahtar)' % keys)
        return [self.info_cmd(), self.key_update()]

    def exchange(self, f):
        name = f.get('exchangeReward') or ''
        r = EXCHANGE.get(name)
        st = self.st
        if not r or not self.ensure():
            return []
        count = st['degisim'].get(name, 0)
        if count >= r['limit'] or INV.spend(self.p, {KEY: r['cost']}, reason='buy_SPECIAL', detail='battle_pass_' + name) is None:
            self.log('   anahtar değişimi yok: %s (%d/%d, %d anahtar)' % (name, count, r['limit'], self.p.resource(KEY)))
            return [self.key_update(name, count)]
        with self.p.lock:
            st['degisim'][name] = count + 1
            self.p.dirty = True
        msgs = []
        for x in r['listOfloot']:
            msgs += self.m.reward(x['lootId'], x['amount']) if self.m else []
        self.log('   anahtar değişimi: %s (%d anahtar)' % (name, r['cost']))
        return msgs + [self.key_update(name, count + 1)]

    def set_filter(self, f):
        mods = (f.get('battlePassWindowSettingsModule') or {}).get('battlePassItemFilters')
        if mods is not None and self.p.d.get('savas_bileti'):
            with self.p.lock:
                self.st['suzgec'] = list(mods)
                self.p.dirty = True
        return []

    def handle(self, name, f):
        fn = {'BattlePassCollectRequest': self.collect, 'BattlePassKeyExchangeRequest': self.exchange,
              'BattlePassSetFilterRequest': self.set_filter}.get(name)
        return fn(f) if fn else None
