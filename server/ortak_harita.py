"""Arkadaş sunucusunda haritaların paylaşımı (cok_oyunculu.py; panelin "Arkadaşlarınla Oyna" sayfası).

Tek oyunculuda her oturumun kendi dünyası (dunya.World) vardır. Arkadaş sunucusunda aynı normal haritadaki oyuncuların dünyaları
bir Harita'yı paylaşır: uzaylılar, kutular, cevherler, bekleyen doğmalar, uzaylı kimlik sayacı, takvimin harita etkinliği ve dünya
kilidi ortaktır (dünyaların döngü adımları sırayla işler). Her dünya kendi kahramanını sürer: konum, hedef, ateş, etkiler, P.E.T.,
portallar, ödüller (uzaylıyı kim öldürürse ödül onun).
  - Uzaylının yapay zekâsını (dunya.think), yeteneklerini (uzayli.py), zehir ve onarımını "sahibi" olan dünya işler: savaştığı
    oyuncu (vuran oyuncu sahibi olur), savaşmıyorsa ulaşılabilir en yakın oyuncu (sahipler).
  - Haritanın işleri (yeniden doğmalar, süresi biten kutular, zaman çizelgeli uzaylılar, takvimin harita etkinliği) liderin döngüsünde:
    haritaya ilk giren, o çıkınca sıradaki.
  - Herkesin görmesi gereken mesajlar (uzaylının hareketi, lazer ve vuruşlar, patlamalar, görsel etkiler) gönderen dünyadan öteki
    üyelere yansıtılır (yansit); her alıcı yalnız tanıdığı gemilerinkini alır (World.tanir).
  - Oyuncular birbirini görüş mesafesinde görür (gorunurluk): ShipCreateCommand, unvan, dronlar ve modüller (kayıttaki başka oyuncunun
    mesajları; game.Session.gorunum), kahramanın hareketi MoveCommand olarak (hareket). Ölü, atlamadaki ya da gizli oyuncu görünmez.
Kapı, mod ve etkinlik haritaları (oturumun kendi koşusu olanlar) paylaşılmaz: her oyuncunun kendi kopyası (game.Session.start_world).
Son oyuncu çıkınca harita durumu tek oyunculudaki gibi saklanır (dunya.WORLD_CACHE) ve ortak durum bırakılır.
"""
import math, threading

UID_BASE = 150300000          # uzaylı kimliklerinin başlangıcı (dunya.World'ünkiyle aynı)
FLASHLIGHT = 62               # el feneri (dunya.FLASHLIGHT): oyuncunun kendi ekranının etkisi, yansıtılmaz
SAHIP_SN = 0.1                # sahiplerin yeniden hesaplanma aralığı (döngü adımı)
# yansıtılan mesajlar -> içlerinde geçen gemi kimliklerinin alanları (alıcı hepsini tanıyorsa gider; 0: çevre, ör. radyasyon)
YANSIYAN = {'MoveCommand': ('userId',), 'AttackLaserRunCommand': ('attackerId', 'targetId'),
            'AttackHitCommand': ('attackerId', 'victimId'), 'AttackMissedCommand': ('targetUserId',),
            'ShipDestroyedCommand': ('destroyedUserId',), 'VisualModifierCommand': ('userId',),
            # lazerin bitişi: istemci AttackLaserRunCommand'da saldıranın hedefini kurar (ShipInfo.Target) ve gemiyi ona döndürür;
            # bu gelmezse öteki oyuncunun gemisi hedefe dönük kalıyor, burnu dönmüyor ve motor efekti çıkmıyordu (AttackAbortLaser.Run)
            'AttackAbortLaserCommand': ('uid',)}
# eski metinle giden görseller (eski_protokol.py) -> içlerindeki gemi kimliklerinin parça sırası (ilk sayı listesi: kalan parçaların
# hepsi kimlik): roket 0|v|saldıran|hedef|…, Smart Bomb / Insta-Shield / EMP 0|n|SMB|uid, gemi yeteneği 0|n|SD|A|etki|kalıcı|
# etkinleştiren[|hedef], teknoloji 0|n|A|S|kod|uid ve Chain Impulse 0|n|ECI|1|saldıran|hedef…
ESKI = {('0', 'v'): (2, 3), ('0', 'n', 'SMB'): (3,), ('0', 'n', 'ISH'): (3,), ('0', 'n', 'EMP'): (3,),
        ('0', 'n', 'SD'): (6, [7]), ('0', 'n', 'A', 'S'): (5,), ('0', 'n', 'ECI'): (4, [5])}

REG = threading.Lock()
HARITALAR = {}                # harita kimliği -> Harita (kullanan dünya varken)


def al(map_id):
    """Haritanın ortak durumu (yoksa kurulur). Dünya kurulurken bir kez (World.__init__); dünya durunca birak()."""
    with REG:
        h = HARITALAR.get(str(map_id))
        if h is None:
            h = HARITALAR[str(map_id)] = Harita(str(map_id))
        h.ref += 1
        return h


