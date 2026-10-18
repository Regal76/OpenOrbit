"""Omega AutoTactic (otomatik pilot; yol haritası Aşama 9; kaynak darkorbitwiki ve istemcinin kodu).

İstemci kendisi oynar (HangUpAI: uzaylıya saldırı, kutu toplama, cephane alımı ShopItemBuyRequest 'ammunition', yetenekler, düşük
canda onarım robotu ve güvenli bölge; Galaksi Kapısında sonraki dalgaya atlama); bunlar sunucuya sıradan isteklerle gelir. F12 ya da
pencerenin APPLY&START düğmesi Premium ister ("You need to purchase the Premium Pack to operater."; tek oyunculuda herkes Premium).
Sunucunun işi:
  AutopilotInfoRequest                  -> AutopilotInfoCommand {remainingSeconds, laserRange, result, autopilotInfos (ayarların JSON'u)}
  AutopilotInfoSaveRequest {autopilotInfos} -> AutopilotInfoSaveCommand {result}; ayarlar profilde
  AutopilotStatus {status: 0 START, 1 STOP}  istemcinin bildirimi (girişte, hareket edince STOP); günlüğe yazılır, süre sayılır
Profilde: otopilot {ayar, durum, baslangic, toplam_sn, oturum}.
"""
import json, os, time

HERE = os.path.dirname(os.path.abspath(__file__))
D = json.load(open(os.path.join(HERE, 'data', 'yeni_sistemler.json'), encoding='utf8'))['otopilot']
START, STOP = 0, 1
REQUESTS = {'AutopilotInfoRequest', 'AutopilotInfoSaveRequest', 'AutopilotStatus'}


class Otopilot:
    def __init__(self, profil, log=print):
        self.p, self.log = profil, log
        self.laser_range = lambda: D['lazer_menzil']      # oturum bağlar: dünyanın lazer menzili
        with profil.lock:
            self.d = profil.d.setdefault('otopilot', {'ayar': '', 'durum': STOP, 'baslangic': 0, 'toplam_sn': 0, 'oturum': 0})
            self.d['durum'] = STOP                        # yeni oturum: istemci girişte STOP bildirir

    def info_cmd(self):
        # tek oyunculuda herkes Premium (gerçek parayla satılıyor, uridyumla karşılığı yok): kayıttaki hesabın premium'u false'du,
        # F12 "You need to purchase the Premium Pack" diyordu (canlı test H72). Kural; profil alanına bakılmaz, profile yazılmaz
        premium = True
        return 'AutopilotInfoCommand', dict(remainingSeconds=D['premium_sn'] if premium else 0, laserRange=int(self.laser_range()),
                                            result=premium, autopilotInfos=self.d.get('ayar') or '')

    def handle(self, name, f, now=None):
        now = now or time.time()
        if name == 'AutopilotInfoRequest':
            return [self.info_cmd()]
        if name == 'AutopilotInfoSaveRequest':
            text = f.get('autopilotInfos') or ''
            try:
                json.loads(text) if text else None
                ok = True
            except ValueError:
                ok = False
            if ok:
                with self.p.lock:
                    self.d['ayar'] = text
                    self.p.dirty = True
            self.log('   otomatik pilot ayarları %s (%d karakter)' % ('kaydedildi' if ok else 'geçersiz', len(text)))
            return [('AutopilotInfoSaveCommand', {'result': ok})]
        if name == 'AutopilotStatus':
            st = f.get('status')
            st = st.get('typeValue', st) if isinstance(st, dict) else st
            st = int(st or 0)
            with self.p.lock:
                if st == START and self.d['durum'] != START:
                    self.d.update(durum=START, baslangic=now, oturum=self.d.get('oturum', 0) + 1)
                    self.log('   otomatik pilot başladı')
                elif st == STOP and self.d['durum'] == START:
                    dt = max(0, int(now - self.d.get('baslangic', now)))
                    self.d.update(durum=STOP, toplam_sn=self.d.get('toplam_sn', 0) + dt)
                    self.log('   otomatik pilot durdu (%d sn)' % dt)
                self.p.dirty = True
            return []
        return []
