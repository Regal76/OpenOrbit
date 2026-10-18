"""Ö3'ün etkinlikleri ve Ö4'ün büyük PvE içerikleri (yol haritası Ö3, Ö4; veri data/ek_etkinlikler.json <- tools/ek_etkinlikler.py,
data/buyuk_icerikler.json <- tools/buyuk_icerikler.py): oturum düzeyindeki kap.

Her sistem aynı yüzü taşır (hepsi isteğe bağlı): REQUESTS (karşıladığı istekler), handle(name, f) -> mesajlar, login_msgs() (hazır
demetinde), login_replace(n, f) (giriş demetindeki kayıtlı mesajın yerine; None: dokunma), tick(now) -> mesajlar, on_kill(w, npc, x, y)
(dünya kilidi altında, uzaylı ödülü verilirken) -> mesajlar, attach(w) (harita açıldı).
window(item) (pencere açıldı: UIButtonTriggerRequest).
Sistemler: Chromin Rush (chromin.py), Hitac Word Puzzle ve Capsule Lottery (hitac_piyango.py), Fever (fever.py), Pursuit of Prestige
(unvan_avi.py), Galaxy Trek (galaxy_trek.py), Fiesta Gate (fiesta.py), Infiltration (sizma.py), Urgent Missions (acil_gorevler.py),
eski Invasion (istila.py); Ö4: Vortex of Greed (vortex.py), Treacherous Domain / World Boss 2025 (dunya_patronu.py), Mimesis Mutiny
(mimesis.py). Ö4'ünkiler haritada dünyanın 'kapi'sını kurar (dalgalar, ölüm ekranı, radyasyon kancaları).
"""
import traceback

import chromin as CHR
import hitac_piyango as HP
import fever as FV
import unvan_avi as UA
import galaxy_trek as GTR
import fiesta as FS
import sizma as SZ
import acil_gorevler as AG
import istila as IS
import vortex as VG
import dunya_patronu as WB
import mimesis as MM


class EkEtkinlikler:
    def __init__(self, profil, magaza, ekapilar=None, log=print):
        self.p, self.m, self.log = profil, magaza, log
        self.chromin = CHR.Chromin(profil, magaza, log)
        magaza.chromin = self.chromin
        self.hitac = HP.HitacPiyango(profil, magaza, log)
        magaza.hitac = self.hitac
        self.fever = FV.Fever(profil, magaza, log)
        self.unvan = UA.UnvanAvi(profil, magaza, log)
        self.trek = GTR.GalaxyTrek(profil, magaza, log)
        self.trek.titles = self.unvan.grant_title
        self.fiesta = FS.Fiesta(profil, magaza, ekapilar, log) if ekapilar else None
        self.istila = IS.Istila(profil, magaza, ekapilar, log) if ekapilar else None
        self.sizma = SZ.Sizma(profil, magaza, log)
        self.acil = AG.AcilGorevler(profil, magaza, log)
        self.vortex = VG.Vortex(profil, magaza, ekapilar, log)                  # Ö4
        self.patron = WB.DunyaPatronu(profil, magaza, ekapilar, log)
        self.mimesis = MM.Mimesis(profil, magaza, ekapilar, log)
        for s in (self.vortex, self.patron, self.mimesis):
            s.titles = self.unvan.grant_title
        self.patron.send = lambda msgs: self.send(msgs)
        self.systems = [self.chromin, self.hitac, self.fever, self.unvan, self.trek, self.sizma, self.acil] + \
            [s for s in (self.fiesta, self.istila) if s] + [self.vortex, self.patron, self.mimesis]
        self.send = lambda msgs: None            # oturum bağlar
        self.world = None
        self.requests = {}
        for s in self.systems:
            for r in getattr(s, 'REQUESTS', ()):
                self.requests[r] = s

    def add(self, system):
        """Kaba sonradan sistem (Clan Battle Station: cbs.py; oturum kurar)."""
        self.systems.append(system)
        for r in getattr(system, 'REQUESTS', ()):
            self.requests[r] = system

    def handles(self, name):
        return name in self.requests

    def handle(self, name, f):
        try:
            return self.requests[name].handle(name, f) or []
        except Exception:
            self.log('   Ö3 isteği hatası (%s):\n%s' % (name, traceback.format_exc()))
            return []

    def _each(self, meth, *a):
        out = []
        for s in self.systems:
            fn = getattr(s, meth, None)
            if fn:
                try:
                    out += fn(*a) or []
                except Exception:
                    self.log('   Ö3 %s hatası (%s):\n%s' % (meth, type(s).__name__, traceback.format_exc()))
        return out

    def login_msgs(self):
        return self._each('login_msgs')

    def on_ready(self):
        """Harita yüklendi (ilk giriş dışındaki ReadyRequest)."""
        return self._each('on_ready')

    def event(self, kind, kw):
        """Oyun olayı (oturumun başarım ve görev olayları): etkinlik görevleri (Galaxy Trek …)."""
        return self._each('event', kind, kw)

    def window(self, item):
        """Pencere açıldı (UIButtonTriggerRequest itemId)."""
        return self._each('window', item)

    def window_update(self, f):
        """Pencerenin durumu (UIWindowUpdateRequest {itemId, maximized, …}): açılınca, taşınınca, kapanınca."""
        return self._each('window_update', f)

    def login_replace(self, n, f):
        for s in self.systems:
            fn = getattr(s, 'login_replace', None)
            rep = fn(n, f) if fn else None
            if rep is not None:
                return rep
        return None

    def tick(self, now):
        return self._each('tick', now)

    def portals(self, map_id, station):
        """Haritanın Ö3 portalları (Fiesta Gate'in X-1 portalı)."""
        return self._each('portals', map_id, station)

    def attach(self, world):
        self.world = world
        world.kill_hooks.append(lambda w, n, x, y: self._each('on_kill', w, n, x, y))
        return self._each('attach', world)
