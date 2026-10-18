"""Sonsuz ve rogue-lite PvE modlarının oturum düzeyi (yol haritası Aşama 8): portallar, pencereler, istekler, kapı CPU'ları,
girişteki göstergeler ve harita sahipliği.

Modlar: Voyagers' Ascent ve Trinity Trials (arena.py), Astral Ascension (astral.py), Deep Space Echoes (echoes.py), Eternal Black
Light (ebl.py). Quarantine Zone ve Compromising Invasion etkinlik kapısı biçiminde (etkinlik_kapi.py, takvimsiz).
Pencereli portal (portalın 'pencere'si): atlayınca (J) dünya gate_window'u çağırır; mod penceresini gönderir ya da kendisi harita
değiştirir. Kapı CPU'ları (ammunition_ggportal_*): kısayol çubuğundan; Eternal CPU X-BL'de, Astral CPU X-1'de, Immunizer CPU
X-7'de kendi kapısını açar.
"""
import arena as AR
import astral as AS
import echoes as EC
import etkinlik_kapi as EKP
import harita as H
import kapi as KAPI

try:
    import ebl as EB
except ImportError:                   # Eternal Black Light'ın verisi yoksa
    EB = None

WINDOWS = ('voyagers', 'trinityTrials', 'expedition', 'eternal_blacklight', 'rogue_lite')    # özellik çubuğu pencereleri
REQUESTS = {
    'VoyagersUIRequest', 'VoyagersGateEnterRequest', 'VoyagersClaimPassRewardRequest',
    'TrinityTrialsUIRequest', 'TrinityTrialsGateEnterRequest', 'TrinityTrialsDropLevelOptionalRequest', 'TrinityTrialsClaimPassRewardRequest',
    'RogueLiteSelectShipRequest', 'RogueLiteSelectRewardRequest', 'RogueLiteChangeEquipmentRequest',
    'ExpeditionInfoRequest', 'ExpeditionShipListRequest', 'ExpeditionSelectShipRequest', 'ExpeditionActivateShipRequest',
    'ExpeditionBuyTicketRequest', 'ExpeditionJumpTargetLevelRequest', 'ExpeditionResetRequest', 'ExpeditionBackRequest',
    'EternalBlacklightChooseOptionRequest'}
QUARANTINE_CPU = 'ammunition_ggportal_quarantine-zone-cpu'


