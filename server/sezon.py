"""Season Pass (yol haritası Aşama 7; veri data/biletler.json "sezon" <- tools/biletler.py, kayıttaki pencereden).

Kayıttaki akışlar ve istemcinin mesajları:
  giriş              SeasonPassStatusCommand {pointsCost, uridiumCost (seviye başına), goldPass, extGoldPass, seasonName, marketingImage,
                     timeToEventEnd sn}, SeasonPassRewardInfoCommand (üç ödül sırası, claimed), SeasonPassMissionInfoCommand
                     {refreshInfo, missionItems [SeasonPassMissionModule {missionStatus, questDefinitionModule}]}, SeasonPointsInfoCommand
  görev ilerlemesi   QuestConditionUpdateCommand (görev motorunun biçimi); bitince "0|A|STM|sp_daily-mission-completed" (weekly, season),
                     QuestCompletedCommand {id, rating}, başarım olayı (kayıt: achievement_quest_quests_1), SeasonPointsInfoCommand
  ödül               SeasonPassRewardClaimRequest {level, goldPass, extGoldPass} -> ödül + SeasonPassRewardClaimCommand {claimed}
                     SeasonPassRewardClaimAllRequest -> alınabilen hepsi
  seviye satın alma  SeasonPassLevelPurchaseRequest {amount} -> uridyumla (uridiumCost) -> SeasonPassLevelPurchaseCommand {success}
  görev yenileme     SeasonPassRefreshRequest {questId, costType}: günlük ya da haftalık görevin yerine havuzdan başkası
Görev durumu (istemcinin MissionStatusType'ı): 0 sürüyor, 1 Gold sürüyor, 2 Gold Pass gerekir, 3 bitti, 4 Gold bitti, 5 Gold Pass
gerekir ama bitti (puanı Gold Pass alınınca gelir).
Tek oyunculu uyarlamalar: sezon takvim çeyreği (ocak, nisan, temmuz, ekim); ödül sırası ve görevler kayıttaki sezonun (her sezon aynı).
Sezon bitince alınmamış ödüller verilir (istemcinin metni: "Any unclaimed rewards from the previous season has been booked to you").
Günlük görevler (3 + 2 Gold) her gün, haftalıklar (5 + 3 Gold) pazartesi havuzdan çekilir; sezonluklar sezon boyunca. Yenileme: günde
1 ücretsiz, sonra 500 U; haftalık 500 U (kayıttaki refreshInfo). Gold Pass mağazada (resource_gold-pass 400.000 U) ya da paketten;
Extra Gold Pass Gold Pass'ten sonra.
Profilde: sezon {donem, puan, gold, ext, alinan, gun, gunluk, hafta, haftalik, deger, tamam, yenileme}.
"""
import datetime, json, os, random, time

import ayar as AY
import gorev_takip as GT
from eski_protokol import legacy

HERE = os.path.dirname(os.path.abspath(__file__))
S = json.load(open(os.path.join(HERE, 'data', 'biletler.json'), encoding='utf8'))['sezon']
COST, UCOST = S['puan_bedeli'], S['uridyum_bedeli']
MAX_LEVEL = len(COST) - 1
MISSIONS = {int(k): v for k, v in S['gorevler'].items()}
DAILY, WEEKLY, SEASON = 3, 6, 9
DAILY_N, WEEKLY_N = (3, 2), (5, 3)            # (normal, Gold) (kayıt)
REFRESH_U = 500
DONE_TEXT = {DAILY: 'sp_daily-mission-completed', WEEKLY: 'sp_weekly-mission-completed', SEASON: 'sp_season-mission-completed'}
TRACKS = (('ucretsiz', False, False), ('gold', True, False), ('ext', False, True))
GOLD_ITEM, EXT_ITEM, POINT_ITEM = 'resource_gold-pass', 'resource_ext-gold-pass', 'resource_season-pass-point'


def mod(name, **f):
    f['_'] = name
    return f


