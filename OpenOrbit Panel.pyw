"""OpenOrbit yerel sunucu paneli: çift tıkla (konsol penceresi açılmaz). Oyun, ayarlar ve kayıtlar buradan yönetilir.
OpenOrbit local server panel: double-click to start (no console window). The game, settings and saves are managed here.

Panel yerel bir pencerede açılır; ilk açılışta kurulum sihirbazı (dil, oyun klasörü, ilk pilot, oyun ayarları). OYNA'ya basınca
sunucular başlar ve oyun açılır. Ayrıntı: README.md, server/panel/panel.py.
"""
import os
import runpy
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PANEL = os.path.join(HERE, 'server', 'panel', 'panel.py')

if sys.version_info < (3, 10):
    import ctypes
    v = sys.version.split()[0]
    ctypes.windll.user32.MessageBoxW(0, 'OpenOrbit Panel için Python 3.10 ya da daha yenisi gerekir.\nBu Python: %s\n\n'
                                        'OpenOrbit Panel needs Python 3.10 or newer.\nThis Python: %s' % (v, v), 'OpenOrbit Panel', 0x10)
    sys.exit(1)
sys.argv = [PANEL] + sys.argv[1:]
runpy.run_path(PANEL, run_name='__main__')