class Harita:
    def __init__(self, map_id):
        self.map_id = map_id
        self.lock = threading.RLock()
        self.npcs, self.boxes, self.ores = {}, {}, {}
        self.pending, self.ore_fields = [], []
        self.next_uid = UID_BASE
        self.uyeler = []              # döngüsü çalışan dünyalar, girişe göre (ilki lider)
        self.etkinlik = None          # takvimin harita etkinliği (etkinlik_harita.HaritaEtkinlik; lider sürer)
        self.ref = 0                  # bu haritayı tutan dünyalar (kurulmuş ama henüz girmemiş olanlar dahil)
        self._sahip, self._sahip_an = {}, 0.0

    @property
    def lider(self):
        return self.uyeler[0] if self.uyeler else None

    def katil(self, w):
        """Dünyanın döngüsü başladı (dünya kilidi altında)."""
        if w not in self.uyeler:
            self.uyeler.append(w)
        if self.etkinlik is not None:
            self.etkinlik.w = self.lider
        self._sahip_an = 0.0

    def ayril(self, w):
        """Dünya durdu (harita değişimi, bağlantı koptu) -> kalan üye yoksa True. Ondan savaşan uzaylılar yeniden sahiplenilir."""
        with self.lock:
            if w in self.uyeler:
                self.uyeler.remove(w)
            for n in self.npcs.values():
                if getattr(n, 'foe', None) is w:
                    n.foe = None
            if self.etkinlik is not None and self.lider is not None:
                self.etkinlik.w = self.lider
            self._sahip_an = 0.0
            return not self.uyeler

    def birak(self):
        """Dünya bu haritayı bıraktı (bir kez): kimse tutmuyorsa kayıttan çıkar."""
        with REG:
            self.ref -= 1
            if self.ref <= 0 and HARITALAR.get(self.map_id) is self:
                del HARITALAR[self.map_id]

    # ------------------------------------------------------------ uzaylıların sahipleri
    def sahipler(self, now):
        """uzaylı kimliği -> yapay zekâsını işleyen dünya. Savaşan uzaylı savaştığı oyuncunun (o haritadaysa); öteki uzaylılar
        ulaşılabilir en yakın oyuncunun (ölü, atlamada, güvenli bölgede, gizli olmayan; kimse değilse en yakının)."""
        if now - self._sahip_an < SAHIP_SN:
            return self._sahip
        uyeler = [w for w in self.uyeler if w.running]
        pos = {w: w.hero_pos(now) for w in uyeler}
        acik = {w: w.ulasilir(now) for w in uyeler}
        out = {}
        for n in self.npcs.values():
            f = getattr(n, 'foe', None)
            if not (n.engaged and f in pos):
                nx, ny = n.mover.pos(now)
                f = min(uyeler, key=lambda w: (not acik[w], (pos[w][0] - nx) ** 2 + (pos[w][1] - ny) ** 2), default=None)
                n.foe = f
            out[n.id] = f
        self._sahip, self._sahip_an = out, now
        return out

    def sahibi_mi(self, w, n, now):
        """Uzaylının yapay zekâsını bu dünya mı işler (yeni doğan, henüz hesaplanmamış uzaylı: lider)."""
        o = self.sahipler(now).get(n.id)
        return (o if o is not None else self.lider) is w

    # ------------------------------------------------------------ mesajlar
    def yansit(self, kaynak, msgs):
        """Kaynak dünyanın herkese görünen mesajları öteki üyelere (tanıdıkları gemilerinkiler)."""
        out = [(m, kimlikler(m)) for m in msgs if not (m[0] == 'VisualModifierCommand' and m[1].get('modifier') == FLASHLIGHT)]
        out = [(m, ids) for m, ids in out if ids is not None]
        if not out:
            return
        for w in self.uyeler:
            if w is kaynak or not w.running:
                continue
            mine = [m for m, ids in out if all(w.tanir(x) for x in ids)]
            if mine:
                w.teslim(mine)

    def hareket(self, kaynak, x, y, ms):
        """Kahraman hareket etti: onu gören oyunculara MoveCommand (oyuncunun kendisine gitmez; istemci kendisi yürütür)."""
        m = ('MoveCommand', dict(userId=kaynak.hid, x=int(x), y=int(y), timeToTarget=int(ms)))
        for w in self.uyeler:
            if w is not kaynak and w.running and kaynak.hid in w.oyuncular:
                w.teslim([m])

    def gorunurluk(self, w, now, hx, hy, gorus, birakma):
        """Öteki oyuncuların w'nin istemcisindeki gemileri: görüşe gireni göster, çıkanı (ölen, atlayan, gizlenen, ayrılan, görünümü
        değişen) kaldır -> mesajlar."""
        cur = {}
        for m in self.uyeler:
            if m is w or not m.running or m.hero_dead or m.jumping or m.reload_pending or m.gizli(now):
                continue
            mx, my = m.hero_pos(now)
            lim = birakma if m.hid in w.oyuncular else gorus
            if math.hypot(mx - hx, my - hy) <= lim:
                cur[m.hid] = m
        msgs = []
        for uid in list(w.oyuncular):
            m = cur.get(uid)
            if m is None or w.oyuncular[uid] != m.imza():
                del w.oyuncular[uid]
                msgs.append(('ShipRemoveCommand', {'userId': uid}))
        for uid, m in cur.items():
            if uid not in w.oyuncular:
                w.oyuncular[uid] = m.imza()
                msgs += m.gorunum_msgs(now)
        return msgs


def kimlikler(m):
    """Yansıtılan mesajın gemi kimlikleri (alıcı hepsini tanımalı) ya da None (yansıtılmaz)."""
    if m[0] in YANSIYAN:
        return [m[1].get(k) for k in YANSIYAN[m[0]]]
    if m[0] != 'LegacyModule':
        return None
    parts = str(m[1].get('message', '')).split('|')
    for key, pos in ESKI.items():
        if tuple(parts[:len(key)]) != key:
            continue
        fixed = [i for i in pos if not isinstance(i, list)]
        rest = [j for i in pos if isinstance(i, list) for j in range(i[0], len(parts))]
        try:
            return [int(parts[i]) for i in fixed + rest]
        except (ValueError, IndexError):
            return None
    return None


def ortak_mi(w):
    """Dünya bir ortak haritada mı ve orada başka oyuncu var mı (yansıtma gereksizse atlanır)."""
    return w.ortak is not None and len(w.ortak.uyeler) > 1
