"""Tek kişilik klan (yol haritası Aşama 10): istemcinin klan penceresi (UIClan) profilden.

Klan yoksa LoginInitClanRequest -> LoginInitMyApplyCommand (kurma bedeli 300.000 kredi; kayıt ve DarkOrbit). Kurulunca oyuncu
lider ve tek üye: gemi etiketi ShipInitializationCommand.clanTag/clanId (profil pilot alanları) ve ClanTagChangedCommand, sohbette
klan odası. Lider bütün haklara sahip; rütbelerin hakları istemcinin ClanRankInfoVo listesindeki adlar (HAKLAR).
Pencerenin bölümleri: bilgi (ad, etiket, açıklama, alım durumu, TeamSpeak adresi), haberler, klan postası (tek üye: kendine),
rütbeler, vergi oranı ve kasa (ödeme), firma (klan firması), Battle Station listesi (boş).
Bot klanlarla gelecekler (Aşama 11): başvurular, üye alma/çıkarma, liderlik devri, diplomasi, Clan Battle Station'lar; şimdilik
istemcinin kendi hata metinleriyle yanıtlanır. Vergi: tek üyede gelir yok (kasa ödemesiyle oyuncuya döner).
"""
import time

KURMA_BEDELI = 300000
HAKLAR = ['hiremember', 'firemember', 'editranks', 'news', 'roundmail', 'tax', 'payout', 'diplo_start', 'diplo_end',
          'diplo_war', 'battle_station_replace_module', 'battle_station_deflector', 'battle_station_build']      # + Ö5 (CBS)
AZAMI_VERGI = 10
REQUESTS = {'LoginInitClanRequest', 'ClanFilterSearchRequest', 'ClanSearchNameTagRequest', 'ClanListRequest', 'ShowClanInfoRequest',
            'FoundClanRequest', 'ApplyClanRequest', 'DeleteClanApplyRequest', 'ClanApplyInfoListRequest', 'ApplyAcceptRequest',
            'ApplyDeclineRequest', 'ChangeClanDescriptionRequest', 'EditClanInfoRequest', 'ChangeClanFirmaRequest',
            'ChangeClanTaxRequest', 'ClanAddNewsRequest', 'ClanNewsListRequest', 'ClanMemberListRequest', 'ClanRankListRequest',
            'ClanNewRankRequest', 'ClanDeleteRankRequest', 'EditClanRanksRequest', 'DeleteMyRankRequest', 'EditClanMemberRequest',
            'ChangeClanLeaderRequest', 'DeleteClanMemberRequest', 'ClanMessageListRequest', 'ClanSendMessageRequest',
            'ClanSendAllMessageRequest', 'ClanDeleteMessageRequest', 'ClanDeleteAllMessageRequest', 'PayoutClanRequest',
            'LeaveClanRequest', 'DeleteClanRequest', 'DelClanRequest', 'ClanReportAdminRequest', 'ClanNewDiplomacyRequest',
            'ClanDeleteDiploRequest', 'ClanDeleteOpenDiploRequest', 'ClanEditDiploOfferRequest', 'ClanBattleStationInfoRequest',
            'BattleStationHistoryListRequest', 'CompanyHierarchyRequest'}


def mod(_cls, **f):
    f['_'] = _cls
    return f


def stamp(t=None):
    return time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(t))


def err(key='empty', **args):
    from magaza import stack_msg
    return stack_msg(key, **args)


def _res(key):
    from magaza import res
    return res(key)


NEWS_KEYS = {'found': 'clan_found'}              # istemci haberi dil anahtarından kurar ("Clan founded")


