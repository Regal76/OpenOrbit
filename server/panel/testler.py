"""Testleri panelden çalıştırma (yol haritası Ö2): server/test/test_*.py dosyaları sırayla, her biri ayrı süreçte (python -I,
server klasöründe; -X utf8: çıktı UTF-8, -I ortam değişkenlerini yok saydığı için) çalışır. Her birinin sonucu (geçti, kaldı, zaman aşımı), süresi, özeti (testin son "TAMAM: …" satırı ya da hata) ve
son çıktı satırları panelde görünür. Aynı anda tek koşu; durdurulabilir. Testler sabit port açmadığı için oyun açıkken de çalışır
(yalnız işlemciyi paylaşır)."""
import glob, os, subprocess, threading, time

from dil import t as _

ZAMAN_ASIMI_SN = 600          # tek test dosyası için
CIKTI_SATIR = 60              # sonuçta saklanan son satırlar


class Testler:
    def __init__(self, server, python, log=print, no_window=0):
        self.server, self.python, self.log, self.no_window = server, python, log, no_window
        self.lock = threading.Lock()
        self.sonuclar, self.calisiyor, self.baslangic, self.bitis = [], False, None, None
        self.proc, self.dur = None, False

    def files(self):
        return sorted(os.path.basename(p) for p in glob.glob(os.path.join(self.server, 'test', 'test_*.py')))

    def state(self):
        with self.lock:
            res = [dict(r) for r in self.sonuclar]
        known = {r['ad'] for r in res}
        res += [{'ad': f, 'durum': 'yok'} for f in self.files() if f not in known]
        count = lambda d: sum(1 for r in res if r['durum'] == d)
        return {'calisiyor': self.calisiyor, 'baslangic': self.baslangic, 'bitis': self.bitis, 'sonuclar': res,
                'ozet': {'gecti': count('gecti'), 'kaldi': count('kaldi') + count('zaman_asimi'), 'toplam': len(res)}}

    def start(self, names=None):
        with self.lock:
            if self.calisiyor:
                raise RuntimeError(_('Testler zaten çalışıyor.'))
            files = self.files()
            sel = [f for f in files if not names or f in names]
            if not sel:
                raise RuntimeError(_('Çalıştırılacak test bulunamadı.'))
            self.sonuclar = [{'ad': f, 'durum': 'bekliyor'} for f in sel]
            self.calisiyor, self.dur, self.baslangic, self.bitis = True, False, time.time(), None
        threading.Thread(target=self._run, daemon=True).start()
        self.log('testler başladı: %d dosya' % len(sel))
        return self.state()

    def stop(self):
        self.dur = True
        p = self.proc
        if p and p.poll() is None:
            try:
                p.kill()
            except OSError:
                pass
        return self.state()

    def _run(self):
        env = dict(os.environ)
        try:
            for r in self.sonuclar:
                if self.dur:
                    r['durum'] = 'atlandi'
                    continue
                r['durum'], t0 = 'calisiyor', time.time()
                try:
                    self.proc = subprocess.Popen([self.python, '-I', '-X', 'utf8', os.path.join(self.server, 'test', r['ad'])], cwd=self.server, env=env,
                                                 stdout=subprocess.PIPE, stderr=subprocess.STDOUT, creationflags=self.no_window)
                    try:
                        out, _ = self.proc.communicate(timeout=ZAMAN_ASIMI_SN)
                        status = 'gecti' if self.proc.returncode == 0 else 'atlandi' if self.dur else 'kaldi'
                    except subprocess.TimeoutExpired:
                        self.proc.kill()
                        out, _ = self.proc.communicate()
                        status = 'zaman_asimi'
                    lines = out.decode('utf-8', 'replace').replace('\r\n', '\n').rstrip('\n').split('\n') if out else []
                except OSError as e:
                    status, lines = 'kaldi', ['Başlatılamadı: %r' % e]
                done = [l for l in lines if l.startswith('TAMAM')]
                err = next((l for l in reversed(lines) if l.strip() and not l.startswith(' ')), '')
                r.update(durum=status, sure_sn=round(time.time() - t0, 1), cikti=lines[-CIKTI_SATIR:], kod=self.proc.returncode if self.proc else None,
                         ozet=(done[-1] if done and status == 'gecti' else err)[:300])
        finally:
            self.proc, self.calisiyor, self.bitis = None, False, time.time()
            s = self.state()['ozet']
            self.log('testler bitti: %d geçti, %d kaldı' % (s['gecti'], s['kaldi']))
