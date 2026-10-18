"""Rütbe, sayaçlar ve kayıtlar (yol haritası Aşama 3). Veri data/rutbe.json (tools/rutbe.py: uzaylı ve gemi puanları resmi
sunucunun Hall of Fame ayrıntılarından, gemi türleri istemcinin game.xml'inden, rütbeler ve formül wiki'den).

Profilde:
  sayaclar        öldürülen uzaylılar (tür başına), öldürülen oyuncu gemileri, ölümler (düşman, radyasyon, öteki), görevler
  rutbe           günlük rütbe hesabı {gun, puan, gecmis: {gün: {puan, ep, onur}}} (haftalık/aylık sıralama farkları için)
  seyir_defteri   LogbookDataCommand kayıtları (yeni önce, en çok KAYIT_SINIRI)
  hesap_gecmisi   BalanceInfoCommand kayıtları (yeni önce)

İstemci (1.1.114, araştırma: istemcinin kodu):
  - rütbe 1-21 (rang_N, gemi etiketinde rankN simgesi), 6000 yönetici, 5000 simgesi. Oyun sırasında güncelleyen mesaj yok:
    ShipInitializationCommand.dailyRank ile (giriş, harita değişimi). Gerçek oyunda günde bir hesaplanır.
  - Hall of Fame: HallOfFameTopRequest {type: TopReqType} -> HallOfFameTopDataListCommand. 17 "Rütben" sayfası (myRankingPoints:
    formülün parçaları; pages npcPointsDetails / playerPointsDetails: points x value), 18/19 ana sayfa (en iyi pilotlar/klanlar),
    4-7 EP, 8-11 onur, 0-3 ve 16 kullanıcı (rütbe puanı), 12-15 klan; HallOfFamePagesRequest {type 1-3, page} -> HallOfFamePages;
    HallOfFameDataListRequest {requested} -> etkinlik sıralamaları (etkinlik yok: boş).
  - Seyir defteri: LogbookDataListRequest {startIndex: 0'dan sayfa} -> 12'şer kayıt; infoText istemcide çevrilir
    (kill_npcID_<kimlik>, experience_points_<n>, honour_points_<n>, received_item, killed_by_npc_<kimlik>, killed_by_radiation …).
  - Hesap geçmişi: BalanceInfoListRequest {page: 1'den} -> amountType GOLD/PEARL _PLUS/_MINUS, description istemcinin anahtarı
    (bonus_abschussAlien, quest_won, buy_BATTERY_id …; internalInfo eşya, infoText adet).
Tek oyunculu uyarlama: şirkette başka oyuncu yok; rütbe puan eşiklerine göre, Hall of Fame listelerinde yalnız oyuncu (klan
listelerinde oyuncunun tek kişilik klanı, Aşama 10; puanı oyuncunun rütbe puanı).
"""
import json, math, os, time

HERE = os.path.dirname(os.path.abspath(__file__))
R = json.load(open(os.path.join(HERE, 'data', 'rutbe.json'), encoding='utf8'))
F = R['formul']
KAYIT_SINIRI = 500
DEFTER_SAYFA = 12                  # istemcinin sayfa boyu
HESAP_SAYFA = 25
NPC_SAYFA = 250                    # kayıttaki npcPointsDetails sayfaları
TOP = {'exp': (4, 5, 6, 7), 'onur': (8, 9, 10, 11), 'puan': (0, 1, 2, 3, 16), 'klan': (12, 13, 14, 15, 19)}
TOP_WEEK, TOP_CLIMB, TOP_MONTH = (2, 6, 10), (3, 7, 11), (16,)
ORE_NAMES = {0: 'PROMETIUM', 1: 'ENDURIUM', 2: 'TERBIUM', 3: 'XENOMIT', 4: 'PROMETID', 5: 'DURANIUM', 6: 'PROMERIUM', 7: 'SEPROM',
             8: 'PALLADIUM'}


def stamp(t=None):
    return time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(t)) + '.0'


def today(t=None):
    return time.strftime('%Y-%m-%d', time.localtime(t))