class Klan:
    def __init__(self, profil, log=print):
        self.p, self.log = profil, log
        self.m = None
        self.on_change = None             # klan kuruldu/silindi: sohbet odaları, gemi etiketi (sosyal.py)
        self.cbs = None                   # Clan Battle Station (Ö5; cbs.py): istasyon sekmesi ve günlüğü

    @property
    def k(self):
        return self.p.d.get('klan')

    # -------------------------------------------------------- komutlar
    def company(self):
        """Firma bilgisi (tek oyunculu: oyuncunun kendi sayıları)."""
        pl, cnt = self.p.d['pilot'], self.p.d.get('sayaclar', {})
        return mod('CompanyDateInfoCommand', members=1, ships=sum((cnt.get('oyuncu') or {}).values()), EP=int(pl.get('ep', 0)),
                   aliens=sum((cnt.get('npc') or {}).values()), hounr=int(pl.get('honourPoints', 0)),
                   ranking=int((self.p.d.get('rutbe') or {}).get('puan', 0)))

    def hierarchy(self):
        """CompanyHierarchyRequest: firmaların klan sıralaması. Kayıttaki yanıt başka oyuncuların klan ve lider adlarını taşıyordu
        (kişisel veri; canlı test N2 -> H79). Tek oyunculu: yalnız oyuncunun klanı, kendi firmasının listesinde 1."""
        k, pl = self.k, self.p.d['pilot']
        fac = int(pl.get('factionId', 0))
        own = mod('CompanyHierarchyRankingModule', clanId=-1, rank=0, clanName='', leaderName='', cbsNamesAndLocations='',
                  rankingPoints=0)
        lists = {1: [], 2: [], 3: []}
        if k:
            own = mod('CompanyHierarchyRankingModule', clanId=k['id'], rank=1, clanName=k['ad'], leaderName=pl.get('userName', ''),
                      cbsNamesAndLocations='', rankingPoints=int((self.p.d.get('rutbe') or {}).get('puan', 0)))
            lists[int(k['firma'] or fac) if int(k['firma'] or fac) in lists else fac] = [own]
        return ('CompanyHierarchyInitializationCommand', dict(mmoRanking=lists[1], eicRanking=lists[2], vruRanking=lists[3],
                                                                ownRanking=own, ownFaction=mod('FactionModule', faction=fac)))

    def info(self):
        k, pl = self.k, self.p.d['pilot']
        return mod('ClanInfoCommand', recruitionInfo=k['alim_bilgi'], taxRate=k['vergi'], clanId=k['id'],
                   recruitionStatus=k['alim'], clanCredits=k['kasa'], teamspeakAdd=k['ts'], clanLeaderName=pl.get('userName', ''),
                   clanName=k['ad'], clanRank=1, clanIcon='', clanLeaderId=self.p.user_id, memberCount=1, clanTag=k['etiket'],
                   clanDesc=k['aciklama'], company=k['firma'], insertDate=k['kurulus'], ranking=1)

    def member(self):
        k, pl = self.k, self.p.d['pilot']
        from harita import name as map_name
        return mod('ClanMemberInfoCommand', faction=int(pl.get('factionId', 0)), mapName=map_name(self.p.d['konum'].get('mapId', 1)),
                   name=pl.get('userName', ''), maxPayout=0, insertDate=k['kurulus'], ep=int(pl.get('ep', 0)),
                   userId=self.p.user_id, ranksId=k.get('benim_rutbem', 0), rank=int(pl.get('dailyRank', 1)))

    def rank_cmd(self, r):
        return mod('ClanRankInfoCommand', rankId=r['id'], clanId=self.k['id'], rankName=r['ad'], rights=list(r['haklar']))

    def ranks(self):
        return [self.rank_cmd(r) for r in self.k['rutbeler']]

    def news_cmd(self, n):
        """İstemci (MyClanDataVo.AddNews): type "user" ise context düz metin; değilse context bir dil anahtarı (%username%,
        %clanname% değiştirilir). Kuruluş haberi istemcinin "clan_found" metni (canlı deneme 2026-10-17: ikisi de boş çıkıyordu)."""
        k = self.k
        kind, text = ('user', n['metin']) if n['tur'] in ('news', 'user') else (n['tur'], NEWS_KEYS.get(n['tur'], n['metin']))
        return mod('ClanNewsInfoCommand', type=kind, clanNewsId=n['id'], userName=n['ad'], clanId=k['id'], context=text,
                   userId=n['kim'], clanName=k['ad'], insertDate=n['tarih'])

    def mail_cmd(self, m):
        return mod('ClanMessageInfoCommand', insertDate=m['tarih'], subject=m['konu'], mailText=m['metin'], type=m.get('tur', 0),
                   sendUserId=m['kim'], textIncName='', subjectIncName='', sendUserName=m['ad'], messageId=m['id'],
                   textParams='', subjectParams='')

    def tax_cmd(self):
        return mod('ClanTaxInfoCommand', income=0, logList=[mod('ClanTaxLogCommand', **x) for x in self.k['kasa_kaydi'][:50]])

    def all_info(self):
        k = self.k
        return mod('ClanAllInfoCommand', clanMemberInfoCommandList=[self.member()], clanTaxInfoCommand=self.tax_cmd(),
                   clanDiploReqInfoCommands=[], myClanDiploReqInfoCommands=[],
                   clanApplyInfoListCommand=mod('ClanApplyInfoListCommand', applyClanInfoCommandList=[]),
                   clanMessageInfoCommands=[self.mail_cmd(m) for m in k['mesajlar']], clanDiploInfoCommands=[],
                   clanRankInfoCommands=self.ranks(), clanInfoCommand=self.info(),
                   clanNewsInfoCommands=[self.news_cmd(n) for n in k['haberler']], companyDateInfoCommand=self.company())

    def tag_cmd(self):
        k = self.k or {}
        return ('ClanTagChangedCommand', {'clanTag': k.get('etiket', ''), 'clanId': k.get('id', 0), 'userId': self.p.user_id})

    def no_clan(self):
        return ('LoginInitMyApplyCommand', {'applyClanList': [], 'foundCost': KURMA_BEDELI, 'companyDateInfoCommand': self.company(),
                                            'rejectApplyClanList': []})

    def nametag(self):
        k = self.k
        return mod('ClanNameTagInfoCommand', tag=k['etiket'], id=k['id'], name=k['ad'])

    # -------------------------------------------------------- yardımcılar
    def next_id(self, key):
        with self.p.lock:
            k = self.k
            k['sira'] = k.get('sira', 1) + 1
            self.p.dirty = True
            return k['sira']

    def add_news(self, kind, text):
        pl = self.p.d['pilot']
        n = {'id': self.next_id('haber'), 'tur': kind, 'ad': pl.get('userName', ''), 'kim': self.p.user_id, 'metin': text[:500],
             'tarih': stamp()}
        with self.p.lock:
            self.k['haberler'].insert(0, n)
            del self.k['haberler'][50:]
            self.p.dirty = True
        return n

    def set_pilot(self):
        k = self.k or {}
        with self.p.lock:
            self.p.d['pilot'].update(clanId=k.get('id', 0), clanTag=k.get('etiket', ''))
            self.p.dirty = True
        if self.on_change:
            self.on_change()

    @staticmethod
    def valid_tag(tag):
        return 1 <= len(tag) <= 4 and all(c.isalnum() or c in '-_.!?*+' for c in tag)

    # -------------------------------------------------------- istekler
    def handle(self, name, f):
        k = self.k
        if name == 'CompanyHierarchyRequest':
            return [self.hierarchy()]
        if name == 'LoginInitClanRequest':
            return [('LoginInitClanCommand', {'clanAllInfoCommand': self.all_info()})] if k else [self.no_clan()]
        if name == 'ClanFilterSearchRequest':
            lst = [self.info()] if k and self.matches(f) else []
            return [('ClanFilterSearchInfoCommand', {'list': lst, 'count': len(lst)})]
        if name == 'ClanSearchNameTagRequest':
            q = str(f.get('lookup', '')).lower()
            hit = [self.nametag()] if k and q and (q in k['etiket'].lower() or q in k['ad'].lower()) else []
            return [('ClanSearchNameTagCommand', {'lookup': f.get('lookup', ''), 'infoCommandList': hit})]
        if name == 'ClanListRequest':
            return [('ClanListCommand', {'type': int(f.get('type') or 0), 'infoCommandList': [self.nametag()] if k else []})]
        if name == 'ShowClanInfoRequest':
            ok = bool(k) and int(f.get('clanId') or 0) == k['id']
            return [('ShowClanInfoCommand', {'success': ok, 'errorMsg': err() if ok else err('err_clan_noClanID'),
                                             'clanInfoCommand': self.info() if ok else None})]
        if name == 'FoundClanRequest':
            return self.found(f)
        if name == 'ApplyClanRequest':
            return [('ApplyClanCommand', {'applyId': 0, 'credits': 0, 'errorMsg': err('err_clan_exist' if k else 'err_select_clan'),
                                          'clanId': int(f.get('clanId') or 0), 'success': False})]
        if name == 'DeleteClanApplyRequest':
            return [('DeleteClanApplyCommand', {'success': False, 'applyId': int(f.get('applyId') or 0), 'errorMsg': err('err_clan_apply')})]
        if name == 'ClanApplyInfoListRequest':
            return [('ClanApplyInfoListCommand', {'applyClanInfoCommandList': []})]
        if name == 'ClanBattleStationInfoRequest' and self.cbs:
            return [self.cbs.clan_info()]
        if name == 'BattleStationHistoryListRequest' and self.cbs:
            return [self.cbs.history(int(f.get('startIndex') or 0))]
        if name == 'ClanBattleStationInfoRequest':
            return [('ClanBattleStationInfoCommand', {'battleStationOverviewInfoCommands': [], 'stationOwnedLongestTime': '',
                                                      'maxStationAtOnce': 0, 'destroyedStations': 0, 'stations': 0, 'allStations': 0})]
        if name == 'BattleStationHistoryListRequest':
            return [('BattleStationHistoryListCommand', {'commandList': [], 'startIndex': int(f.get('startIndex') or 0), 'total': 0})]
        if not k:
            return self.no_clan_reply(name, f)
        return self.member_request(name, f)

    def matches(self, f):
        k = self.k
        q = str(f.get('lookup', '')).strip().lower()
        if q and q not in k['etiket'].lower() and q not in k['ad'].lower():
            return False
        fac = int(f.get('factionType') or 0)
        return not fac or not k['firma'] or fac == k['firma']

    def no_clan_reply(self, name, f):
        """Klansızken gelen üye istekleri: istemcinin "klanda değilsin" metni."""
        e = err('err_clan_user_not_in_clan')
        replies = {'LeaveClanRequest': ('LeaveClanCommand', {'errorMsg': e, 'success': False}),
                   'DeleteClanRequest': ('DeleteClanCommand', {'success': False, 'errorMsg': e}),
                   'DelClanRequest': ('DelClanCommand', {'success': False, 'errorMsg': e})}
        r = replies.get(name)
        self.log('   klan isteği klansız: %s' % name)
        return [r] if r else []

    def found(self, f):
        tag, cname = str(f.get('clanTag', '')).strip(), str(f.get('clanName', '')).strip()
        desc = str(f.get('clanDescription', ''))
        reply = lambda ok, key='empty', cid=0, **a: [('FoundClanCommand', {'success': ok, 'clanId': cid, 'errorMsg': err(key, **a)})]
        if self.k:
            return reply(False, 'err_user_in_clan')
        if not tag or not cname:
            return reply(False, 'clan_errmsg_required', _NAME_=_res('clan_name' if not cname else 'clan_tag'))
        if len(cname) > 50:
            return reply(False, 'clan_errmsg_to_long')
        if len(desc) > 2000:
            return reply(False, 'clan_errmsg_desc_to_long')
        if not self.valid_tag(tag):
            return reply(False, 'clan_errmsg_clantag_not_allowed')
        import envanter as INV
        if INV.spend(self.p, {'currency_credits': KURMA_BEDELI}, 'nav_sub1_clan_found_long') is None:
            return reply(False, 'clan_errmsg_user_not_enough_money')
        cid = 900000 + (self.p.user_id % 100000)
        with self.p.lock:
            self.p.d['klan'] = {'id': cid, 'etiket': tag, 'ad': cname, 'aciklama': desc, 'kurulus': stamp(), 'alim': 0,
                                'alim_bilgi': 0, 'vergi': 0, 'kasa': 0, 'kasa_kaydi': [], 'ts': '',
                                'firma': int(self.p.d['pilot'].get('factionId', 0)), 'haberler': [], 'mesajlar': [],
                                'rutbeler': [], 'benim_rutbem': 0, 'sira': 1}
            self.p.dirty = True
        self.add_news('found', cname)
        self.set_pilot()
        self.log('   klan kuruldu: [%s] %s' % (tag, cname))
        msgs = reply(True, 'empty', cid) + [('JoinClanCommand', {'clanAllInfoCommand': self.all_info()}), self.tag_cmd()]
        return msgs + (self.m.money_msgs() if self.m else [])

    def member_request(self, name, f):
        k = self.k
        if name == 'ChangeClanDescriptionRequest':
            desc = str(f.get('desc', ''))
            ok = len(desc) <= 2000
            if ok:
                with self.p.lock:
                    k['aciklama'] = desc
                    self.p.dirty = True
            return [('ChangeClanDescriptionCommand', {'success': ok, 'errorMsg': err('success_clan_change_descr' if ok else
                                                                                     'clan_errmsg_desc_to_long'), 'desc': k['aciklama']})]
        if name == 'EditClanInfoRequest':
            return self.edit_info(f)
        if name == 'ChangeClanFirmaRequest':
            firm = int(f.get('firma') or 0)
            ok = firm in (0, 1, 2, 3)
            if ok:
                with self.p.lock:
                    k['firma'] = firm
                    self.p.dirty = True
            return [('ChangeClanFirmaCommand', {'success': ok, 'companyDateInfoCommand': self.company(),
                                                'errorMsg': err() if ok else err('clan_err_wrong_value'), 'firm': k['firma']})]
        if name == 'ChangeClanTaxRequest':
            tax = int(f.get('tax') or 0)
            ok = 0 <= tax <= AZAMI_VERGI
            if ok:
                with self.p.lock:
                    k['vergi'] = tax
                    self.p.dirty = True
            return [('ChangeClanTaxCommand', {'tax': k['vergi'], 'success': ok,
                                              'errorMsg': err('clan_changed_tax' if ok else 'clan_err_wrong_value')})]
        if name == 'ClanAddNewsRequest':
            text = str(f.get('newsMessage', '')).strip()
            if not text:
                return [('ClanAddNewsCommand', {'errorMsg': err('clan_errmsg_required', _NAME_=_res('diplo_hl_bewerbungstext')),
                                                'success': False, 'clanNewsInfoCommand': None})]
            n = self.add_news('news', text)
            return [('ClanAddNewsCommand', {'errorMsg': err(), 'success': True, 'clanNewsInfoCommand': self.news_cmd(n)})]
        if name == 'ClanNewsListRequest':
            return [('ClanNewsListCommand', {'newsList': [self.news_cmd(n) for n in k['haberler']]})]
        if name == 'ClanMemberListRequest':
            return [('ClanMemberListCommand', {'memberList': [self.member()]})]
        if name in ('ClanRankListRequest', 'ClanNewRankRequest', 'ClanDeleteRankRequest', 'EditClanRanksRequest',
                    'DeleteMyRankRequest', 'EditClanMemberRequest'):
            return self.rank_request(name, f)
        if name in ('ChangeClanLeaderRequest', 'DeleteClanMemberRequest'):
            e = err('err_clan_you_are_leader')
            if name == 'ChangeClanLeaderRequest':
                return [('ChangeClanLeaderCommand', {'success': False, 'stack': e, 'command': self.info(),
                                                     'newLeaderId': int(f.get('newLeaderId') or 0)})]
            return [('DeleteClanMemberCommand', {'removeUserID': int(f.get('removeUserID') or 0), 'success': False, 'errorMsg': e})]
        if name in ('ClanMessageListRequest', 'ClanSendMessageRequest', 'ClanSendAllMessageRequest', 'ClanDeleteMessageRequest',
                    'ClanDeleteAllMessageRequest'):
            return self.mail_request(name, f)
        if name == 'PayoutClanRequest':
            return self.payout(f)
        if name == 'LeaveClanRequest':
            return [('LeaveClanCommand', {'errorMsg': err('err_clan_you_are_leader'), 'success': False})]
        if name in ('DeleteClanRequest', 'DelClanRequest'):
            return self.delete(name)
        if name == 'ClanReportAdminRequest':
            return [('ClanReportAdminCommand', {'success': True, 'errorMsg': err('clan_message_report_to_admin')})]
        if name in ('ClanNewDiplomacyRequest', 'ClanDeleteDiploRequest', 'ClanDeleteOpenDiploRequest', 'ClanEditDiploOfferRequest'):
            return self.diplo(name, f)
        return []

    def edit_info(self, f):
        k = self.k
        tag, cname = str(f.get('clanTag', k['etiket'])).strip(), str(f.get('clanName', k['ad'])).strip()
        reply = lambda ok, key='empty', **a: [('EditClanInfoCommand', {'success': ok, 'clanId': k['id'], 'clanInfoCommand': self.info(),
                                                                       'errorMsg': err(key, **a)})]
        if not tag or not cname:
            return reply(False, 'clan_errmsg_required', _NAME_=_res('clan_name' if not cname else 'clan_tag'))
        if not self.valid_tag(tag):
            return reply(False, 'clan_errmsg_clantag_not_allowed')
        if len(cname) > 50:
            return reply(False, 'clan_errmsg_to_long')
        changed = tag != k['etiket']
        with self.p.lock:
            k.update(etiket=tag, ad=cname, ts=str(f.get('clanTS', k['ts']))[:100], alim=int(f.get('recruitingStatus') or 0),
                     alim_bilgi=int(f.get('recuritingInfo') or 0))
            self.p.dirty = True
        msgs = reply(True)
        if changed:
            self.set_pilot()
            msgs.append(self.tag_cmd())
        return msgs

    def rank_request(self, name, f):
        k = self.k
        lst = lambda: mod('ClanRankListCommand', ranks=self.ranks())
        if name == 'ClanRankListRequest':
            return [('ClanRankListCommand', {'ranks': self.ranks()})]
        if name == 'ClanNewRankRequest':
            rname = str(f.get('newRank', '')).strip()
            if not rname:
                return [('ClanNewRankCommand', {'command': lst(), 'errorMsg': err('err_clan_emptyRankNotAllowed'), 'success': False})]
            if any(r['ad'].lower() == rname.lower() for r in k['rutbeler']):
                return [('ClanNewRankCommand', {'command': lst(), 'errorMsg': err('err_clan_rankExist'), 'success': False})]
            if len(k['rutbeler']) >= 10:
                return [('ClanNewRankCommand', {'command': lst(), 'errorMsg': err('err_clan_maxRank', XXX=10), 'success': False})]
            rid = self.next_id('rutbe')                     # profil kilidi tekrar girilemez: kimlik kilitten önce
            with self.p.lock:
                k['rutbeler'].append({'id': rid, 'ad': rname[:30], 'haklar': []})
                self.p.dirty = True
            return [('ClanNewRankCommand', {'command': lst(), 'errorMsg': err('clan_new_rank_insert', XXX=rname[:30]), 'success': True})]
        if name == 'ClanDeleteRankRequest':
            rid = int(f.get('deleteRankId') or 0)
            ok = any(r['id'] == rid for r in k['rutbeler'])
            with self.p.lock:
                k['rutbeler'] = [r for r in k['rutbeler'] if r['id'] != rid]
                if k.get('benim_rutbem') == rid:
                    k['benim_rutbem'] = 0
                self.p.dirty = True
            return [('ClanDeleteRankCommand', {'clanRankListCommand': lst(), 'success': ok,
                                               'errorMsg': err() if ok else err('err_clan_no_rank')})]
        if name == 'EditClanRanksRequest':
            by_id = {r['id']: r for r in k['rutbeler']}
            with self.p.lock:
                for r in f.get('ranks') or []:
                    cur = by_id.get(int(r.get('rankId') or 0))
                    if cur:
                        cur['ad'] = str(r.get('rankName', cur['ad']))[:30] or cur['ad']
                        cur['haklar'] = [x for x in r.get('rights') or [] if x in HAKLAR]
                self.p.dirty = True
            return [('EditClanRanksCommand', {'command': lst(), 'errorMsg': err('success_clan_edit_rank'), 'success': True})]
        if name == 'DeleteMyRankRequest':
            with self.p.lock:
                k['benim_rutbem'] = 0
                self.p.dirty = True
            return [('DeleteMyRankCommand', {'command': self.member(), 'errorMsg': err('clan_delete_my_rank_success'), 'success': True})]
        if name == 'EditClanMemberRequest':
            rid, uid = int(f.get('rankId') or 0), int(f.get('memberId') or 0)
            ok = uid == self.p.user_id and (rid == 0 or any(r['id'] == rid for r in k['rutbeler']))
            if ok:
                with self.p.lock:
                    k['benim_rutbem'] = rid
                    self.p.dirty = True
            return [('EditClanMemberCommand', {'clanId': k['id'], 'success': ok, 'command': self.member(),
                                               'errorMsg': err('success_clan_change_rank' if ok else 'err_clan_no_change_rank')})]
        return []

    def mail_request(self, name, f):
        k, pl = self.k, self.p.d['pilot']
        if name == 'ClanMessageListRequest':
            return [('ClanMessageListCommand', {'messageList': [self.mail_cmd(m) for m in k['mesajlar']]})]
        if name in ('ClanSendMessageRequest', 'ClanSendAllMessageRequest'):
            subject, text = str(f.get('subject', '')).strip(), str(f.get('msgText', '')).strip()
            cmd = 'ClanSendMessageCommand' if name == 'ClanSendMessageRequest' else 'ClanSendAllMessageCommand'
            if not subject or not text:
                return [(cmd, {'errorMsg': err('clan_errmsg_required', _NAME_=_res('clan_betreff' if not subject else 'diplo_hl_bewerbungstext')),
                               'success': False, 'clanMessageInfoCommand': None})]
            if name == 'ClanSendMessageRequest' and int(f.get('toUserId') or 0) not in (0, self.p.user_id):
                return [(cmd, {'errorMsg': err('err_clan_user_not_in_clan'), 'success': False, 'clanMessageInfoCommand': None})]
            m = {'id': self.next_id('mesaj'), 'konu': subject[:50], 'metin': text[:5000], 'kim': self.p.user_id,
                 'ad': pl.get('userName', ''), 'tarih': stamp(), 'tur': 0 if name == 'ClanSendMessageRequest' else 1}
            with self.p.lock:
                k['mesajlar'].insert(0, m)
                del k['mesajlar'][100:]
                self.p.dirty = True
            return [(cmd, {'errorMsg': err('clan_msg_send'), 'success': True, 'clanMessageInfoCommand': self.mail_cmd(m)})]
        if name == 'ClanDeleteMessageRequest':
            mid = int(f.get('messageId') or 0)
            ok = any(m['id'] == mid for m in k['mesajlar'])
            with self.p.lock:
                k['mesajlar'] = [m for m in k['mesajlar'] if m['id'] != mid]
                self.p.dirty = True
            return [('ClanDeleteMessageCommand', {'messageId': mid, 'errorMsg': err('clan_msg_delete') if ok else err(),
                                                  'success': ok})]
        if name == 'ClanDeleteAllMessageRequest':
            with self.p.lock:
                k['mesajlar'] = []
                self.p.dirty = True
            return [('ClanDeleteAllMessageCommand', {'errorMsg': err('clan_msg_all_delete'), 'success': True})]
        return []

    def payout(self, f):
        k, pl = self.k, self.p.d['pilot']
        amount = int(f.get('amount') or 0)
        if amount <= 0 or amount > k['kasa']:
            return [('PayoutClanCommand', {'success': False, 'errorMsg': err('err_clan_no_money'), 'clanTaxLogCommand': None,
                                           'clanInfoCommand': self.info()})]
        log = {'balanceUserId': self.p.user_id, 'credits': amount, 'insertDate': stamp(), 'toName': pl.get('userName', ''),
               'fromName': k['ad'], 'moneyType': 'payout', 'reason': str(f.get('reason', ''))[:100]}
        with self.p.lock:
            k['kasa'] -= amount
            k['kasa_kaydi'].insert(0, log)
            self.p.dirty = True
        self.p.gain(kredi=amount, neden='clan_hl_auszahlungen', detay=k['ad'])
        return [('PayoutClanCommand', {'success': True, 'errorMsg': err('success_clan_payout'),
                                       'clanTaxLogCommand': mod('ClanTaxLogCommand', **log), 'clanInfoCommand': self.info()})] + \
            (self.m.money_msgs() if self.m else [])

    def delete(self, name):
        k = self.k
        with self.p.lock:
            self.p.d['klan'] = None
            self.p.dirty = True
        self.set_pilot()
        self.log('   klan silindi: [%s] %s' % (k['etiket'], k['ad']))
        cmd = 'DeleteClanCommand' if name == 'DeleteClanRequest' else 'DelClanCommand'
        return [(cmd, {'success': True, 'errorMsg': err()}), ('ClearClanCommand', {'clanId': k['id']}), self.tag_cmd()]

    def diplo(self, name, f):
        """Diplomasi başka klan ister (bot klanlar, Aşama 11)."""
        e = err('err_diplo_not_with_own_clan' if int(f.get('diploClanID') or f.get('toClanId') or 0) == self.k['id'] else
                'err_clan_noClanID')
        did = int(f.get('diploId') or 0)
        if name == 'ClanNewDiplomacyRequest':
            return [('ClanNewDiplomacyCommand', {'errorMsg': e, 'success': False, 'clanDiploReqInfoCommand': None})]
        if name == 'ClanDeleteDiploRequest':
            return [('ClanDeleteDiploCommand', {'diploId': did, 'baseStackCommand': e, 'success': False})]
        if name == 'ClanDeleteOpenDiploRequest':
            return [('ClanDeleteOpenDiploCommand', {'diploId': did, 'success': False, 'errorMsg': e})]
        return [('ClanEditDiploOfferCommand', {'status': str(f.get('status', '')), 'success': False, 'clanDiploInfoCommand': None,
                                               'stack': e, 'clanDiploReqInfoCommand': None})]

    # -------------------------------------------------------- sohbet
    def rooms(self):
        k = self.k
        return [('clan', 'clan', str(k['id']))] if k else []
