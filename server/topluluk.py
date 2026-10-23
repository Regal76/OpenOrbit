"""Sunucudaki oyuncular: grup (grup.py), rehber (rehber.py), sohbetin fısıltısı, posta ve pilot kartı başka oyuncuyu buradan bulur.

Tek oyunculuda yalnız oyuncunun kendisi; arkadaş sunucusunda (cok_oyunculu.py) sunucunun kendi oyuncusu ve misafirler. Kaydı sunucuda
olan herkes bilinir (bağlı olmayan misafirin kaydı da bellekte durur: posta ve rehber isteği ona yazılır, son hâli paneline gider);
oyun bağlantısı olan çevrimiçidir. Misafirin sunucudaki kimliği her katılmada başka (cok_oyunculu._yeni_uid): kalıcı bağlar (rehber)
ada göre tutulur.
"""
import cok_oyunculu as CO

OYUN = None          # game modülü (game.py bağlar): PROFIL, CURRENT


class Kisi:
    __slots__ = ('profil', 'oturum')

    def __init__(self, profil, oturum):
        self.profil, self.oturum = profil, oturum       # oturum: bağlı game.Session ya da None

    @property
    def uid(self):
        return self.profil.user_id

    @property
    def ad(self):
        return str(self.profil.d['pilot'].get('userName', ''))

    @property
    def world(self):
        w = self.oturum.world if self.oturum is not None else None
        return w if w is not None and w.running else None

    def gonder(self, msgs, note=None):
        """Bağlıysa istemcisine (bağlantı kapanmışsa sessizce düşer) -> gitti mi."""
        s = self.oturum
        if s is None or not msgs:
            return False
        try:
            s.send(msgs, note)
            return True
        except (OSError, ConnectionError):
            return False


def hepsi():
    """kimlik -> Kisi: sunucunun oyuncusu ve bitmemiş misafir oturumları."""
    g = OYUN
    if g is None:
        return {}
    host = g.PROFIL
    cur = g.CURRENT
    out = {host.user_id: Kisi(host, cur if cur is not None and cur.profil is host else None)}
    for m in CO.liste():
        if m.profil is not None:
            s = m.session
            out[m.profil.user_id] = Kisi(m.profil, s if s is not None and s.profil is m.profil else None)
    return out


def bul(ad=None, uid=None):
    """Kimliğe ya da ada (büyük/küçük harf ayrımsız) göre oyuncu ya da None."""
    kisiler = hepsi()
    if uid is not None:
        return kisiler.get(uid)
    ad = str(ad or '').strip().lower()
    return next((k for k in kisiler.values() if ad and k.ad.lower() == ad), None) if ad else None


def kisi(profil):
    """Profilin Kisi'si (oturumuyla) ya da yalnız profille (sunucudan düşmüş)."""
    return hepsi().get(profil.user_id) or Kisi(profil, None)
