"""Görevler: görev listesi, bilgi, kabul/iptal, ilerleme ve ödüller (kayıttaki akışlar). Veri: data/gorevler.json (tools/gorevler.py).

Kayıttaki akışlar:
  görev vericiye yaklaşınca  QuestGiversAvailableCommand(görev verici) + QuestListCommand; uzaklaşınca boş liste
  QuestInfoRequest           -> QuestInfoCommand(tanım, puanlar)
  QuestAcceptRequest         -> QuestInitializationCommand(tanım, koşul durumları) + QuestListCommand
  ilerleme                   -> QuestConditionUpdateCommand(koşul, değer/etkin/tamam); hedefe ulaşınca önce değer, sonra tamam
                                ve sıradaki koşul etkin. "Görev vericiye dön" etkinleşince mini haritada işaret (CreateMinimapMark)
  QuestGiverApproachedRequest -> dönüş koşulu + QuestCompletedCommand + RemoveMinimapMark + ödüller + QuestListCommand
  QuestCancelRequest         -> RemoveMinimapMark + QuestCancelledCommand + QuestListCommand
Süre sınırlı görev ("sure_sn"; tanımda HASTE koşulu, değeri geçen ms): süre dolarsa ya da kısıtı bozulursa ("basarisiz": ölüm, bir
firmanın oyuncusunu vurmak) QuestFailedCommand {id} (istemci "q2_failed_quest" iletisiyle görevi kaldırır) + QuestListCommand; görev
yeniden alınabilir. Süre gerçek zamanla (oyundan çıkınca da) işler.
Liste durumları (istemcinin AcceptabilityType'ı): 0 kabul edilemez (eksik seviye/önceki görev), 1 alınabilir, 2 sürüyor, 3 tamamlandı.
Profilde: gorevler.aktif {görev: {koşul: değer}}, gorevler.tamam [görev].
"""
import copy, json, os, time
import rutbe as RT
import booster as BOOSTER

import harita as H
import kapi as KAPI

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = json.load(open(os.path.join(HERE, 'data', 'gorevler.json'), encoding='utf8'))
QUESTS = {int(k): v for k, v in DATA['gorevler'].items()}
MAX_QUESTS = DATA.get('en_cok_gorev', 4)

KILL_NPC, CARGO, COLLECT_BONUS_BOX, COLLECT_LOOT, SELL_ORE, VISIT_MAP, VISIT_QUEST_GIVER, ON_MAP = 6, 51, 55, 67, 52, 34, 62, 77
KILL_PLAYERS = 28            # PvP görevleri: olay "kill_player" (ileride bot oyuncular gönderecek)
# Ö1: eşyayı çubuğa koy (olay slot_bar: {(çubuk, öğe)}; eşleşme [çubuk, öğe] ya da [çubuk, yuva, öğe]), istasyon nesnesine git
# (olay asset: nesne türü; eşleşme [tür], 48 hangar …), Skylab modülünü seviyeye yükselt (olay skylab: modül, seviye; eşleşme
# [modül], hedef seviye). İstemcinin koşul sınıfları: PutItemInSlotBarCondition, VisitMapAssetCondition, UpdateSkylabToLevelCondition
PUT_ITEM_IN_SLOT_BAR, VISIT_MAP_ASSET, UPDATE_SKYLAB_TO_LEVEL = 70, 75, 76
HASTE = 2                    # süre sınırı gösterimi (istemci: HasteCondition, zaman biçiminde)
START = '_bas'               # etkin görevin değerlerinde başlangıç zamanı (süreli görevler)
NOT_ACCEPTABLE, NOT_STARTED, RUNNING, COMPLETED = 0, 1, 2, 3
REQ_LEVEL, REQ_PRE_QUEST = 0, 3
MARK_GIVER, MARK_TRADE = 1, 2            # işaret kimliği quest_<görev>_<n> (kayıt: dönüşte 1)


def mod(name, **f):
    f['_'] = name
    return f


def conditions(case):
    """Ağaçtaki koşullar (kimliği olanlar)."""
    for el in case['modifier']:
        c = el['condition']
        if c['id']:
            yield c
        if el['questCase']['id'] or el['questCase']['modifier']:
            yield from conditions(el['questCase'])


