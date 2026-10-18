"""Panelin dili: Türkçe ya da İngilizce (ilk açılışta kurulum sihirbazında seçilir; save/panel.json 'dil', Panel sayfasından değişir).

Metinler kodda Türkçe yazılır; İngilizceleri arayuz/en.json'da, anahtar Türkçe metnin kendisi (gettext gibi). Arayüz (panel.js T())
ve Python (t()) aynı sözlüğü kullanır; sözlükte olmayan metin Türkçe kalır. Biçim: Python metinlerinde %s, arayüzde {0} {1} …
Eksik ya da biçimi tutmayan çevirileri test/test_panel_dil.py yakalar.
"""
import json, os, threading

DILLER = ('tr', 'en')
SOZLUK = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'arayuz', 'en.json')
_secili = None                  # panel bağlar: () -> 'tr' | 'en' | None
_en = None
_lock = threading.Lock()


def bagla(fn):
    """Seçili dili veren işlevi bağla (panel: CFG.get('dil'))."""
    global _secili
    _secili = fn


def current():
    try:
        d = _secili() if _secili else None
    except Exception:
        d = None
    return d if d in DILLER else 'tr'


def sozluk():
    global _en
    with _lock:
        if _en is None:
            try:
                with open(SOZLUK, encoding='utf8') as fh:
                    _en = json.load(fh)
            except (OSError, ValueError):
                _en = {}
        return _en


def t(text, *args):
    """Metnin seçili dildeki hâli; args varsa % ile biçimlenir."""
    if text and current() == 'en':
        text = sozluk().get(text, text)
    return text % args if args else text
