"""Kayıt ve panel yolları (yönetim paneli, panel/): profil, web ayarları, oyun ayarları.

  save/kayitlar/<kimlik>/profil.json     kayıt yuvasının profili (oyun sunucusu yazar)
  save/kayitlar/<kimlik>/web_ayarlari.json  giriş ekranının dili (web.py, profilin yanında)
  save/kayitlar/<kimlik>/kayit.json      yuvanın adı, notu, tarihleri (panel)
  save/kayitlar/<kimlik>/yedek/          yedekler (panel)
  save/panel.json                        panel ayarları: etkin yuva, istemci klasörü, görüntü, yedekleme …
  save/ayarlar.json                      oyun ayarları (ayar.py)
Etkin yuva panel.json'un 'aktif_kayit'ı. Eski düzen (save/profil.json) panel ilk açılınca 'ana' yuvasına taşınır; taşınmadıysa ya da
etkin yuva yoksa profil yolu eski dosyadır (game.py / web.py --profil olmadan çalışınca).
Yalnız standart kitaplık: web.py, game.py ve panel birlikte kullanır.
"""
import json, os

HERE = os.path.dirname(os.path.abspath(__file__))
SAVE = os.environ.get('DO_KAYIT_KLASORU') or os.path.join(HERE, 'save')      # testler geçici klasör verir
KAYITLAR = os.path.join(SAVE, 'kayitlar')
SILINENLER = os.path.join(SAVE, 'silinenler')
PANEL = os.path.join(SAVE, 'panel.json')
AYARLAR = os.path.join(SAVE, 'ayarlar.json')
ESKI_PROFIL = os.path.join(SAVE, 'profil.json')
LOGS = os.environ.get('DO_GUNLUK_KLASORU') or os.path.join(HERE, 'logs')


def panel_config(path=PANEL):
    try:
        with open(path, encoding='utf8') as fh:
            d = json.load(fh)
        return d if isinstance(d, dict) else {}
    except (OSError, ValueError):
        return {}


def slot_dir(slot, root=KAYITLAR):
    return os.path.join(root, slot)


def active_slot(path=PANEL):
    s = panel_config(path).get('aktif_kayit')
    return s if isinstance(s, str) and s and os.path.isdir(slot_dir(s)) else None


def profile_path(slot=None):
    """Yuvanın (verilmezse etkin yuvanın) profil dosyası; yuva yoksa eski save/profil.json."""
    slot = slot or active_slot()
    return os.path.join(slot_dir(slot), 'profil.json') if slot else ESKI_PROFIL