def evaluate(case, values, enabled=True, out=None):
    """Koşul durumları {koşul: (etkin, tamam)} ve durumun tamamlanıp tamamlanmadığı. Sıralı durumda tamamlanmamış ilk öğeden
    sonrakiler etkin değil ve hepsi gerekir; sırasızda hepsi etkin, mandatoryCount kadarı yeter."""
    out = {} if out is None else out
    done, gate = 0, enabled
    for el in case['modifier']:
        c = el['condition']
        if c['id']:
            comp = values.get(str(c['id']), 0) >= c['targetValue']
            out[c['id']] = (gate and not comp, comp)
        else:
            comp = evaluate(el['questCase'], values, gate, out)[1]
        done += comp
        if not comp and case['ordered']:
            gate = False
    need = len(case['modifier']) if case['ordered'] else (case['mandatoryCount'] or len(case['modifier']))
    return out, done >= need


def maps_for(spec, faction):
    """"own X-3" / "enemy X-5" / "any enemy map" / "4-5" / "Epsilon Gate" / "LoW" -> harita kimlikleri (oyuncunun firmasına göre;
    kapı: kapının haritaları, kapilar.json)."""
    ids = {v: k for k, v in H.NAMES.items()}
    if spec.endswith(' Gate') and spec.split()[0].lower() in KAPI.KAPI:
        return list(KAPI.KAPI[spec.split()[0].lower()]['haritalar'])
    if spec.startswith('own X-'):
        names = ['%d-%s' % (faction, spec[6:])]
    elif spec.startswith('enemy X-'):
        names = ['%d-%s' % (f, spec[8:]) for f in (1, 2, 3) if f != faction]
    elif spec == 'any enemy map':
        names = ['%d-%d' % (f, n) for f in (1, 2, 3) if f != faction for n in range(1, 9)]
    else:
        names = [spec]
    return [ids[n] for n in names if n in ids]


