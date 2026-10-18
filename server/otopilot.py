"""Omega AutoTactic (otomatik pilot; yol haritası Aşama 9; kaynak darkorbitwiki ve istemcinin kodu).

İstemci kendisi oynar (HangUpAI: uzaylıya saldırı, kutu toplama, cephane alımı ShopItemBuyRequest 'ammunition', yetenekler, düşük
canda onarım robotu ve güvenli bölge; Galaksi Kapısında sonraki dalgaya atlama); bunlar sunucuya sıradan isteklerle gelir. F12 ya da
pencerenin APPLY&START düğmesi Premium ister ("You need to purchase the Premium Pack to operater."; tek oyunculuda herkes Premium).
Sunucunun işi:
  AutopilotInfoRequest                  -> AutopilotInfoCommand {remainingSeconds, laserRange, result, autopilotInfos (ayarların JSON'u)}
  AutopilotInfoSaveRequest {autopilotInfos} -> AutopilotInfoSaveCommand {result}; ayarlar profilde
  AutopilotStatus {status: 0 START, 1 STOP}  istemcinin bildirimi (girişte, hareket edince STOP); günlüğe yazılır, süre sayılır
Profilde: otopilot {ayar, durum, baslangic, toplam_sn, oturum, secim}.

Seçili uzaylılar ve kutular (2026-10-18, kullanıcı bildirimi: harita değişince seçimler sıfırlanıyor, listede yalnız görüştekiler):
  - İstemci seçimleri haritaya göre tutuyor (NPCSelectedList / CollectSelectedList: harita -> liste; ayarların kendisi PlayerPrefs
    "AutoAFKData"da, bilgi gelince yazılıyor). Pencere açılınca bulunduğu haritanın anahtarı yoksa sözlüğü yenisiyle değiştiriyor
    (UIAssistantSystem.UpdateInfo): öteki haritaların seçimleri siliniyor, kayıtta yalnız yeni harita gidiyordu. Otomatik pilotun
    kutu süzgeci de anahtarı doğrudan okuyor (UnitComponentSystem.GetCollectables). Sunucu seçimi haritadan bağımsız tutar (secim) ve
    her haritanın anahtarıyla gönderir: kutular her haritada aynı, uzaylılardan o haritada çıkanlar (npc.json'un tablosu, haritada
    yaşayanlar, o haritada seçilmişler). Kayıtta her anahtar istemcinin elindekiyle karşılaştırılır; eklenen seçilir, çıkarılan bırakılır.
  - Sağdaki listeleri istemci yalnız tanıdığı birimlerden ve kutulardan kuruyor (GetNPCIDList, GetBoxList; saniyede bir). Pencere
    açıldıktan sonra (elle uçulana dek) ve otomatik pilot çalışırken haritanın bütün uzaylıları ve kutuları bildirilir (reveal; dunya.py
    in_view): listede haritanın tümü çıkar, otomatik pilot uzaktaki hedefe de gider.
"""
import json, os, time

HERE = os.path.dirname(os.path.abspath(__file__))
D = json.load(open(os.path.join(HERE, 'data', 'yeni_sistemler.json'), encoding='utf8'))['otopilot']
START, STOP = 0, 1
REQUESTS = {'AutopilotInfoRequest', 'AutopilotInfoSaveRequest', 'AutopilotStatus'}
NPC_LIST, BOX_LIST = 'NPCSelectedList', 'CollectSelectedList'     # AssistantData: harita -> NpcData {Name, NpcID, NpcType} / "box_<tür>"
SINIR = 40000              # gönderilen JSON'un üst sınırı (protokolde metin en çok 65.535 bayt; istemci kaydederken aynısını yollar)


def _maps(v):
    """Ayarların harita -> liste sözlüğü (bozuksa boş)."""
    return {str(k): x for k, x in v.items() if isinstance(x, list)} if isinstance(v, dict) else {}


def _npc_key(e):
    return (e.get('Name') or None) if isinstance(e, dict) else None     # istemcinin de eşleştirdiği alan (NpcData.Name)


def _box_key(e):
    return (e or None) if isinstance(e, str) else None


def _num(k):
    return (0, int(k)) if k.isdigit() else (1, k)