def season_id(now=None):
    t = datetime.datetime.fromtimestamp(time.time() if now is None else now)
    return '%d-Q%d' % (t.year, (t.month - 1) // 3 + 1)


def season_end(now=None):
    t = datetime.datetime.fromtimestamp(time.time() if now is None else now)
    q = (t.month - 1) // 3
    y, m = (t.year + 1, 1) if q == 3 else (t.year, q * 3 + 4)
    return datetime.datetime(y, m, 1).timestamp()


def achievement_group(now=None):
    """Bu sezonun Season Pass başarım grubu (SEASONPASS_Qn; istemcinin LevelAbsolute başarımları: "Gold Season Pass'in 50 / 80
    seviyesi"). Gerçek oyunun sezonları başlangıç ayıyla adlı (achievement_seasonpass_202608 = Q14); tek oyunculu sezon takvim
    çeyreği: bu çeyreğin başından önce başlamış en yeni sezonunki (uyarlama)."""
    import re
    import basarim as BS
    t = datetime.datetime.fromtimestamp(time.time() if now is None else now)
    start = (t.year, ((t.month - 1) // 3) * 3 + 1)
    best = None
    for aid, a in BS.ACH.items():
        m = re.match(r'achievement_seasonpass_(\d{4})(\d{2})$', aid)
        if m and (int(m.group(1)), int(m.group(2))) <= start and (best is None or m.groups() > best[0]):
            best = (m.groups(), a['grup'])
    return best[1] if best else None


def day_id(now=None):
    return datetime.date.fromtimestamp(time.time() if now is None else now).isoformat()


def week_id(now=None):
    y, w, _ = datetime.date.fromtimestamp(time.time() if now is None else now).isocalendar()
    return '%d-W%02d' % (y, w)


def level_of(points):
    total, lv = 0, 0
    for i, c in enumerate(COST):
        total += c
        if points >= total:
            lv = i
        else:
            break
    return lv


def threshold(lv):
    return sum(COST[:lv + 1])


def pool(qtype, gold):
    return sorted(q for q, m in MISSIONS.items() if m['tur'] == qtype and m['gold'] == gold)


def pick(qtype, seed, counts, exclude=()):
    rng = random.Random(seed)
    out = []
    for gold, n in zip((False, True), counts):
        cands = [q for q in pool(qtype, gold) if q not in exclude]
        out += rng.sample(cands, min(n, len(cands)))
    return out


def points_of(qid):
    return sum(r['amount'] for r in MISSIONS[qid]['tanim']['rewards'] if r['lootId'] == POINT_ITEM)


class Sezon:
    def __init__(self, profil, log=print):
        self.p, self.log = profil, log
        self.m = None              # mağaza (ödüller, para mesajları; oturum bağlar)
        self.send = None           # oturuma gönderme (görev ilerlemesi olaylardan gelir)
        self.map_id = None
        self.busy = False

    # ------------------------------------------------------------ durum
    @property
    def st(self):
        return self.p.d.setdefault('sezon', {})

    def ensure(self, now=None):
        """Sezon, gün ve hafta değiştiyse yenile -> bildirilecek mesajlar."""
        now = time.time() if now is None else now
        st, msgs = self.st, []
        sid = season_id(now)
        if st.get('donem') != sid:
            if st.get('donem'):
                msgs += self.close_season()
            with self.p.lock:
                st.clear()
                st.update(donem=sid, puan=0, gold=False, ext=False, alinan={k: [] for k, g, e in TRACKS}, deger={}, tamam=[],
                          sezonluk=pool(SEASON, False) + pool(SEASON, True), yenileme={'gun': 0, 'hafta': 0})
                self.p.dirty = True
            msgs += self.activate_items()
        if st.get('gun') != day_id(now):
            self.reset_list('gunluk', DAILY, DAILY_N, 'gun', day_id(now))
        if st.get('hafta') != week_id(now):
            self.reset_list('haftalik', WEEKLY, WEEKLY_N, 'hafta', week_id(now))
        return msgs

    def reset_list(self, key, qtype, counts, stamp_key, stamp):
        st = self.st
        with self.p.lock:
            for q in st.get(key, []):
                st['deger'].pop(str(q), None)
                if q in st['tamam']:
                    st['tamam'].remove(q)
            st[key] = pick(qtype, '%s|%s' % (st['donem'], stamp), counts)
            st[stamp_key] = stamp
            st['yenileme'][stamp_key] = 0
            self.p.dirty = True

    def missions(self):
        st = self.st
        return st.get('gunluk', []) + st.get('haftalik', []) + st.get('sezonluk', [])

    def level(self):
        return level_of(self.st.get('puan', 0))

    def status_code(self, qid):
        gold, done = MISSIONS[qid]['gold'], qid in self.st['tamam']
        if not gold:
            return 3 if done else 0
        if self.st.get('gold'):
            return 4 if done else 1
        return 5 if done else 2

    # ------------------------------------------------------------ mesajlar
    def status_cmd(self, now=None, tips=False):
        st = self.st
        return ('SeasonPassStatusCommand', dict(pointsCost=list(COST), uridiumCost=list(UCOST), goldPass=bool(st.get('gold')),
                                                showTips=tips, marketingImage=S['gorsel'], seasonName=S['ad'],
                                                extGoldPass=bool(st.get('ext')),
                                                timeToEventEnd=max(0, int(season_end(now) - (time.time() if now is None else now)))))

    def reward_cmd(self):
        al = self.st['alinan']
        rows = {}
        for key, gold, ext in TRACKS:
            rows[key] = [mod('SeasonPassRewardModule', amount=n, goldPass=gold, claimed=lv in al[key], level=lv, extGoldPass=ext, lootId=l)
                         for lv, l, n in S['odul'][key]]
        return ('SeasonPassRewardInfoCommand', dict(goldPassRewardItems=rows['gold'], freeRewardItems=rows['ucretsiz'],
                                                    extGoldPassRewardItems=rows['ext']))

    def refresh_info(self):
        y = self.st['yenileme']
        free_left = max(0, 1 - y.get('gun', 0))
        return mod('RefreshQuestInfo', nextDailyUridium=-1 if free_left else REFRESH_U, weeklyCount=0, dailyLeft=free_left, dailyCount=1,
                   nextWeeklyUridium=REFRESH_U, weeklyLeft=0)

    def mission_cmd(self):
        st = self.st
        items = [mod('SeasonPassMissionModule', missionStatus=mod('SeasonPassMissionStatusModule', type=self.status_code(q)),
                     questDefinitionModule=GT.with_state(MISSIONS[q]['tanim'], st['deger'].get(str(q), {}), q in st['tamam']))
                 for q in self.missions()]
        return ('SeasonPassMissionInfoCommand', dict(refreshInfo=self.refresh_info(), missionInfoType=0, missionItems=items))

    def points_cmd(self):
        return ('SeasonPointsInfoCommand', {'points': int(self.st.get('puan', 0))})

    def login_msgs(self):
        msgs = self.ensure()
        # showTips: istemci (UIMainCenterNewSystem.InitWindows) girişte pencereyi açar, bayrağı yalnız kendinde siler. Hiç
        # kaydedilmediği için pencere her girişte açılıyordu (canlı test H56): sezonda bir kez, ipucu yeni sezonda sıfırlanır
        tips = not self.st.get('ipucu')
        if tips:
            with self.p.lock:
                self.st['ipucu'] = True
                self.p.dirty = True
        self.level_event()                                          # başarım (eski profiller: seviye zaten 50'yi geçmiş olabilir)
        return msgs + [self.status_cmd(tips=tips), self.mission_cmd(), self.points_cmd(), self.reward_cmd()]

    # ------------------------------------------------------------ puan ve Gold Pass
    def add_points(self, n):
        old = self.level()
        with self.p.lock:
            self.st['puan'] = self.st.get('puan', 0) + n
            self.p.dirty = True
        if self.level() > old:
            self.log('   Season Pass seviyesi %d (%d puan)' % (self.level(), self.st['puan']))
            self.level_event()
            return [self.points_cmd(), self.reward_cmd()]       # ızgara yalnız ödül listesiyle açılır (canlı test H44)
        return [self.points_cmd()]

    def level_event(self):
        """Başarım: Gold Season Pass'in seviyesi (LevelAbsolute; Gold Pass yoksa 0)."""
        self.p.ach('season_level', deger=self.level() if self.st.get('gold') else 0, grup=achievement_group())

    def activate_items(self):
        """Depodaki Gold / Extra Gold Pass bu sezona (Extra yalnız Gold'dan sonra) -> mesajlar."""
        msgs = []
        st = self.st
        if not st.get('gold') and self.p.resource(GOLD_ITEM) > 0:
            self.p.add_resource(GOLD_ITEM, -1)
            with self.p.lock:
                st['gold'] = True
                self.p.dirty = True
            pend = [q for q in self.missions() if MISSIONS[q]['gold'] and q in st['tamam']]
            for q in pend:                                          # Gold Pass'ten önce biten Gold görevlerinin puanı
                msgs += self.add_points(points_of(q))
            self.log('   Gold Pass etkin (%s)%s' % (st['donem'], ', %d görevin puanı' % len(pend) if pend else ''))
            self.level_event()                                      # Gold Pass'ten önce ulaşılan seviye de sayılır
        if st.get('gold') and not st.get('ext') and self.p.resource(EXT_ITEM) > 0:
            self.p.add_resource(EXT_ITEM, -1)
            with self.p.lock:
                st['ext'] = True
                self.p.dirty = True
            self.log('   Extra Gold Pass etkin (%s)' % st['donem'])
        return msgs

    def grant(self, loot, n):
        """Mağaza ödülü: Season Pass puanı ya da Gold/Extra Gold Pass -> mesajlar."""
        self.ensure()
        if loot == POINT_ITEM:
            return self.add_points(n)
        self.p.add_resource(loot, n)
        msgs = self.activate_items()
        return msgs + [self.status_cmd(), self.mission_cmd(), self.reward_cmd(), self.points_cmd()]

    # ------------------------------------------------------------ görevler
    def event(self, kind, **kw):
        """Oyun olayı -> görev ilerlemesi (oturuma gönderilir)."""
        if self.busy or not self.p.d.get('sezon'):
            return []
        self.busy = True
        try:
            msgs = self._event(kind, kw)
        finally:
            self.busy = False
        if msgs and self.send:
            self.send(msgs)
        return msgs

    def _event(self, kind, kw):
        msgs, done = [], []
        st = self.st
        for q in self.missions():
            if q in st['tamam']:
                continue
            vals = st['deger'].setdefault(str(q), {})
            m, fin = GT.advance(self.p, MISSIONS[q]['tanim']['rootCase'], vals, kind, kw, self.map_id)
            msgs += m
            if fin:
                done.append(q)
        for q in done:
            msgs += self.complete(q)
        for q in done:                                              # sezon görevleri: N günlük/haftalık bitir
            msgs += self._event('sp_quest', dict(kategori=GT.SP_CATEGORY[MISSIONS[q]['tur']]))
        return msgs

    def complete(self, qid):
        st = self.st
        with self.p.lock:
            if qid not in st['tamam']:
                st['tamam'].append(qid)
            self.p.dirty = True
        qt = MISSIONS[qid]['tur']
        msgs = [legacy('0|A|STM|%s' % DONE_TEXT[qt]), ('QuestCompletedCommand', {'id': qid, 'rating': 0})]
        locked = MISSIONS[qid]['gold'] and not st.get('gold')
        if not locked:
            bonus = self.p.mods().get('sezon_puani', 0)                     # N.O.V.A. Bonus Hunter / Bonus Slayer (nova.py)
            msgs += self.add_points(int(round(points_of(qid) * (1 + bonus) * AY.carpan('sezon_puani'))))      # panel
        if qt == DAILY and self.m:                                          # günlük görev: Armory Token (Aşama 9; armory.py)
            import armory as AU
            msgs += self.m.reward(AU.TOKEN, AU.D['gunluk_gorev_jetonu'])
        self.p.ach('quest', id=qid)                                  # kayıt: Season Pass görevi başarımlarda sayılır
        self.log('   Season Pass görevi bitti: %d (%s, %d puan%s)' % (qid, {DAILY: 'günlük', WEEKLY: 'haftalık', SEASON: 'sezon'}[qt],
                                                                     points_of(qid), ', Gold Pass bekliyor' if locked else ''))
        return msgs

    # ------------------------------------------------------------ istekler
    def claimable(self, key, lv):
        st = self.st
        if lv > self.level() or lv in st['alinan'][key]:
            return None
        if key == 'gold' and not st.get('gold') or key == 'ext' and not st.get('ext'):
            return None
        return next(((l, n) for rlv, l, n in S['odul'][key] if rlv == lv), None)

    def give(self, key, lv):
        got = self.claimable(key, lv)
        if not got:
            return None
        with self.p.lock:
            self.st['alinan'][key].append(lv)
            self.p.dirty = True
        l, n = got
        self.log('   Season Pass ödülü: seviye %d %s: %s x%d' % (lv, key, l, n))
        return self.m.reward(l, n) if self.m else []

    def claim(self, f):
        self.ensure()
        lv = int(f.get('level') or 0)
        key = 'ext' if f.get('extGoldPass') else 'gold' if f.get('goldPass') else 'ucretsiz'
        msgs = self.give(key, lv)
        if msgs is None:
            return [legacy('0|A|STM|sp_error_no-claimable-rewards')]
        return msgs + [('SeasonPassRewardClaimCommand', dict(extGoldPass=key == 'ext', goldPass=key == 'gold', claimed=True, level=lv))]

    def claim_all(self, f=None):
        self.ensure()
        msgs, n = [], 0
        for key, gold, ext in TRACKS:
            for lv, l, a in S['odul'][key]:
                got = self.give(key, lv)
                if got is not None:
                    n += 1
                    msgs += got + [('SeasonPassRewardClaimCommand', dict(extGoldPass=ext, goldPass=gold, claimed=True, level=lv))]
        if not n:
            return [legacy('0|A|STM|sp_error_no-claimable-rewards')]
        return msgs + [self.reward_cmd()]

    def buy_levels(self, f):
        self.ensure()
        cur = self.level()
        n = max(0, min(int(f.get('amount') or 0), MAX_LEVEL - cur))
        cost = sum(UCOST[cur + 1:cur + 1 + n])
        pl = self.p.d['pilot']
        if not n or pl.get('uridium', 0) < cost:
            self.log('   Season Pass seviyesi alınamadı: %d seviye, %d U' % (n, cost))
            return [('SeasonPassLevelPurchaseCommand', {'success': False})]
        tot = self.p.gain(uridyum=-cost, neden='buy_SPECIAL', detay='season_pass_level')
        with self.p.lock:
            self.st['puan'] = max(self.st.get('puan', 0), threshold(cur + n))
            self.p.dirty = True
        self.log('   Season Pass: %d seviye alındı (%d U) -> %d' % (n, cost, self.level()))
        self.level_event()
        return ([('SeasonPassLevelPurchaseCommand', {'success': True}), self.points_cmd(), self.reward_cmd()]     # ızgara (H44)
                + (self.m.money_msgs() if self.m else []))

    def refresh(self, f):
        """SeasonPassRefreshRequest: günlük/haftalık görevin yerine havuzdan başkası (bitmiş görev yenilenmez)."""
        self.ensure()
        st, qid = self.st, int(f.get('questId') or 0)
        key = 'gunluk' if qid in st.get('gunluk', []) else 'haftalik' if qid in st.get('haftalik', []) else None
        if not key or qid in st['tamam']:
            return [self.mission_cmd()]
        stamp = 'gun' if key == 'gunluk' else 'hafta'
        free = key == 'gunluk' and st['yenileme'].get('gun', 0) < 1
        if not free:
            if self.p.d['pilot'].get('uridium', 0) < REFRESH_U:
                return [legacy('0|A|STM|not_enough_uridium'), self.mission_cmd()]
            self.p.gain(uridyum=-REFRESH_U, neden='buy_SPECIAL', detay='season_pass_refresh')
        qt, gold = MISSIONS[qid]['tur'], MISSIONS[qid]['gold']
        cands = [q for q in pool(qt, gold) if q not in st[key]]
        if not cands:
            return [self.mission_cmd()]
        new = random.choice(cands)
        with self.p.lock:
            st[key][st[key].index(qid)] = new
            st['deger'].pop(str(qid), None)
            st['yenileme'][stamp] = st['yenileme'].get(stamp, 0) + 1
            self.p.dirty = True
        self.log('   Season Pass görevi yenilendi: %d -> %d%s' % (qid, new, '' if free else ' (%d U)' % REFRESH_U))
        return [self.mission_cmd()] + ([] if free or not self.m else self.m.money_msgs())

    def close_season(self):
        """Sezon bitti: ulaşılan seviyelerin alınmamış ödülleri verilir."""
        msgs, n = [], 0
        for key, gold, ext in TRACKS:
            for lv, l, a in S['odul'][key]:
                got = self.give(key, lv)
                if got is not None:
                    msgs += got
                    n += 1
        self.log('   Season Pass sezonu bitti (%s): %d ödül verildi' % (self.st.get('donem'), n))
        return msgs + [legacy('0|A|STM|sp_season-has-ended_description')]

    def handle(self, name, f):
        fn = {'SeasonPassRewardClaimRequest': self.claim, 'SeasonPassRewardClaimAllRequest': self.claim_all,
              'SeasonPassLevelPurchaseRequest': self.buy_levels, 'SeasonPassRefreshRequest': self.refresh}.get(name)
        return fn(f) if fn else None

    def tick(self, now):
        if self.p.d.get('sezon') and (self.st.get('gun') != day_id(now) or self.st.get('donem') != season_id(now)):
            msgs = self.ensure(now) + [self.status_cmd(now), self.mission_cmd(), self.points_cmd(), self.reward_cmd()]
            if self.send:
                self.send(msgs)
