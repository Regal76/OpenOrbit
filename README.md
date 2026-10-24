<h1 align="center"><img src="docs/img/logo.png" alt="OpenOrbit" width="560"></h1>

**[English](#english)** · **[Türkçe](#türkçe)** · **[Discord](https://discord.gg/BUb9rNTKNt)**

[![Discord](https://img.shields.io/badge/Discord-Join%20%C2%B7%20Kat%C4%B1l-5865F2?logo=discord&logoColor=white)](https://discord.gg/BUb9rNTKNt)

A single-player, offline server for the original DarkOrbit Unity client, with a desktop management panel.
Orijinal DarkOrbit Unity istemcisi için tek oyunculu, çevrimdışı sunucu ve masaüstü yönetim paneli.

![The original client on the local server · Yerel sunucuda orijinal istemci](docs/img/game.jpg)

| Play · Oyna | Play with Friends · Arkadaşlarınla Oyna |
| --- | --- |
| ![Play page · Oyna sayfası](docs/img/play.jpg) | ![Play with Friends page · Arkadaşlarınla Oyna sayfası](docs/img/friends.jpg) |
| **Game Settings · Oyun Ayarları** | **Setup wizard · Kurulum sihirbazı** |
| ![Game Settings page · Oyun Ayarları sayfası](docs/img/settings.jpg) | ![Setup wizard · Kurulum sihirbazı](docs/img/setup.jpg) |

---

## English

### What it is

OpenOrbit runs a local server on your computer and starts the **original DarkOrbit client** against it.
You play alone and offline: the client never connects to the official servers and its files are never changed. Internet
is needed only to download the game (once, if the panel does it for you), to check for updates and to fetch the game's
images from the official CDN the first time they are shown (without internet the game still runs, without those
images). A management panel starts the game and handles your saves, game settings and events.

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

- **First-run setup wizard:** language (English or Turkish), game folder (downloaded for you if it isn't on your
  computer), your first pilot and game settings.
- **Play:** your active save, the PLAY button, launch steps, warnings and live status while you play.
- **Play with Friends:** host a server or join a friend's; everyone plays with their own save (see below).
- **Saves:** several save slots; create, rename, copy, export and import (.zip), edit (credits, uridium, give items,
  repair the ship …), and automatic or manual backups that you can restore.
- **Game Settings:** multipliers and rules (damage, rewards, drop chances, alien and box counts, prices, cooldowns …),
  presets such as Relaxed, Fast progress and Hard, and your own templates. Most settings apply while you play.
- **Events:** each event by calendar, or on / off by hand.
- **Client:** game folder, game download, version check, window mode, resolution and display.
- **Server:** processes, ports, behavior and live logs.
- **Panel:** language, setup wizard, updates, desktop shortcut, folders and a button to join the Discord server.

### Playing with friends

- **Host:** on the Play with Friends page, HOST starts the server for everyone and opens the game with your own save.
  You can set a join password and the maximum number of guests. The page shows the addresses to give your friends and
  lists connected guests (you can remove one).
- **Ports:** TCP 8081 (game and account upload) and TCP 7771 (chat). No UDP port is needed; the web login (80, 8090)
  stays on your computer. Allow Python through Windows Firewall when it asks. On the same home network nothing else is
  needed; over the internet forward those two ports on your router, or use a virtual network (Radmin VPN, ZeroTier,
  Tailscale) if your provider uses CGNAT.
- **Join:** enter your friend's address (and password), pick a save and press JOIN. Your save is backed up, uploaded to
  your friend's server and the game opens. While you play, your progress is written back to your own save every few
  seconds; when you leave or close the game, its final state is saved on your computer.
- **Your save stays yours:** the host keeps guests' saves in memory only; they never appear on the host's Saves page.
- **What is shared:** company, battle and Blacklight maps (1-1 … 5-4, BL): aliens, boxes and ores, and you see each
  other. Chat is shared. Gates, modes and event maps are each player's own copy; mail, clans and the auction stay
  personal. The host's game settings apply to everyone. There is no PvP.
- Both sides need the same panel and game version.

### Requirements

- Windows 10 or 11.
- [Python](https://www.python.org/downloads/windows/) 3.10 or newer. Nothing else is needed to play.
- The **original DarkOrbit Unity client**, version **1.1.115** (not included). If the panel doesn't find it on your
  computer, the setup wizard downloads it from the game's official download server and installs it into the project
  folder: about 3.5 GB to download and 4.4 GB of free disk space. A stopped download resumes where it left off. If you
  install it yourself, the folder must contain `DarkOrbit.exe` and `DarkOrbit_Data`.
- Microsoft Edge or Google Chrome for the panel window (otherwise your default browser opens it).
- Optional: `pip install capstone`, only if you want to adapt the server to a newer client version (Client page).

### Quick start

1. Download this repository (Code > Download ZIP) and extract it, or clone it.
2. Double-click **`OpenOrbit Panel.pyw`**. The panel opens in its own window; no console window appears.
3. Follow the setup wizard: choose a language, pick the DarkOrbit game folder (it is found automatically in the usual
   places; if the game isn't on your computer, the wizard downloads it), create your first pilot and choose a preset.
4. Press **PLAY**. The servers start and the game opens. On the client's login screen press START.

You can run the wizard again at any time from the **Panel** page, where you can also switch the language and put a
desktop shortcut on your desktop.

### Updates

The panel checks this repository for a newer version shortly after it starts and then every six hours. By default it
installs the update by itself once the game and the servers are closed, then restarts; the open panel window reloads.
On the **Panel** page you can choose *Only notify* or turn it off, and check by hand.

- **Downloaded as a ZIP** (no Git needed): the new version's archive (about 2 MB) is downloaded, changed files are
  replaced and files that were removed from the project are taken out. Their old versions are kept in
  `server/save/guncelleme/` (last two updates).
- **Cloned with Git:** the panel fast-forwards with `git`. If you changed tracked files or have commits of your own, it
  changes nothing and only tells you.
- Your saves, settings, logs, personal login templates, downloaded game images and the game client are never changed.
- **Coming from the old name (DarkOrbit Server Emulator):** versions from before 24 October 2026 can't update themselves
  any more (the panel says *The archive is not this project.*). Download the ZIP once more and copy its contents over your
  folder; your saves, settings and the game stay. Then open the panel with `OpenOrbit Panel.pyw`; the **Panel** page
  replaces the old desktop shortcut when you press *Create shortcut*.

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
| `DarkOrbit_Version1.1.115/` | The game client, if the panel downloaded it (`istemci_indiriliyor/` while downloading) |
| `server/save/guncelleme/` | Old versions of the files that updates replaced (last two updates) |
| `server/cdn/do_img/` | Game images downloaded from the official CDN (news, event and window artwork) |

All of these are created on first run and stay on your computer.

### Good to know

- Don't run `DarkorbitLauncher.exe` from the client folder: it may update the client from the official servers and break
  compatibility. Start the game from the panel.
- The server is written for client version 1.1.115. For another version the panel warns you and can adapt the protocol
  from the new client's code (Client page; needs `capstone`).
- Bot players are not in yet: missions that need other players don't progress.

### Community

Join the [Discord server](https://discord.gg/BUb9rNTKNt) for announcements, help, bug reports and suggestions. It has
Turkish and English channels, and channels for screenshots and finding people to play with. You can also join from the
panel's **Panel** page.

### Legal

This is a fan project for personal, offline use. It is not affiliated with or endorsed by Bigpoint GmbH. DarkOrbit, the
client, graphics, sounds and texts belong to Bigpoint GmbH; part of the game data is compiled from darkorbitwiki.com.
Don't use it to connect to or harm the official servers.

The repository contains neither the game client nor the game's images: you download the client from Bigpoint's official
download server (or the panel does it for you), and the server fetches each image from the official CDN the first time
the game shows it and keeps it on your computer. The software is provided as is, without any warranty.

The project's own code is released under the [MIT License](LICENSE). It doesn't cover Bigpoint's client, graphics,
sounds, texts or game data.

---

## Türkçe

### Nedir

OpenOrbit bilgisayarında yerel bir sunucu çalıştırır ve **orijinal DarkOrbit istemcisini** ona bağlar.
Tek başına ve çevrimdışı oynarsın: istemci resmî sunuculara bağlanmaz, dosyaları değiştirilmez. İnternet yalnız oyunu
indirmek (panel senin için indirirse, bir kez), güncellemeleri denetlemek ve oyunun görsellerini ilk gösterildiklerinde
resmî CDN'den almak için gerekir (internet yoksa oyun yine çalışır, o görseller olmadan). Bir yönetim paneli oyunu başlatır;
kayıtlarını, oyun ayarlarını ve etkinlikleri yönetir.

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

- **İlk açılışta kurulum sihirbazı:** dil (Türkçe ya da İngilizce), oyun klasörü (bilgisayarında yoksa indirilir), ilk
  pilotun ve oyun ayarları.
- **Oyna:** etkin kaydın, OYNA düğmesi, başlatma adımları, uyarılar ve oynarken canlı durum.
- **Arkadaşlarınla Oyna:** sunucu kur ya da arkadaşının sunucusuna katıl; herkes kendi kaydıyla oynar (aşağıda).
- **Kayıtlar:** birden çok kayıt yuvası; oluştur, yeniden adlandır, kopyala, dışa ve içe aktar (.zip), düzenle (kredi,
  uridyum, eşya ver, gemiyi onar …), otomatik ya da elle yedekler ve geri yükleme.
- **Oyun Ayarları:** çarpanlar ve kurallar (hasar, ödüller, düşme şansı, uzaylı ve kutu sayısı, fiyatlar, beklemeler …),
  Rahat, Hızlı ilerleme, Zorlu gibi hazır ayarlar ve kendi şablonların. Çoğu ayar oynarken uygulanır.
- **Etkinlikler:** her etkinlik takvime göre ya da elle açık / kapalı.
- **İstemci:** oyun klasörü, oyunu indirme, sürüm denetimi, pencere kipi, çözünürlük ve ekran.
- **Sunucu:** süreçler, portlar, davranış ve canlı günlükler.
- **Panel:** dil, kurulum sihirbazı, güncellemeler, masaüstü kısayolu, klasörler ve Discord sunucusuna katılma düğmesi.

### Arkadaşlarınla oynamak

- **Host:** Arkadaşlarınla Oyna sayfasında SUNUCU KUR herkes için sunucuyu başlatır ve oyunu kendi kaydınla açar. Katılma
  şifresi ve en çok misafir sayısı seçilebilir. Sayfa arkadaşlarına vereceğin adresleri gösterir ve bağlı misafirleri
  listeler (birini çıkarabilirsin).
- **Portlar:** TCP 8081 (oyun ve hesap gönderimi) ve TCP 7771 (sohbet). UDP portu gerekmez; web girişi (80, 8090) senin
  bilgisayarında kalır. Windows Güvenlik Duvarı sorunca Python'a izin ver. Aynı ev ağında başka bir şey gerekmez;
  internet üzerinden modeminde bu iki portu yönlendir, sağlayıcın CGNAT kullanıyorsa sanal ağ kur (Radmin VPN, ZeroTier,
  Tailscale).
- **Join:** arkadaşının adresini (ve şifreyi) yaz, kaydını seç ve KATIL'a bas. Kaydın yedeklenir, arkadaşının sunucusuna
  gönderilir ve oyun açılır. Oynarken ilerlemen birkaç saniyede bir kendi kaydına yazılır; ayrılınca ya da oyunu
  kapatınca son hâli bilgisayarına kaydedilir.
- **Kaydın senin:** sunucu misafirlerin kaydını yalnız bellekte tutar; sunucunun Kayıtlar sayfasında görünmez.
- **Ortak olanlar:** firma, savaş ve Blacklight haritaları (1-1 … 5-4, BL): uzaylılar, kutular ve cevherler, birbirinizi
  görürsünüz. Sohbet ortak. Kapı, mod ve etkinlik haritaları herkesin kendi kopyası; posta, klan ve müzayede kişisel.
  Sunucunun oyun ayarları herkese uygulanır (GM konsolu yalnız sunucuyu kuranda). PvP yok.
- İki tarafta da panel ve oyun sürümü aynı olmalı.

### Gereksinimler

- Windows 10 ya da 11.
- [Python](https://www.python.org/downloads/windows/) 3.10 ya da daha yenisi. Oynamak için başka bir şey gerekmez.
- **Orijinal DarkOrbit Unity istemcisi**, sürüm **1.1.115** (depoda yok). Panel onu bilgisayarında bulamazsa kurulum
  sihirbazı oyunun resmî indirme sunucusundan indirip proje klasörüne kurar: yaklaşık 3,5 GB indirme ve 4,4 GB boş disk
  alanı. Durdurulan indirme kaldığı yerden sürer. Kendin kurarsan klasörde `DarkOrbit.exe` ve `DarkOrbit_Data` olmalı.
- Panel penceresi için Microsoft Edge ya da Google Chrome (yoksa varsayılan tarayıcın açar).
- İsteğe bağlı: `pip install capstone`; yalnız sunucuyu daha yeni bir istemci sürümüne uyarlamak istersen (İstemci sayfası).

### Hızlı başlangıç

1. Bu depoyu indir (Code > Download ZIP) ve aç ya da klonla.
2. **`OpenOrbit Panel.pyw`** dosyasına çift tıkla. Panel kendi penceresinde açılır; konsol penceresi çıkmaz.
3. Kurulum sihirbazını izle: dili seç, DarkOrbit oyun klasörünü seç (bilinen yerlerde kendiliğinden bulunur; oyun
   bilgisayarında yoksa sihirbaz indirir), ilk pilotunu oluştur ve bir hazır ayar seç.
4. **OYNA**'ya bas. Sunucular başlar, oyun açılır. İstemcinin giriş ekranında START'a bas.

Sihirbazı istediğin zaman **Panel** sayfasından yeniden açabilirsin; dili değiştirmek ve masaüstüne kısayol koymak da
orada.

### Güncellemeler

Panel açıldıktan kısa süre sonra ve sonra altı saatte bir bu depoda yeni sürüm olup olmadığına bakar. Varsayılan olarak
oyun ve sunucular kapanınca güncellemeyi kendisi kurar ve yeniden başlar; açık panel penceresi kendini yeniler. **Panel**
sayfasından *Yalnız haber ver*'i seçebilir, kapatabilir ve elle denetleyebilirsin.

- **ZIP olarak indirdiysen** (Git gerekmez): yeni sürümün arşivi (yaklaşık 2 MB) indirilir, değişen dosyalar yenilenir,
  projeden kaldırılan dosyalar çıkarılır. Eski hâlleri `server/save/guncelleme/`'de saklanır (son iki güncelleme).
- **Git ile klonladıysan:** panel `git` ile ileri sarar. İzlenen dosyaları değiştirdiysen ya da kendi commit'lerin varsa hiçbir
  şeye dokunmaz, yalnız haber verir.
- Kayıtların, ayarların, günlüklerin, kişisel giriş şablonların, inen oyun görselleri ve oyun istemcisi hiç değişmez.
- **Eski addan (DarkOrbit Server Emulator) geliyorsan:** 24 Ekim 2026'dan önceki sürümler artık kendiliğinden
  güncellenemez (panel *Arşiv bu projenin değil.* der). ZIP'i bir kez daha indirip içindekileri klasörünün üstüne kopyala;
  kayıtların, ayarların ve oyun yerinde kalır. Sonra paneli `OpenOrbit Panel.pyw` ile aç; **Panel** sayfasında
  *Kısayol oluştur*'a basınca eski masaüstü kısayolu yenisiyle değişir.

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
| `DarkOrbit_Version1.1.115/` | Oyun istemcisi, panel indirdiyse (inerken `istemci_indiriliyor/`) |
| `server/save/guncelleme/` | Güncellemelerin değiştirdiği dosyaların eski hâlleri (son iki güncelleme) |
| `server/cdn/do_img/` | Resmî CDN'den inen oyun görselleri (haber, etkinlik ve pencere görselleri) |

Hepsi ilk açılışta oluşur ve bilgisayarında kalır.

### Bilmekte yarar var

- İstemci klasöründeki `DarkorbitLauncher.exe`'yi çalıştırma: istemciyi resmî sunuculardan güncelleyip uyumu bozabilir.
  Oyunu panelden başlat.
- Sunucu 1.1.115 istemcisi için yazıldı. Başka bir sürümde panel uyarır ve protokolü yeni istemcinin kodundan uyarlayabilir
  (İstemci sayfası; `capstone` gerekir).
- Bot oyuncular henüz yok: başka oyuncu gerektiren görevler ilerlemez.

### Topluluk

Duyurular, yardım, hata bildirimi ve öneriler için [Discord sunucusuna](https://discord.gg/BUb9rNTKNt) katıl. Türkçe ve
İngilizce kanalların yanında ekran görüntüleri ve birlikte oynayacak arkadaş bulmak için kanallar var. Panelin **Panel**
sayfasından da katılabilirsin.

### Yasal not

Kişisel, çevrimdışı kullanım için bir hayran projesidir; Bigpoint GmbH ile bağlantısı yoktur, onun onayını taşımaz.
DarkOrbit, istemci, grafikler, sesler ve metinler Bigpoint GmbH'ye aittir; oyun verilerinin bir kısmı darkorbitwiki.com'dan
derlenmiştir. Resmî sunuculara bağlanmak ya da onlara zarar vermek için kullanma.

Depoda ne oyun istemcisi ne de oyunun görselleri var: istemciyi Bigpoint'in resmî indirme sunucusundan sen indirirsin (ya
da panel senin için indirir); sunucu her görseli oyun onu ilk gösterdiğinde resmî CDN'den alır ve bilgisayarında saklar.
Yazılım olduğu gibi, hiçbir garanti olmadan sunulur.

Projenin kendi kodu [MIT Lisansı](LICENSE) ile yayımlanır. Bigpoint'in istemcisini, grafiklerini, seslerini, metinlerini
ve oyun verilerini kapsamaz.