class Otopilot:
    def __init__(self, profil, log=print):
        self.p, self.log = profil, log
        self.laser_range = lambda: D['lazer_menzil']      # oturum bağlar: dünyanın lazer menzili
        self.maps = lambda: (None, {})                    # oturum bağlar: (bulunulan harita, harita -> orada çıkan uzaylıların adları)
        self.pencere = False                              # pencere açıldı, elle uçulmadı: haritanın tümü bildirilir (reveal)
        with profil.lock:
            self.d = profil.d.setdefault('otopilot', {'ayar': '', 'durum': STOP, 'baslangic': 0, 'toplam_sn': 0, 'oturum': 0})
            self.d['durum'] = STOP                        # yeni oturum: istemci girişte STOP bildirir

    # ------------------------------------------------------------ seçimler
    def selection(self):
        """Haritadan bağımsız seçim {npc: [NpcData], kutu: [ad], npc_harita: ad -> seçildiği haritalar}. Önceki kayıtta yoksa
        haritalara göre listelerin birleşimi."""
        s = self.d.get('secim')
        if s is None:
            s = {'npc': [], 'kutu': [], 'npc_harita': {}}
            try:
                old = json.loads(self.d.get('ayar') or '{}')
            except ValueError:
                old = {}
            self.merge(s, {}, old if isinstance(old, dict) else {})
            self.d['secim'] = s
        return s

    @staticmethod
    def merge(s, old, new):
        """Kaydedilen ayarların seçimlerini haritadan bağımsız seçime işler: her haritanın listesi istemcinin elindekiyle (sunucunun
        son gönderdiği ya da istemcinin son kaydettiği) karşılaştırılır, eklenen seçilir, çıkarılan bırakılır. İstemci yalnız
        bulunduğu haritanınkini değiştirir; ötekiler aynı geldiğinden bir şey değiştirmez."""
        for field, key, store in ((NPC_LIST, _npc_key, 'npc'), (BOX_LIST, _box_key, 'kutu')):
            before = _maps(old.get(field))
            for mid, items in _maps(new.get(field)).items():
                prev = {key(e) for e in before.get(mid, [])}
                now = {key(e) for e in items}
                gone = prev - now
                if gone:
                    s[store] = [e for e in s[store] if key(e) not in gone]
                have = {key(e) for e in s[store]}
                for e in items:
                    k = key(e)
                    if k is None or k in prev:
                        continue
                    if k not in have:
                        s[store].append(e)
                        have.add(k)
                    if store == 'npc' and mid not in s['npc_harita'].setdefault(k, []):
                        s['npc_harita'][k].append(mid)

    def info_json(self, cur=None, names=None):
        """İstemciye gidecek ayarlar: kaydedilenler, seçim listeleri her haritanın anahtarıyla (bulunulan harita cur önce; sınıra
        dek). names: harita -> orada çıkan uzaylıların adları. Hiç ayar yoksa boş (istemci kendi varsayılanını kurar)."""
        names = names or {}
        text = self.d.get('ayar') or ''
        s = self.selection()
        if not text and not s['npc'] and not s['kutu']:
            return ''
        try:
            base = json.loads(text) if text else {}
        except ValueError:
            base = {}
        base = base if isinstance(base, dict) else {}
        here = {m for ms in s['npc_harita'].values() for m in ms} | set(names) | set(_maps(base.get(NPC_LIST))) | \
            set(_maps(base.get(BOX_LIST)))
        order = ([cur] if cur else []) + sorted(here - {cur}, key=_num)
        npcs, boxes = {}, {}
        base[NPC_LIST], base[BOX_LIST] = npcs, boxes
        size = len(json.dumps(base, separators=(',', ':')))
        box_cost = len(json.dumps(s['kutu'], separators=(',', ':')))
        for mid in order:
            seen = set(names.get(mid, ())) | {k for k, ms in s['npc_harita'].items() if mid in ms}
            row = [e for e in s['npc'] if _npc_key(e) in seen]
            cost = len(json.dumps(row, separators=(',', ':'))) + box_cost + 2 * len(mid) + 8
            if size + cost > SINIR and mid != cur:
                break
            npcs[mid], boxes[mid] = row, list(s['kutu'])
            size += cost
        return json.dumps(base, separators=(',', ':'))

    def info_cmd(self):
        # tek oyunculuda herkes Premium (gerçek parayla satılıyor, uridyumla karşılığı yok): kayıttaki hesabın premium'u false'du,
        # F12 "You need to purchase the Premium Pack" diyordu (canlı test H72). Kural; profil alanına bakılmaz, profile yazılmaz
        premium = True
        cur, names = self.maps()                          # dünyanın kilidi profilinkinden önce (dışında) alınır
        with self.p.lock:
            text = self.info_json(cur, names)
            if text != (self.d.get('ayar') or ''):
                self.d['ayar'] = text                     # istemcinin elindeki: sonraki kayıt bununla karşılaştırılır
                self.p.dirty = True
        return 'AutopilotInfoCommand', dict(remainingSeconds=D['premium_sn'] if premium else 0, laserRange=int(self.laser_range()),
                                            result=premium, autopilotInfos=text)

    # ------------------------------------------------------------ haritanın tümü
    def reveal(self):
        """Haritanın bütün uzaylıları ve kutuları istemciye bildirilsin mi: pencere açıldıktan sonra (elle uçulana dek) ya da otomatik
        pilot çalışırken (dunya.py in_view okur)."""
        return self.pencere or self.d.get('durum') == START

    def manual_move(self):
        """Oyuncunun hareket isteği: otomatik pilot çalışmıyorsa elle uçuyor, pencere kapanmış sayılır."""
        if self.d.get('durum') != START:
            self.pencere = False

    def handle(self, name, f, now=None):
        now = now or time.time()
        if name == 'AutopilotInfoRequest':
            self.pencere = True
            return [self.info_cmd()]
        if name == 'AutopilotInfoSaveRequest':
            text = f.get('autopilotInfos') or ''
            try:
                new = json.loads(text) if text else None
                ok = True
            except ValueError:
                ok = False
            if ok:
                with self.p.lock:
                    s = self.selection()
                    try:
                        old = json.loads(self.d.get('ayar') or '{}')
                    except ValueError:
                        old = {}
                    self.merge(s, old if isinstance(old, dict) else {}, new if isinstance(new, dict) else {})
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
                    self.pencere = False                  # elle uçuldu (istemci hareket edince durdurur)
                    self.log('   otomatik pilot durdu (%d sn)' % dt)
                self.p.dirty = True
            return []
        return []