# ------------------------------------------------------------ sayaçlar
def counters(p):
    c = p.d.setdefault('sayaclar', {})
    done = len((p.d.get('gorevler') or {}).get('tamam', []))          # sayaçlardan önce bitirilen görevler de sayılır
    for k, v in (('npc', {}), ('oyuncu', {}), ('olum_dusman', 0), ('olum_radyasyon', 0), ('olum_diger', 0), ('gorev', done),
                 ('dost', 0), ('phoenix', 0)):
        c.setdefault(k, v)
    return c


def event(p, kind, **kw):
    """Oyun olayları (profil.ach; başarımlarla aynı olaylar) -> sayaçlar."""
    if kind not in ('kill', 'death', 'quest'):
        return
    with p.lock:
        c = counters(p)
        if kind == 'kill' and kw.get('avatar', 'NPC') == 'NPC' and kw.get('npc') is not None:
            c['npc'][str(kw['npc'])] = c['npc'].get(str(kw['npc']), 0) + 1
        elif kind == 'kill' and kw.get('avatar') == 'PLAYER':           # bot oyuncular (Aşama 11)
            c['oyuncu'][kw.get('gemi', '')] = c['oyuncu'].get(kw.get('gemi', ''), 0) + 1
        elif kind == 'death':
            k = {'RADIATION': 'olum_radyasyon', 'NPC': 'olum_dusman', 'PLAYER': 'olum_dusman'}.get(kw.get('neden'), 'olum_diger')
            c[k] += 1
        elif kind == 'quest':
            c['gorev'] += 1
        p.dirty = True