class Gorevler:
    def __init__(self, profil, log=print):
        self.p, self.log = profil, log
        self.map_id = None
        self.giver = None          # bu haritadaki görev verici (kimlik, x, y)
        self.trade = None          # bu haritadaki rafineri (x, y)
        self.grant = None          # (lootId, adet) -> ödül mesajları (oturum: mağaza ve dünya)
        self.marks = {}            # görev -> gösterilen işaretler
        self.send = None           # zamanlayıcının iletileri (oturum bağlar)
        self.next_tick = 0.0

    @property
    def st(self):
        return self.p.d['gorevler']

    def faction(self):
        return self.p.d['pilot'].get('factionId', 2)

    def resolve(self, matches):
        return [str(m) for x in matches for m in (maps_for(x[1:], self.faction()) if str(x).startswith('@') else [x])]

    # ------------------------------------------------------------ durum ve liste
    def values(self, qid):
        return self.st['aktif'].get(str(qid), {})

    def status(self, qid):
        """-> (durum, eksik koşullar)."""
        if qid in self.st['tamam']:
            return COMPLETED, []
        if str(qid) in self.st['aktif']:
            return RUNNING, []
        q, miss = QUESTS[qid], []
        if self.p.d['pilot'].get('level', 1) < q['seviye']:
            miss.append(mod('QuestRequirementModule', requirementType=REQ_LEVEL, minValue=q['seviye'], maxValue=0, matches=[], missingMatches=[]))
        pre = [x for x in q['onceki'] if x in QUESTS and x not in self.st['tamam']]       # oynanamayan önceki görev engel olmaz
        if pre:
            miss.append(mod('QuestRequirementModule', requirementType=REQ_PRE_QUEST, minValue=0, maxValue=len(pre), matches=[],
                            missingMatches=[mod('QuestLocalizationModule', questId=x, textKeyFoundation='') for x in pre]))
        return (NOT_ACCEPTABLE if miss else NOT_STARTED), miss

    def slim(self, qid):
        q = QUESTS[qid]
        s, miss = self.status(qid)
        return mod('QuestSlimInfoModule', questId=qid, rootCaseId=q['kok']['id'], minLevel=q['seviye'], priority=q['oncelik'],
                   types=[mod('QuestTypeModule', type=t) for t in q['turler']], icon=mod('QuestIconModule', icon=q['simge']),
                   acceptabilityStatus=mod('QuestAcceptabilityStatusModule', type=s), missingAcceptRequirements=miss,
                   textKeyFoundation='', portraitId='', star=0)

    def list_cmd(self):
        return ('QuestListCommand', {'list': [self.slim(q) for q in sorted(QUESTS)], 'onlyStarter': False, 'maxQuests': MAX_QUESTS,
                                     'maxEventQuests': 1})

    def definition(self, qid):
        q = QUESTS[qid]
        root = copy.deepcopy(q['kok'])
        vals = self.values(qid)
        flags = evaluate(root, vals)[0]
        for c in conditions(root):
            active, comp = flags[c['id']]
            c['state'].update(currentValue=min(vals.get(str(c['id']), 0), c['targetValue']), active=active, completed=comp)
            if c['type'] == HASTE:
                c['state']['currentValue'] = self.elapsed_ms(qid, c['targetValue'])
            c['matches'] = self.resolve(c['matches'])
            for s in c['subConditions']:
                s['matches'] = self.resolve(s['matches'])
        return mod('QuestDefinitionModule', id=qid, types=[mod('QuestTypeModule', type=t) for t in q['turler']], rootCase=root,
                   rewards=[mod('LootModule', lootId=l, amount=n, modifier='') for l, n in q['oduller']],
                   icons=[mod('QuestIconModule', icon=q['simge'])], textKeyFoundation='', portraitId='', star=0)

    def info(self, qid):
        if qid not in QUESTS:
            return []
        return [('QuestInfoCommand', {'definition': self.definition(qid), 'ratings': [], 'playersRating': {
            '_': 'QuestChallengeRatingModule', 'name': '', 'epppLink': '', 'rank': 0, 'rating': 0, 'diffToFirst': 0}})]

    def login_msgs(self):
        """Girişte ve harita değişiminde: etkin görevler, liste ve bu haritadaki işaretler."""
        self.marks = {}
        msgs = [('QuestInitializationCommand', {'quest': self.definition(int(q))}) for q in self.st['aktif'] if int(q) in QUESTS]
        msgs.append(self.list_cmd())
        for q in self.st['aktif']:
            if int(q) in QUESTS:
                msgs += self.mark_msgs(int(q))
        return msgs

    # ------------------------------------------------------------ işaretler
    def mark_msgs(self, qid):
        """Etkin "görev vericiye dön" / "maden sat" koşulu için mini harita işareti (kayıt: görev vericinin konumu, yanıp söner)."""
        flags = evaluate(QUESTS[qid]['kok'], self.values(qid))[0]
        want = set()
        for c in conditions(QUESTS[qid]['kok']):
            if flags[c['id']][0]:
                if c['type'] == VISIT_QUEST_GIVER and self.giver:
                    want.add(MARK_GIVER)
                elif c['type'] == SELL_ORE and self.trade:
                    want.add(MARK_TRADE)
        have = self.marks.setdefault(qid, set())
        msgs = []
        for n in sorted(want - have):
            x, y = self.giver[1:] if n == MARK_GIVER else self.trade
            msgs.append(('CreateMinimapMark', dict(count=-1, scale=1.0, uid='quest_%d_%d' % (qid, n), positionX=x, positionY=y, interval=0.5,
                                                   inverse=False, soundModule=mod('SoundTriggerModule', playSound=True, soundId=132), type=0)))
        for n in sorted(have - want):
            msgs.append(('RemoveMinimapMark', {'uid': 'quest_%d_%d' % (qid, n)}))
        self.marks[qid] = want
        return msgs

    # ------------------------------------------------------------ istekler
    def accept(self, qid):
        s = self.status(qid)[0] if qid in QUESTS else None
        if s != NOT_STARTED or len(self.st['aktif']) >= MAX_QUESTS:
            self.log('   görev alınamadı: %s (durum %s, etkin %d)' % (qid, s, len(self.st['aktif'])))
            return [self.list_cmd()]
        with self.p.lock:
            self.st['aktif'][str(qid)] = {START: time.time()} if QUESTS[qid].get('sure_sn') else {}
            self.p.dirty = True
        self.log('   görev alındı: %d %s%s' % (qid, QUESTS[qid]['ad'], ' (%d sn)' % QUESTS[qid]['sure_sn'] if QUESTS[qid].get('sure_sn') else ''))
        msgs = [('QuestInitializationCommand', {'quest': self.definition(qid)}), self.list_cmd()] + self.mark_msgs(qid)
        return msgs + self.event('map', map=self.map_id) if self.map_id is not None else msgs

    def cancel(self, qid):
        if str(qid) not in self.st['aktif']:
            return []
        with self.p.lock:
            del self.st['aktif'][str(qid)]
            self.p.dirty = True
        msgs = [('RemoveMinimapMark', {'uid': 'quest_%d_%d' % (qid, n)}) for n in sorted(self.marks.pop(qid, set()))]
        self.log('   görev iptal: %d' % qid)
        return msgs + [('QuestCancelledCommand', {'id': qid}), self.list_cmd()]

    # ------------------------------------------------------------ ilerleme
    def matches(self, c, kind, kw):
        """Olay bu koşulu ilerletiyor mu -> eklenecek miktar."""
        on_map = [s for s in c['subConditions'] if s['type'] == ON_MAP]
        if on_map and str(kw.get('map', self.map_id)) not in self.resolve(on_map[0]['matches']):
            return 0
        m = c['matches']
        if c['type'] == KILL_NPC and kind == 'kill':
            return 1 if not m or str(kw.get('npc')) in m else 0
        if c['type'] == CARGO and kind == 'cargo':
            return 1
        if c['type'] == COLLECT_BONUS_BOX and kind == 'bonus':
            return 1
        if c['type'] == COLLECT_LOOT and kind == 'loot':
            return kw['amount'] if not m or kw['loot'] in m else 0
        if c['type'] == SELL_ORE and kind == 'sell':
            return kw['amount'] if not m or str(kw['ore'] + 1) in m else 0
        if c['type'] == VISIT_MAP and kind == 'map':
            return 1 if str(kw.get('map')) in self.resolve(m) else 0
        if c['type'] == VISIT_QUEST_GIVER and kind == 'giver':
            return 1
        if c['type'] == PUT_ITEM_IN_SLOT_BAR and kind == 'slot_bar' and len(m) >= 2:
            items = set(kw.get('items', ()))
            return 1 if (m[0], m[-1]) in items and (len(m) < 3 or (m[0], m[1], m[-1]) in set(kw.get('slots', ()))) else 0
        if c['type'] == VISIT_MAP_ASSET and kind == 'asset':
            return 1 if str(kw.get('tur')) in m else 0
        if c['type'] == UPDATE_SKYLAB_TO_LEVEL and kind == 'skylab':
            return c['targetValue'] if m and kw.get('modul') == m[0] and kw.get('seviye', 0) >= c['targetValue'] else 0
        if c['type'] == KILL_PLAYERS and kind == 'kill_player':
            # eşleşme [gemi sayısı, gemiler…, firma sayısı, firmalar…] (istemci: KillPlayersCondition.ParseMatches)
            n = int(m[0]) if m else 0
            ships, rest = m[1:1 + n], m[1 + n:]
            facs = rest[1:1 + int(rest[0])] if rest else []
            if kw.get('faction') == self.faction():
                return 0
            return 1 if (not ships or str(kw.get('ship')) in ships) and (not facs or str(kw.get('faction')) in facs) else 0
        return 0

    def event(self, kind, **kw):
        """Oyun olayı (kill, cargo, bonus, loot, sell, map, giver) -> koşul güncellemeleri, işaretler, tamamlanan görevler."""
        msgs = self.broken(kind, **kw) if kind == 'kill_player' else []
        for qs in list(self.st['aktif']):
            qid = int(qs)
            if qid not in QUESTS:
                continue
            root = QUESTS[qid]['kok']
            vals = self.st['aktif'][qs]
            before = evaluate(root, vals)[0]
            changed = []
            for c in conditions(root):
                if before[c['id']][0]:
                    inc = self.matches(c, kind, kw)
                    if inc:
                        with self.p.lock:
                            vals[str(c['id'])] = min(c['targetValue'], vals.get(str(c['id']), 0) + inc)
                            self.p.dirty = True
                        changed.append(c)
            if not changed:
                continue
            after, done = evaluate(root, vals)
            ids = {c['id'] for c in changed}
            for c in conditions(root):
                v = min(vals.get(str(c['id']), 0), c['targetValue'])
                if c['id'] in ids:
                    msgs.append(self.cond_update(c['id'], v, True, False))
                if after[c['id']] != before[c['id']]:
                    msgs.append(self.cond_update(c['id'], v, *after[c['id']]))
            msgs += self.mark_msgs(qid)
            if done:
                msgs += self.complete(qid)
        return msgs

    # ------------------------------------------------------------ süre ve kısıtlar
    def elapsed_ms(self, qid, target):
        vals = self.values(qid)
        if START not in vals:
            return 0
        return int(min(target - 1, max(0, (time.time() - vals[START]) * 1000)))

    def fail(self, qid, why):
        if str(qid) not in self.st['aktif']:
            return []
        with self.p.lock:
            del self.st['aktif'][str(qid)]
            self.p.dirty = True
        msgs = [('RemoveMinimapMark', {'uid': 'quest_%d_%d' % (qid, n)}) for n in sorted(self.marks.pop(qid, set()))]
        self.log('   görev başarısız: %d %s (%s)' % (qid, QUESTS[qid]['ad'], why))
        return msgs + [('QuestFailedCommand', {'id': qid}), self.list_cmd()]

    def broken(self, kind, **kw):
        """Kısıt bozuldu mu: ölüm ya da yasak firmanın oyuncusunu vurmak -> başarısız görevlerin mesajları."""
        msgs = []
        for qs in list(self.st['aktif']):
            q = QUESTS.get(int(qs))
            for f in (q or {}).get('basarisiz', []):
                if (f['tur'] == 'olum' and kind == 'death') or (f['tur'] == 'oyuncu' and kind == 'kill_player'
                                                               and kw.get('faction') == f['firma']):
                    msgs += self.fail(int(qs), 'kısıt: %s' % f['tur'])
                    break
        return msgs

    def tick(self, now):
        """Süreli görevler: süre dolunca başarısız; değilse 5 sn'de bir süre koşulunun değeri."""
        if now < self.next_tick:
            return
        self.next_tick = now + 5.0
        msgs = []
        for qs in list(self.st['aktif']):
            q = QUESTS.get(int(qs))
            if not q or not q.get('sure_sn'):
                continue
            start = self.st['aktif'][qs].get(START, now)
            if now - start >= q['sure_sn']:
                msgs += self.fail(int(qs), 'süre doldu')
                continue
            for c in conditions(q['kok']):
                if c['type'] == HASTE:
                    msgs.append(self.cond_update(c['id'], self.elapsed_ms(int(qs), c['targetValue']), True, False))
        if msgs and self.send:
            self.send(msgs)

    @staticmethod
    def cond_update(cid, value, active, completed):
        return ('QuestConditionUpdateCommand', {'questConditionId': cid, 'state': mod(
            'QuestConditionStateModule', currentValue=value, active=active, completed=completed)})

    def complete(self, qid):
        with self.p.lock:
            self.st['aktif'].pop(str(qid), None)
            if qid not in self.st['tamam']:
                self.st['tamam'].append(qid)
            self.p.dirty = True
        self.p.ach('quest', id=qid)
        RT.note(self.p, 'quest_success_%d' % qid, quest=qid, done=1)          # seyir defteri
        if qid == 20003:
            self.p.ach('tutorial')                   # başarım: başlangıç görevleri (20000-20003) bitti
        msgs = [('QuestCompletedCommand', {'id': qid, 'rating': 0})]
        msgs += [('RemoveMinimapMark', {'uid': 'quest_%d_%d' % (qid, n)}) for n in sorted(self.marks.pop(qid, set()))]
        mult = 1 + BOOSTER.mods(self.p).get('gorev_odulu', 0)        # QR-01 / NQR-B01: görev ödülleri x2 (uridyum hariç; Ö6)
        for loot, n in QUESTS[qid]['oduller']:
            n = n if loot == 'currency_uridium' else int(n * mult)
            msgs += self.grant(loot, n) if self.grant else []
        self.log('   görev tamamlandı: %d %s (%s)' % (qid, QUESTS[qid]['ad'], ', '.join('%s x%d' % (l, n) for l, n in QUESTS[qid]['oduller'])))
        return msgs + [self.list_cmd()]