class PveModlari:
    def __init__(self, profil, magaza, ekapilar, log=print):
        self.p, self.m, self.k, self.log = profil, magaza, ekapilar, log
        self.voyagers = AR.Voyagers(profil, log)
        self.trinity = AR.Trinity(profil, log)
        for a in (self.voyagers, self.trinity):
            a.m = magaza
        self.astral = AS.Astral(profil, magaza, log)
        self.echoes = EC.Echoes(profil, magaza, log)
        self.ebl = EB.Ebl(profil, magaza, log) if EB else None
        self.send = lambda msgs: None          # oturum bağlar
        self.change_map = None                 # oturum bağlar: (hedef, portal, konum)
        self.world = None
        self.extra_windows = {}                # başka modüllerin pencereli portalları: tür -> (portal, dünya, git)
        self.last_where = 'X-1'                # son açılan kapı penceresinin haritası (günlük giriş sayacı)
        self.maps = {self.voyagers.D['harita']: self.voyagers}
        for ids in self.trinity.D['haritalar'].values():
            self.maps.update({m: self.trinity for m in ids})
        self.maps.update({m: self.astral for m in AS.D['haritalar']})
        self.maps.update({m: self.echoes for m in [EC.D['salon']] + EC.D['haritalar']})
        if self.ebl:
            self.maps.update({m: self.ebl for m in self.ebl.maps()})

    # ------------------------------------------------------------ dünya
    def portals(self, map_id, station):
        out = self.voyagers.portals(map_id, station) + self.trinity.portals(map_id, station) + self.astral.portals(map_id) \
            + self.echoes.portals(map_id)
        if self.ebl:
            out += self.ebl.portals(map_id)
        return out

    def attach(self, world):
        """Harita açıldı: modun haritasıysa koşusu (dünyanın 'kapi'sı)."""
        self.world = world
        world.portal_cpu = self.portal_cpu
        world.gate_window = self.window
        mode = self.maps.get(int(world.map_id))
        if mode:
            mode.attach(world)
            if mode is self.echoes and int(world.map_id) == EC.D['salon']:
                jump = self.echoes.jump_info_cmd()
                world.send([self.echoes.info_cmd()] + ([jump] if jump[1]['levels'] else []))
        return mode

    def portal_cpu(self, item):
        """Kısayol çubuğundan kapı CPU'su (dünya kilidi altında)."""
        w = self.world
        msgs = None
        if item == AS.D['cpu']:
            msgs = self.astral.use_cpu(w.map_id)
            if msgs:
                for g in self.astral.portals(w.map_id):
                    w.add_gate(g)
        elif self.ebl and item == self.ebl.D['cpu']:
            msgs = self.ebl.use_cpu(w.map_id)
            if msgs:
                for g in self.ebl.portals(w.map_id):
                    w.add_gate(g)
        elif item == QUARANTINE_CPU and 'karantina' in EKP.GATES:
            msgs = self.quarantine_cpu(w)
        if msgs is None:
            w.log('   kapı CPU\'su kullanılamaz: %s (%s)' % (item, H.name(w.map_id)))
            msgs = [KAPI.screen('This CPU cannot be used here.')]
        st = self.p.menu_status(item)
        w.send(msgs + ([('MenuItemStatusCommand', st)] if st else []))

    def quarantine_cpu(self, w):
        """Immunizer CPU: X-7'de Quarantine Zone kapısı (etkinlik kapısı biçimi, tek can)."""
        g = EKP.GATES['karantina']
        if H.map_class(w.map_id) != g['giris'] or self.k.gate('karantina').get('hazir'):
            return None
        if self.p.use_ammo(QUARANTINE_CPU) is None:
            return None
        self.k.enter('karantina')
        for x in self.k.entry_portals(w.map_id, w.station):
            if x['kapi'] == 'karantina':
                w.add_gate(x)
        self.log('   Immunizer CPU: Quarantine Zone kapısı')
        return [KAPI.screen('The Quarantine Zone gate has opened.', big=True)]

    # ------------------------------------------------------------ pencereli portallar
    def window(self, g):
        """Dünya kilidi altında: pencereyi gönder ya da haritayı değiştir (zamanlayıcıyla, kilit dışında)."""
        kind = g['pencere']
        w = self.world
        go = lambda dest, pos=None: w.later(0.2, lambda: self.change_map(dest, dict(g, pencere=None), pos))
        if kind in ('voyagers', 'trinity'):
            self.last_where = g.get('giris', 'X-1')
            a = self.voyagers if kind == 'voyagers' else self.trinity
            w.send([a.window(self.last_where)])
        elif kind == 'astral':
            dest, msgs = self.astral.gate_jump()
            w.send(msgs)
            if dest:
                go(dest)
        elif kind == 'astral_odul':
            go(self.astral.choose_gate(g))
        elif kind == 'echoes_giris':
            dest, msgs = self.echoes.enter_hall()
            w.send(msgs)
            if dest:
                go(dest, (10500, 6550))
        elif kind == 'echoes_basla':
            if not self.echoes.st['kadro']:
                w.send([KAPI.screen('Choose your ships first (middle gate).'), self.echoes.ship_list()])
            else:
                w.send([self.echoes.roster_cmd()])
        elif kind == 'echoes_gemi':
            w.send([self.echoes.ship_list()])
        elif kind == 'echoes_cikis':
            w.send([('ExpeditionShowUiCommand', dict(type=EC.UI_LEAVE, param0='', param1=''))])
        elif kind == 'ebl' and self.ebl:
            dest, msgs = self.ebl.gate_jump()
            w.send(msgs)
            if dest:
                go(dest)
        elif kind in self.extra_windows:
            self.extra_windows[kind](g, w, go)          # Ö3: Fiesta Gate'in giriş penceresi (fiesta.py)

    def on_jump(self, gate):
        """Oturumun harita değişiminden önce (portal kaydı): Astral'ın çıkışı oyuncunun donanımını geri getirir."""
        if gate and gate.get('astral_cikis'):
            self.astral.leaving()

    # ------------------------------------------------------------ istekler
    def handle(self, name, f):
        """Mod istekleri -> mesajlar (harita değişimi gerekiyorsa change_map çağrılır)."""
        v, t, a, e = self.voyagers, self.trinity, self.astral, self.echoes
        if name == 'VoyagersUIRequest':
            return [v.gecis.cmd('VoyagersPassCommand')]
        if name == 'VoyagersClaimPassRewardRequest':
            return v.pass_claim(f, 'VoyagersPassCommand')
        if name == 'VoyagersGateEnterRequest':
            dest, msgs = v.enter(f, self.last_where)
            return self.jump(dest) if dest else msgs
        if name == 'TrinityTrialsUIRequest':
            return t.ui(f)
        if name == 'TrinityTrialsClaimPassRewardRequest':
            return t.pass_claim(f, 'TrinityTrialsPassCommand')
        if name == 'TrinityTrialsDropLevelOptionalRequest':
            return t.drop_level_optional(f)
        if name == 'TrinityTrialsGateEnterRequest':
            dest, msgs = t.enter(f, self.last_where)
            return self.jump(dest) if dest else msgs
        if name == 'RogueLiteSelectShipRequest':
            dest = a.select_ship(f)
            return self.jump(dest) if dest else [KAPI.screen('This ship cannot be selected.')]
        if name == 'RogueLiteSelectRewardRequest':
            return a.select_reward(f)
        if name == 'RogueLiteChangeEquipmentRequest':
            return a.change_equipment(f)
        if name == 'ExpeditionInfoRequest':
            # ExpeditionJumpLevelInfoCommand burada değil: istemci onu alınca atlama penceresini açıyor (canlı test H49: Echoes
            # penceresi her açılışta boş bir "Note" penceresi getiriyordu); salona girişte, atlanacak blok varsa
            return [e.info_cmd()]
        if name == 'ExpeditionShipListRequest':
            return [e.ship_list()]
        if name == 'ExpeditionSelectShipRequest':
            return e.select_ships(f)
        if name == 'ExpeditionActivateShipRequest':
            dest, msgs = e.start_level(f)
            return msgs + self.jump(dest) if dest else msgs        # önce pencere kapatma, sonra atlama (H74)
        if name == 'ExpeditionBuyTicketRequest':
            return e.buy_ticket()
        if name == 'ExpeditionJumpTargetLevelRequest':
            return e.jump(f)
        if name == 'ExpeditionResetRequest':
            return e.reset()
        if name == 'ExpeditionBackRequest':
            return self.jump(KAPI.HOME_MAP.get(self.p.d['pilot'].get('factionId'), 5))
        if name == 'EternalBlacklightChooseOptionRequest' and self.ebl:
            return self.ebl.choose(f)
        return []

    def jump(self, dest, pos=None):
        if self.change_map:
            self.change_map(dest, {'kapi': 'pve'}, pos)
        return []

    # ------------------------------------------------------------ giriş
    def login_replace(self, name):
        """Kayıttaki giriş mesajı yerine profilinki (yoksa None: olduğu gibi)."""
        if name == 'RogueLiteInfoCommand':
            return [self.astral.info_cmd()]
        if name == 'RogueLiteRankEventInfoCommand':
            return [self.astral.rank_cmd()]
        if name == 'EternalBlacklightInfoCommand' and self.ebl:
            # sıralama listesi kayıtta yok, yalnız koşu bitince gidiyordu: Rank sekmesi "No ranking boards are available" (H76)
            return [self.ebl.info_cmd(), self.ebl.rank_cmd()]
        return None