# ------------------------------------------------------------ rütbe puanı
def days_registered(p, now=None):
    try:
        t0 = time.mktime(time.strptime(p.d.get('olusturma', ''), '%Y-%m-%d %H:%M:%S'))
    except ValueError:
        return 0
    return max(0, int(((now or time.time()) - t0) // 86400))


def ship_type(p):
    return R['gemi_turu'].get(p.ship()['lootId'], 1)


def npc_points(p):
    return sum(R['npc_puan'].get(k, {}).get('puan', 0) * n for k, n in counters(p)['npc'].items())


def player_points(p):
    return sum(R['gemi_puan'].get(k, {}).get('puan', 0) * n for k, n in counters(p)['oyuncu'].items())


def breakdown(p, now=None):
    """HallOfFameRankingPoints alanları (rütbe puanı formülünün parçaları, wiki) + rankPoints."""
    c, pl = counters(p), p.d['pilot']
    parts = dict(ExperiencePoints=int(pl.get('ep', 0)), honorPoints=int(pl.get('honourPoints', 0)), playerShotPoints=player_points(p),
                 yourLevel=int(pl.get('level', 1)), daysSinceRegistration=days_registered(p, now), yourShipType=ship_type(p),
                 npcShotPoints=npc_points(p), missionsCompleted=c['gorev'], friendlyPlayersDestroyed=c['dost'],
                 DestroyedByEnemies=c['olum_dusman'], DestroyedByRadiationZone=c['olum_radyasyon'], phoenixDestroyed=c['phoenix'])
    pts = (parts['ExperiencePoints'] * F['ep'] + parts['honorPoints'] * F['onur'] + parts['playerShotPoints'] * F['oyuncu']
           + parts['yourLevel'] * F['seviye'] + parts['daysSinceRegistration'] * F['gun'] + parts['yourShipType'] * F['gemi']
           + parts['npcShotPoints'] * F['npc'] + parts['missionsCompleted'] * F['gorev'] + parts['friendlyPlayersDestroyed'] * F['dost']
           + parts['DestroyedByEnemies'] * F['olum_dusman'] + parts['DestroyedByRadiationZone'] * F['olum_radyasyon']
           + parts['phoenixDestroyed'] * F['phoenix'])
    parts['rankPoints'] = max(0, int(pts))
    return parts


def rank_for(points):
    """Rütbe puanından rütbe (1-21; tek oyunculu eşikler, rutbe.json esikler)."""
    return max(i + 1 for i, t in enumerate(R['esikler']) if points >= t)


def daily_rank(p, now=None, force=False):
    """Günde bir (giriş ve harita değişiminde bakılır): rütbe hesaplanır, pilot.dailyRank'e yazılır -> yeni rütbe ya da None."""
    day = today(now)
    st = p.d.setdefault('rutbe', {})
    if st.get('gun') == day and not force:
        return None
    b = breakdown(p, now)
    rank = rank_for(b['rankPoints'])
    icon = R['kanun_disi']['simge'] if p.d['pilot'].get('honourPoints', 0) <= R['kanun_disi']['onur'] else rank
    prev = st.get('ay')
    monthly = bool(prev and prev != day[:7] and active_month(st.get('gecmis', {}), prev))
    with p.lock:
        st.update(gun=day, puan=b['rankPoints'], rutbe=rank, ay=day[:7])
        hist = st.setdefault('gecmis', {})
        hist[day] = dict(puan=b['rankPoints'], ep=int(p.d['pilot'].get('ep', 0)), onur=int(p.d['pilot'].get('honourPoints', 0)))
        for old in sorted(hist)[:-40]:
            del hist[old]
        p.d['pilot']['dailyRank'] = icon           # ShipInitializationCommand.dailyRank (profil.PILOT_FIELDS)
        p.dirty = True
    if monthly:
        p.ach('monthly_rank')                       # başarım: aylık sıralama (basarim.SERVER_SIDE)
    return icon


def active_month(hist, month):
    """Ay içinde rütbe puanı arttı mı (günlük kayıtlardan)."""
    inside = [hist[d]['puan'] for d in sorted(hist) if d.startswith(month)]
    before = [hist[d]['puan'] for d in sorted(hist) if d < month]
    return bool(inside) and max(inside) > (before[-1] if before else 0)


def _since(p, field, days, now=None):
    """Son N günde artış (günlük kayıtlardan; en eski kayıt daha yeniyse ondan)."""
    hist = p.d.get('rutbe', {}).get('gecmis', {})
    cur = breakdown(p, now)['rankPoints'] if field == 'puan' else int(p.d['pilot'].get('ep' if field == 'ep' else 'honourPoints', 0))
    limit = today((now or time.time()) - days * 86400)
    olds = [d for d in sorted(hist) if d <= limit] or sorted(hist)[:1]
    return max(0, cur - hist[olds[-1]][field]) if olds else cur


# ------------------------------------------------------------ Hall of Fame
def _row(p, rank, points, value):
    return {'_': 'HallOfFameDataCommand', 'userId': p.d['pilot'].get('userId', 0), 'rank': rank, 'time': '', 'points': int(points),
            'value': int(value), 'userName': p.d['pilot'].get('userName', '')}


def _zero_points():
    return {'_': 'HallOfFameRankingPoints', **{k: 0 for k in (
        'honorPoints', 'belowRanking', 'belowPoints', 'missionsCompleted', 'friendlyPlayersDestroyed', 'ExperiencePoints',
        'aboveRanking', 'DestroyedByEnemies', 'npcShotPoints', 'DestroyedByRadiationZone', 'yourRanking', 'yourLevel',
        'daysSinceRegistration', 'yourShipType', 'rankPoints', 'playerShotPoints', 'abovePoints', 'phoenixDestroyed')},
        'shipsCategoryName': ''}


def ranking_points(p, now=None):
    """Rütben sayfası: formülün parçaları, rütbe (yourRanking: rang_N) ve bir üst rütbe için gereken puan (abovePoints)."""
    b = breakdown(p, now)
    rank = rank_for(b['rankPoints'])
    nxt = R['esikler'][rank] if rank < len(R['esikler']) else b['rankPoints']
    loot = p.ship()['lootId']
    out = _zero_points()
    out.update(b, yourRanking=rank, aboveRanking=min(rank + 1, 21), abovePoints=max(0, nxt - b['rankPoints']),
               belowRanking=max(rank - 1, 1), belowPoints=max(0, b['rankPoints'] - R['esikler'][rank - 1]),
               shipsCategoryName=R['gemi_puan'].get(loot, {}).get('ad', loot.replace('ship_', '').title()))
    return out


def _page(page_type, rows, total=1, cur=1):
    return {'_': 'HallOfFamePages', 'pageType': page_type, 'myList': [], 'dataList': rows, 'type': 0, 'pageSize': NPC_SAYFA,
            'currentPage': cur, 'totalPage': total}


def hof_top(p, f, now=None):
    """HallOfFameTopRequest -> HallOfFameTopDataListCommand (tek oyunculu: listelerde yalnız oyuncu)."""
    t = int(f.get('type') or 0)
    out = dict(myRankingPoints=_zero_points(), type=t, allRankList=[], pages=[], myRankList=[])
    if t == 17:
        c = counters(p)
        npc = [{'_': 'HallOfFameDataCommand', 'userId': int(k), 'rank': 0, 'time': '', 'points': v['puan'],
                'value': c['npc'].get(k, 0), 'userName': v['ad']} for k, v in sorted(R['npc_puan'].items(), key=lambda kv: int(kv[0]))]
        pages = [npc[i:i + NPC_SAYFA] for i in range(0, len(npc), NPC_SAYFA)]
        ships = [{'_': 'HallOfFameDataCommand', 'userId': 0, 'rank': 0, 'time': '', 'points': v['puan'], 'value': c['oyuncu'].get(k, 0),
                  'userName': v['ad']} for k, v in R['gemi_puan'].items()]
        out.update(myRankingPoints=ranking_points(p, now),
                   pages=[_page('npcPointsDetails', pg, len(pages), i + 1) for i, pg in enumerate(pages)] + [_page('playerPointsDetails', ships)])
    elif t == 18:                                                    # ana sayfa: puan, ad, sıra; value firma simgesi
        row = _row(p, 1, breakdown(p, now)['rankPoints'], p.d['pilot'].get('factionId', 0))
        out.update(allRankList=[row], myRankList=[row])
    elif t in TOP['klan']:                                           # tek kişilik klan (klan.py): klan yoksa liste boş
        k = p.d.get('klan')
        if k:
            span = {14: 7, 15: 7}.get(t)                             # 14 haftalık, 15 yükselenler (kullanıcıdaki 2/3 gibi)
            value = _since(p, 'puan', span, now) if span else breakdown(p, now)['rankPoints']
            row = dict(_row(p, 1, value, k.get('firma', 0)), userId=k['id'], userName='[%s] %s' % (k['etiket'], k['ad']))
            out.update(allRankList=[row], myRankList=[row])
    else:
        field = 'ep' if t in TOP['exp'] else 'onur' if t in TOP['onur'] else 'puan'
        if t in TOP_WEEK + TOP_CLIMB:
            value = _since(p, field, 7, now)
        elif t in TOP_MONTH:
            value = _since(p, field, 30, now)
        else:
            value = (breakdown(p, now)['rankPoints'] if field == 'puan'
                     else int(p.d['pilot'].get('ep' if field == 'ep' else 'honourPoints', 0)))
        row = _row(p, 1, value, value)
        out.update(allRankList=[row], myRankList=[row])
    return [('HallOfFameTopDataListCommand', out)]


def hof_pages(p, f, now=None):
    """HallOfFamePagesRequest {type 1 kullanıcı, 2 EP, 3 onur; page} -> HallOfFamePages (satır: sıra, ad, puan, rütbe)."""
    t = int(f.get('type') or 1)
    pts = (breakdown(p, now)['rankPoints'] if t == 1 else int(p.d['pilot'].get('ep', 0)) if t == 2
           else int(p.d['pilot'].get('honourPoints', 0)))
    row = _row(p, 1, pts, p.d['pilot'].get('dailyRank', 1))
    return [('HallOfFamePages', dict(pageType='', myList=[row], dataList=[row], type=t, pageSize=50, currentPage=1, totalPage=1))]


HOF_EVENTS = {2: lambda p: (p.d.get('labirent') or {}).get('avlar', 0),                   # FrozenLabyrinth: Synk avları
              3: lambda p: ((p.d.get('pve') or {}).get('ebl') or {}).get('en_iyi', 0)}      # EternalGate: Eternal Black Light dalgası


def _ebl_time(p):
    t = ((p.d.get('pve') or {}).get('ebl') or {}).get('en_iyi_an')
    return time.strftime('%Y-%m-%d %H:%M', time.localtime(float(t) / 1000.0)) if t else ''


HOF_TIMES = {3: _ebl_time}          # Time sütunu: en ileri dalganın zamanı (boş görünüyordu; canlı test H76)


def hof_events(p, f):
    """HallOfFameDataListRequest {requested: istemcinin HallOfFameType'ı}: etkinlik sıralamaları. Tek oyunculu: Frozen Labyrinth
    (Synk avları) ve Eternal Gate (Eternal Black Light'ın en ileri dalgası) listelerinde yalnız oyuncu; diğerleri boş."""
    t = int(f.get('requested') or 0)
    v = HOF_EVENTS.get(t, lambda p: 0)(p)
    rows = [dict(_row(p, 1, v, v), time=HOF_TIMES.get(t, lambda p: '')(p))] if v else []
    return [('HallOfFameDataListCommand', dict(dataList=rows, type=t, pages=[], myList=rows))]


# ------------------------------------------------------------ seyir defteri
def note(p, info_text, info='', count=0, args='{}', quest=0, done=0, t=None):
    """Seyir defterine kayıt (yeni en üstte)."""
    with p.lock:
        lst = p.d.setdefault('seyir_defteri', [])
        lst.insert(0, dict(quest=quest, info=info, args=args, count=int(count), insertDate=stamp(t), questDone=done, infoText=info_text))
        del lst[KAYIT_SINIRI:]
        p.dirty = True


def note_kill(p, npc_id, ep, onur):
    """Uzaylı öldürme: istemcide alt alta "… imha ettin", "XXX TP kazandın", "XXX Şeref Puanı kazandın" (kayıttaki sıra)."""
    if onur:
        note(p, 'honour_points_%d' % onur)
    if ep:
        note(p, 'experience_points_%d' % ep)
    note(p, 'kill_npcID_%s' % npc_id)


def logbook(p, f):
    """LogbookDataListRequest {startIndex: sayfa (0'dan)} -> LogbookDataListCommand (12'şer)."""
    lst = p.d.get('seyir_defteri', [])
    page = max(0, int(f.get('startIndex') or 0))
    rows = [dict(e, _='LogbookDataCommand') for e in lst[page * DEFTER_SAYFA:(page + 1) * DEFTER_SAYFA]]
    return [('LogbookDataListCommand', dict(startIndex=page, total=len(lst), list=rows))]


# ------------------------------------------------------------ hesap geçmişi
CUR = {'kredi': 'GOLD', 'credits': 'GOLD', 'uridyum': 'PEARL', 'uridium': 'PEARL'}


def money(p, cur, amount, description, internal='', qty=0, t=None):
    """Para hareketi kaydı: cur kredi/uridyum (ya da credits/uridium), amount eksiyse harcama."""
    amount = int(amount)
    if not amount or cur not in CUR:
        return
    with p.lock:
        lst = p.d.setdefault('hesap_gecmisi', [])
        lst.insert(0, dict(internalInfo=internal, insertDate=stamp(t), amountType='%s_%s' % (CUR[cur], 'PLUS' if amount > 0 else 'MINUS'),
                           amount=abs(amount), infoText=int(qty), description=description, userId=p.d['pilot'].get('userId', 0)))
        del lst[KAYIT_SINIRI:]
        p.dirty = True


# Eski kayıtların açıklamaları -> istemcinin doğru gösterdiği anahtar (canlı test H27; kontrol kanalıyla tek tek denendi):
# _id'li buy_* metinlerinde %ITEMNAME%/%AMOUNT% ham kalıyor, _id'siz olanlar "(adet)" ekliyor (kayıttaki "buy_BATTERY" gibi).
# İstemcide karşılığı olmayan anahtar "Extra purchased" görünüyordu (kazançta da).
DESC_FIX = {'buy_BATTERY_id': 'buy_BATTERY', 'buy_MINES_id': 'buy_MINES', 'buy_EMP_id': 'buy_EMP', 'buy_ROCKET_id': 'buy_ROCKET',
            'buy_LASER_id': 'buy_LASER', 'buy_ROCKETLAUNCHER_id': 'buy_ROCKETLAUNCHER', 'buy_ROBOT_id': 'buy_ROBOT',
            'buy_CPU_id': 'buy_CPU', 'log_purchased_drone_formation_id': 'buy_SPECIAL', 'buy_DRONE_id': 'buy_DRONE',
            'buy_BOOSTER_id': 'buy_BOOSTER', 'buy_ORE_id': 'buy_ORE', 'buy_SPECIAL_id': 'buy_SPECIAL',
            'auction_book_back_money': 'auction_bookMoneyBack', 'uridium_bank': 'title_uridium_bank',
            'payout': 'clan_hl_auszahlungen', 'gg_reward': 'galaxy_gate_done', 'captain_roster_full': 'aktion_system_back'}


def balance(p, f):
    """BalanceInfoListRequest {page: 1'den} -> BalanceInfoListCommand."""
    lst = p.d.get('hesap_gecmisi', [])
    pages = max(1, math.ceil(len(lst) / HESAP_SAYFA))
    page = min(max(1, int(f.get('page') or 1)), pages)
    rows = [dict(e, _='BalanceInfoCommand', description=DESC_FIX.get(e.get('description'), e.get('description')))
            for e in lst[(page - 1) * HESAP_SAYFA:page * HESAP_SAYFA]]
    return [('BalanceInfoListCommand', dict(page=page, pageCount=pages, list=rows))]


def buy_desc(loot):
    """Satın almanın hesap geçmişindeki açıklaması (istemcinin buy_* anahtarları; adet infoText'ten "(5)" olarak eklenir)."""
    if loot.startswith('ammunition_laser_'):
        return 'buy_BATTERY'
    if loot.startswith('ammunition_mine_'):
        return 'buy_MINES'
    if loot.startswith('ammunition_specialammo_emp'):
        return 'buy_EMP'
    if loot.startswith(('ammunition_rocket', 'ammunition_specialammo_')):
        return 'buy_ROCKET'
    if loot.startswith('equipment_weapon_laser_'):
        return 'buy_LASER'
    if loot.startswith('equipment_weapon_rocketlauncher_'):
        return 'buy_ROCKETLAUNCHER'
    if loot.startswith('equipment_generator_'):
        return 'buy_GENERATOR'
    if loot.startswith('equipment_extra_repbot'):
        return 'buy_ROBOT'
    if loot.startswith('equipment_extra_cpu_'):
        return 'buy_CPU'
    if loot.startswith('drone_formation_'):
        return 'buy_SPECIAL'
    if loot.startswith('drone_'):
        return 'buy_DRONE'
    if loot.startswith('booster_'):
        return 'buy_BOOSTER'
    if loot.startswith('resource_ore_'):
        return 'buy_ORE'
    if '_design_' in loot:
        return 'buy_SHIPMODEL'
    if loot.startswith('ship_'):
        return 'buy_SHIP'
    return 'buy_SPECIAL'


def sell_desc(loot):
    if loot.startswith('ammunition_laser_'):
        return 'sell_batteries'
    if loot.startswith(('ammunition_rocket', 'ammunition_mine_', 'ammunition_specialammo_')):
        return 'sell_rockets'
    if loot.startswith('equipment_weapon_laser_'):
        return 'sell_laser'
    if loot.startswith('equipment_weapon_rocketlauncher_'):
        return 'sell_rocketlauncher'
    if loot.startswith('equipment_generator_'):
        return 'sell_generator'
    if loot.startswith('equipment_extra_repbot'):
        return 'sell_robot'
    if loot.startswith('drone_designs_'):
        return 'sell_drone_designs_%s' % loot.split('_')[-1]
    if loot.startswith('drone_'):
        return 'sell_drone'
    return 'sell_special'


def ore_desc(ore_type):
    return 'sellOre_%s' % ORE_NAMES.get(int(ore_type), str(ore_type))
