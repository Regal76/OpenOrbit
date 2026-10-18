# DarkOrbit Server Emulator

**[English](#english)** · **[Türkçe](#türkçe)**

A single-player, offline server for the original DarkOrbit Unity client, with a desktop management panel.
Orijinal DarkOrbit Unity istemcisi için tek oyunculu, çevrimdışı sunucu ve masaüstü yönetim paneli.

---

## English

### What it is

DarkOrbit Server Emulator runs a local server on your computer and starts the **original DarkOrbit client** against it.
You play alone and offline: the client never connects to the official servers, its files are never changed, and no
internet connection is needed. A management panel starts the game and handles your saves, game settings and events.

### Features

- **Your own account:** the full account interface (windows, missions, Season Pass, Command Center) with progress that
  is saved locally.
- **Combat and the world:** aliens on every map, lasers, rockets, launchers, mines, ship abilities, bonus and cargo boxes,
  mining and refining, portals and death screens.
- **Equipment:** shop, hangar, ships and designs, drones and formations, P.E.T., boosters. Items that are sold for real
  money on the official servers can be bought with uridium.
- **Galaxy Gates and modes:** Galaxy Gates (Kronos included), event gates, Voyagers' Ascent, Trinity Trials, Astral
  Ascension, Deep Space Echoes, Eternal Black Light and more.
- **Systems:** Assembly, Dispatch, Skylab, Uridium Bank, Synthesis, N.O.V.A., Armory, Quantum Fluid Core, particle
  cannons, Singularity Drive, Omega AutoTactic, pilot skills, achievements and titles, ranks, daily login, Battle Pass.
- **Events:** yearly and weekly events follow the real calendar; you can switch each one on or off in the panel.
- **Social, single-player:** chat, mail, clans and the auction (with optional virtual rivals). Bot players are planned.

### The management panel

- **First-run setup wizard:** language (English or Turkish), game folder, your first pilot and game settings.
- **Play:** your active save, the PLAY button, launch steps, warnings and live status while you play.
- **Saves:** several save slots; create, rename, copy, export and import (.zip), edit (credits, uridium, give items,
  repair the ship …), and automatic or manual backups that you can restore.
- **Game Settings:** multipliers and rules (damage, rewards, drop chances, alien and box counts, prices, cooldowns …),
  presets such as Relaxed, Fast progress and Hard, and your own templates. Most settings apply while you play.
- **Events:** each event by calendar, or on / off by hand.
- **Client:** game folder, version check, window mode, resolution and display.
- **Server:** processes, ports, behavior and live logs.

### Requirements

- Windows 10 or 11.
- [Python](https://www.python.org/downloads/windows/) 3.10 or newer. Nothing else is needed to play.
- The **original DarkOrbit Unity client**, version **1.1.114** (not included). The folder must contain `DarkOrbit.exe`
  and `DarkOrbit_Data`.
- Microsoft Edge or Google Chrome for the panel window (otherwise your default browser opens it).
- Optional: `pip install capstone`, only if you want to adapt the server to a newer client version (Client page).

### Quick start

1. Download this repository (Code > Download ZIP) and extract it, or clone it.
2. Double-click **`DarkOrbit Panel.pyw`**. The panel opens in its own window; no console window appears.
3. Follow the setup wizard: choose a language, pick the DarkOrbit game folder (it is found automatically in the usual
   places), create your first pilot and choose a preset.
4. Press **PLAY**. The servers start and the game opens. On the client's login screen press START.

You can run the wizard again at any time from the **Panel** page, where you can also switch the language and put a
desktop shortcut on your desktop.

### In-game tips

- Choose the game's own language on the client's login screen (the selector at the top, before START).
- 2D or 3D: Settings > Display > Choose 2D version, Save, OK; the game opens in that mode next time you enter.
- Missions are taken at Mission Control in the stations. Quit with the in-game logout button: it saves cleanly.
- Game Settings > Developer > GM console turns on the game's hidden admin window (Ctrl, then Shift, then Z in the game):
  teleport, spawn aliens and boxes, give items, finish missions, reset cooldowns.

### Where your data is

| Path | Contents |
| --- | --- |
| `server/save/kayitlar/<save>/` | A save slot: `profil.json` and its backups (`yedek/`) |
| `server/save/ayarlar.json` | Game settings and event choices |
| `server/save/panel.json` | Panel settings (language, game folder, display, backups) |
| `server/logs/` | Server, client and panel logs |

All of these are created on first run and stay on your computer.

### Good to know

- Don't run `DarkorbitLauncher.exe` from the client folder: it may update the client from the official servers and break
  compatibility. Start the game from the panel.
- The server is written for client version 1.1.114. For another version the panel warns you and can adapt the protocol
  from the new client's code (Client page; needs `capstone`).
- The login templates (`server/data/giris.json`, `haritalar.json`, `yanitlar.json`) are not part of this repository.
  Without them the game starts with a minimal login, and some windows and the shop may be empty; the panel shows a
  warning in that case.
- Bot players are not in yet: missions that need other players don't progress.

### Legal

This is a fan project for personal, offline use. It is not affiliated with or endorsed by Bigpoint GmbH. DarkOrbit, the
client, graphics, sounds and texts belong to Bigpoint GmbH; part of the game data is compiled from darkorbitwiki.com.
Don't use it to connect to or harm the official servers.

---

## Türkçe

### Nedir

DarkOrbit Server Emulator bilgisayarında yerel bir sunucu çalıştırır ve **orijinal DarkOrbit istemcisini** ona bağlar.
Tek başına ve çevrimdışı oynarsın: istemci resmî sunuculara bağlanmaz, dosyaları değiştirilmez, internet gerekmez. Bir
yönetim paneli oyunu başlatır; kayıtlarını, oyun ayarlarını ve etkinlikleri yönetir.

### Özellikler

- **Kendi hesabın:** hesabın tam arayüzü (pencereler, görevler, Season Pass, Command Center); ilerleme yerelde saklanır.
- **Savaş ve dünya:** her haritada uzaylılar, lazer, roket, fırlatıcı, mayın, gemi yetenekleri, bonus ve kargo kutuları,
  maden ve rafine, portallar, ölüm ekranı.
- **Donanım:** mağaza, hangar, gemiler ve tasarımlar, dronlar ve formasyonlar, P.E.T., boosterlar. Resmî sunucularda
  gerçek parayla satılan eşyalar uridyumla alınır.
- **Galaksi Kapıları ve modlar:** Galaksi Kapıları (Kronos dahil), etkinlik kapıları, Voyagers' Ascent, Trinity Trials,
  Astral Ascension, Deep Space Echoes, Eternal Black Light ve dahası.
- **Sistemler:** Assembly, Dispatch, Skylab, Uridium Bank, Synthesis, N.O.V.A., Armory, Quantum Fluid Core, parçacık
  topları, Singularity Drive, Omega AutoTactic, pilot yetenekleri, başarımlar ve unvanlar, rütbe, günlük giriş, Battle Pass.
- **Etkinlikler:** yıllık ve haftalık etkinlikler gerçek takvime göre açılır; her birini panelden açıp kapatabilirsin.
- **Sosyal, tek oyunculu:** sohbet, posta, klan ve müzayede (isteğe bağlı sanal rakiplerle). Bot oyuncular planlanıyor.

### Yönetim paneli

- **İlk açılışta kurulum sihirbazı:** dil (Türkçe ya da İngilizce), oyun klasörü, ilk pilotun ve oyun ayarları.
- **Oyna:** etkin kaydın, OYNA düğmesi, başlatma adımları, uyarılar ve oynarken canlı durum.
- **Kayıtlar:** birden çok kayıt yuvası; oluştur, yeniden adlandır, kopyala, dışa ve içe aktar (.zip), düzenle (kredi,
  uridyum, eşya ver, gemiyi onar …), otomatik ya da elle yedekler ve geri yükleme.
- **Oyun Ayarları:** çarpanlar ve kurallar (hasar, ödüller, düşme şansı, uzaylı ve kutu sayısı, fiyatlar, beklemeler …),
  Rahat, Hızlı ilerleme, Zorlu gibi hazır ayarlar ve kendi şablonların. Çoğu ayar oynarken uygulanır.
- **Etkinlikler:** her etkinlik takvime göre ya da elle açık / kapalı.
- **İstemci:** oyun klasörü, sürüm denetimi, pencere kipi, çözünürlük ve ekran.
- **Sunucu:** süreçler, portlar, davranış ve canlı günlükler.

### Gereksinimler

- Windows 10 ya da 11.
- [Python](https://www.python.org/downloads/windows/) 3.10 ya da daha yenisi. Oynamak için başka bir şey gerekmez.
- **Orijinal DarkOrbit Unity istemcisi**, sürüm **1.1.114** (depoda yok). Klasörde `DarkOrbit.exe` ve `DarkOrbit_Data`
  olmalı.
- Panel penceresi için Microsoft Edge ya da Google Chrome (yoksa varsayılan tarayıcın açar).
- İsteğe bağlı: `pip install capstone`; yalnız sunucuyu daha yeni bir istemci sürümüne uyarlamak istersen (İstemci sayfası).

### Hızlı başlangıç

1. Bu depoyu indir (Code > Download ZIP) ve aç ya da klonla.
2. **`DarkOrbit Panel.pyw`** dosyasına çift tıkla. Panel kendi penceresinde açılır; konsol penceresi çıkmaz.
3. Kurulum sihirbazını izle: dili seç, DarkOrbit oyun klasörünü seç (bilinen yerlerde kendiliğinden bulunur), ilk pilotunu
   oluştur ve bir hazır ayar seç.
4. **OYNA**'ya bas. Sunucular başlar, oyun açılır. İstemcinin giriş ekranında START'a bas.

Sihirbazı istediğin zaman **Panel** sayfasından yeniden açabilirsin; dili değiştirmek ve masaüstüne kısayol koymak da
orada.

### Oyun içi ipuçları

- Oyunun kendi dilini istemcinin giriş ekranında seç (START'tan önce üstteki seçici).
- 2D ya da 3D: Ayarlar > Display > Choose 2D version, Save, OK; oyuna yeniden girince o kipte açılır.
- Görevler istasyonlardaki Mission Control'den alınır. Oyundan çıkış düğmesiyle çık: kayıt sorunsuz kapanır.
- Oyun Ayarları > Geliştirici > GM konsolu oyunun gizli yönetici penceresini açar (oyunda Ctrl, ardından Shift, ardından Z):
  ışınlanma, uzaylı ve kutu doğurma, eşya verme, görevleri bitirme, beklemeleri sıfırlama.

### Verilerin nerede

| Yol | İçerik |
| --- | --- |
| `server/save/kayitlar/<kayıt>/` | Bir kayıt yuvası: `profil.json` ve yedekleri (`yedek/`) |
| `server/save/ayarlar.json` | Oyun ayarları ve etkinlik seçimleri |
| `server/save/panel.json` | Panel ayarları (dil, oyun klasörü, görüntü, yedekleme) |
| `server/logs/` | Sunucu, istemci ve panel günlükleri |

Hepsi ilk açılışta oluşur ve bilgisayarında kalır.

### Bilmekte yarar var

- İstemci klasöründeki `DarkorbitLauncher.exe`'yi çalıştırma: istemciyi resmî sunuculardan güncelleyip uyumu bozabilir.
  Oyunu panelden başlat.
- Sunucu 1.1.114 istemcisi için yazıldı. Başka bir sürümde panel uyarır ve protokolü yeni istemcinin kodundan uyarlayabilir
  (İstemci sayfası; `capstone` gerekir).
- Giriş şablonları (`server/data/giris.json`, `haritalar.json`, `yanitlar.json`) bu depoda yok. Onlar olmadan oyun en
  küçük girişle açılır; bazı pencereler ve mağaza boş kalabilir, panel bu durumda uyarır.
- Bot oyuncular henüz yok: başka oyuncu gerektiren görevler ilerlemez.

### Yasal not

Kişisel, çevrimdışı kullanım için bir hayran projesidir; Bigpoint GmbH ile bağlantısı yoktur, onun onayını taşımaz.
DarkOrbit, istemci, grafikler, sesler ve metinler Bigpoint GmbH'ye aittir; oyun verilerinin bir kısmı darkorbitwiki.com'dan
derlenmiştir. Resmî sunuculara bağlanmak ya da onlara zarar vermek için kullanma.
