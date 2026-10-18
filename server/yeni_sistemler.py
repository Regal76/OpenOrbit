"""Bu istemcideki yeni sistemlerin oturum düzeyi (yol haritası Aşama 9): N.O.V.A. kaptanları (nova.py), Armory Unlock (armory.py),
Quantum Fluid Core ve Hyperforge (qfc.py), Omega AutoTactic (otopilot.py).

Oturum bağlar: istekler (REQUESTS), girişteki kayıtlı yanıtların yerine profildekiler (login_replace: N.O.V.A. kadrosu, Evocation
Chip sayısı, göstergedeki enerji; login_msgs: QFC listesi), mağazanın ödül yolu (reward: N.O.V.A. ve QFC eşyaları), profilin
bonusları (mods: takılı N.O.V.A.), dünya (attach: istasyonda mı, lazer menzili). Echo sandıkları Deep Space Echoes'un patron
seviyelerinde düşer (echoes.py, qfc.py).
Aşama 9b: Synthesis penceresi (synthesis.py), top/kırıcı/sürücü/mercek ödülleri ve depodan taşıma, sürücü/merceklerin alt nitelik
yenilemesi (LockAttributeItemRerollRequest; parcacik.py). Uçuştaki atış dünyanın kendi modülünde (parcacik.Atis).
"""
import armory as AU
import nova as NV
import otopilot as OP
import parcacik as PC
import qfc as QF
import synthesis as SY

LOCK_REQUESTS = {'LockAttributeItemRerollRequest'}            # sürücü/merceğin alt nitelikleri (parcacik.py)
REQUESTS = AU.REQUESTS | NV.REQUESTS | OP.REQUESTS | QF.REQUESTS | SY.REQUESTS | LOCK_REQUESTS


class YeniSistemler:
    def __init__(self, profil, magaza, log=print):
        self.p, self.log = profil, log
        self.nova = NV.Nova(profil, log)
        self.armory = AU.Armory(profil, log)
        self.qfc = QF.Qfc(profil, log)
        self.otopilot = OP.Otopilot(profil, log)
        self.synthesis = SY.Synthesis(profil, log)                  # Aşama 9b: Synthesis penceresi
        for x in (self.nova, self.armory, self.qfc, self.synthesis):
            x.m = magaza
        self.m = magaza
        self.world = None
        moved = PC.migrate(profil)                                  # depodaki top, kırıcı, sürücü, mercek -> envanter (Aşama 9b)
        if moved:
            log('   parçacık eşyaları depodan envantere: %d' % moved)

    def attach(self, world):
        self.world = world
        self.nova.at_station = world.in_station
        self.otopilot.laser_range = world.laser_range
        self.otopilot.maps = world.omega_maps                   # seçim listeleri: harita -> orada çıkan uzaylılar
        self.otopilot.pencere = False                           # yeni harita: pencere kapanmış sayılır
        world.omega_view = self.otopilot.reveal                 # pencere açıkken ve otomatik pilot çalışırken haritanın tümü

    def handle(self, name, f):
        if name in AU.REQUESTS:
            return self.armory.handle(name, f)
        if name in NV.REQUESTS:
            return self.nova.handle(f)
        if name in QF.REQUESTS:
            return self.qfc.handle(f)
        if name in OP.REQUESTS:
            return self.otopilot.handle(name, f)
        if name in SY.REQUESTS:
            return self.synthesis.handle(name, f)
        if name in LOCK_REQUESTS:
            iid = int(f.get('targetItemId') or 0)
            ok = PC.lock_reroll(self.p, iid, f.get('lockIndexList') or [])
            self.log('   Singularity Drive yenileme: %s %s' % (self.p.d['esyalar'].get(str(iid)), 'tamam' if ok else 'olmadı'))
            from envanter import update_msgs
            K = PC.D['kilit']
            return [('LockAttributeItemRerollCommand', {'result': ok}), PC.lock_list_cmd(self.p)] + \
                (update_msgs(self.m, self.p, [K['yenileme_esya'], K['kilit_esya']]) if ok else [])
        return []

    def reward(self, loot, n):
        """Mağazanın ödül yolu: N.O.V.A. (captain_*) kadroya, QFC (equipment_core_*) bağlı gemisiyle envantere; değilse None."""
        if loot.startswith('captain_'):
            return self.nova.hire(loot, n)
        if loot.startswith(QF.PREFIX):
            return self.qfc.grant(loot, n)
        if PC.is_item(loot):
            return self.particle(loot, n)
        return None

    def particle(self, loot, n):
        """Top, kırıcı, sürücü, mercek: ek nitelikleriyle envantere (takılmaz: tür kuralı hangarda)."""
        from eski_protokol import legacy
        msgs = []
        for _ in range(n):
            iid = PC.create(self.p, loot)
            msgs += [self.m.inv_item(iid, loot, 1), self.m.pack([self.m.hangar_item(iid, loot, 1)])]
        if loot in PC.DRIVES or loot in PC.LENSES:
            msgs.append(PC.lock_list_cmd(self.p))
        else:
            import gemi_modul as GM
            msgs.append(GM.list_cmd(self.p))
        return msgs + [legacy('0|LM|ST|LOT|%s|%d' % (loot, n))]

    def mods(self, map_id):
        return self.nova.mods(map_id)

    def login_replace(self, name):
        """Giriş demetindeki kayıtlı mesajın yerine profilinki (yoksa None)."""
        if name == 'CaptainRosterListCommand':
            return [self.nova.roster_cmd()]
        if name == 'CaptainGetResourcesBackCommand':
            return [self.nova.chips_cmd()]
        if name == 'QuantumFluidCoreDataListCommand':
            return [self.qfc.list_cmd()]
        if name == 'EnergyUpdateCommand':
            return [self.nova.energy_cmd()]
        return None

    def login_msgs(self):
        """Harita yüklenince (hazır demeti): QFC listesi, Synthesis tarifleri, sürücü/merceklerin alt nitelikleri, N.O.V.A. ipucu."""
        return [self.qfc.list_cmd(), self.synthesis.list_cmd(), PC.lock_list_cmd(self.p), self.nova.perk_update_cmd()]
