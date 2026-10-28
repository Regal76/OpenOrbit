/* OpenOrbit paneli — Dünya Editörü (dunyalar.py, /api/dunya…; belgeler/DUNYA_EDITORU.md). panel.js'in yardımcılarını kullanır.
   Dünya: standart oyun verisinin üstüne konan değişiklik katmanı. Standart dünya salt okunur: değişiklikler taslakta durur,
   "Yeni dünya olarak kaydet" onları bir dünyaya çevirir. Kaydın varsayılan dünyası OYNA'da açılır.
   Görünümler: kitaplık (dünya kartları, pilotların dünyaları) ve editör (dünya çubuğu, bölüm menüsü, bölüm). Değişiklikler kendiliğinden
   kaydedilir (yama: dosya + JSON Pointer -> tam değer). */
'use strict';

Object.assign(IC, {
  map: '<polygon points="1 6 1 22 8 18 16 22 23 18 23 2 16 6 8 2 1 6"/><line x1="8" y1="2" x2="8" y2="18"/><line x1="16" y1="6" x2="16" y2="22"/>',
  alien: '<path d="M12 3c-4.4 0-8 3.1-8 7.4 0 4.6 4.2 10.6 8 10.6s8-6 8-10.6C20 6.1 16.4 3 12 3z"/><path d="M7.5 11.5c1.6-.2 3 .7 3.3 2.2-1.6.3-3-.5-3.3-2.2z"/><path d="M16.5 11.5c-1.6-.2-3 .7-3.3 2.2 1.6.3 3-.5 3.3-2.2z"/>',
  target: '<circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="6"/><circle cx="12" cy="12" r="2"/>',
  box: '<path d="M21 16V8a2 2 0 0 0-1-1.7l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.7l7 4a2 2 0 0 0 2 0l7-4a2 2 0 0 0 1-1.7z"/><polyline points="3.3 7 12 12 20.7 7"/><line x1="12" y1="22" x2="12" y2="12"/>',
  ring: '<circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="4.5" stroke-dasharray="3 2"/>',
  lock: '<rect x="4" y="11" width="16" height="11" rx="2"/><path d="M8 11V7a4 4 0 0 1 8 0v4"/>',
  layers: '<polygon points="12 2 2 7 12 12 22 7 12 2"/><polyline points="2 17 12 22 22 17"/><polyline points="2 12 12 17 22 12"/>',
  move: '<polyline points="5 9 2 12 5 15"/><polyline points="9 5 12 2 15 5"/><polyline points="15 19 12 22 9 19"/><polyline points="19 9 22 12 19 15"/><line x1="2" y1="12" x2="22" y2="12"/><line x1="12" y1="2" x2="12" y2="22"/>',
  crosshair: '<circle cx="12" cy="12" r="9"/><line x1="12" y1="1" x2="12" y2="6"/><line x1="12" y1="18" x2="12" y2="23"/><line x1="1" y1="12" x2="6" y2="12"/><line x1="18" y1="12" x2="23" y2="12"/>',
  minus: '<line x1="5" y1="12" x2="19" y2="12"/>',
  nest: '<polygon points="12 2 20.7 7 20.7 17 12 22 3.3 17 3.3 7 12 2"/><circle cx="12" cy="12" r="3"/>',
  maximize: '<polyline points="15 3 21 3 21 9"/><polyline points="9 21 3 21 3 15"/><line x1="21" y1="3" x2="14" y2="10"/><line x1="3" y1="21" x2="10" y2="14"/>',
  gift: '<polyline points="20 12 20 22 4 22 4 12"/><rect x="2" y="7" width="20" height="5"/><line x1="12" y1="22" x2="12" y2="7"/><path d="M12 7H7.5a2.5 2.5 0 0 1 0-5C11 2 12 7 12 7z"/><path d="M12 7h4.5a2.5 2.5 0 0 0 0-5C13 2 12 7 12 7z"/>',
});

const DE = { liste: null, did: null, bolum: 'genel', ozet: null, zam: {}, durum: 'hazir', esyalar: null, uzayli: null, sec: {} };
// bölüm: kimlik, ad, simge, açıklama, hazır mı (yakında olanlar menüde sönük)
const DE_BOLUMLER = [
  ['genel', N('Genel Bakış'), 'globe', N('Dünyanın kartı, değişiklik özeti ve bu dünyada oynayan pilotlar.'), true],
  ['haritalar', N('Haritalar'), 'map', N('Uzaylıların doğma listesi ve bölgeleri, bonus kutuları, portallar, güvenli bölgeler ve inler.'), true],
  ['uzaylilar', N('Uzaylılar'), 'alien', N('Can, kalkan, hasar, hız, saldırganlık ve ödüller; var olan bir uzaylıdan yenisini türet.'), true],
  ['gorevler', N('Görevler'), 'target', N('Hedefler, ödüller, seviye ve önkoşullar; birkaç tıkla yeni görev.'), true],
  ['magaza', N('Mağaza'), 'cart', N('Ürünlerin fiyatı ve para birimi; ürünü satıştan kaldır.'), true],
  ['muzayede', N('Açık Artırma'), 'gavel', N('Saatlik, günlük ve haftalık lotlar: eşya, adet, anında alım fiyatı.'), true],
  ['kutular', N('Kutular ve Ganimet'), 'gift', N('Bonus kutularının ve booty kutularının içeriği.'), true],
  ['kapilar', N('Galaksi Kapıları'), 'ring', N('Dalgalar, uzaylılar ve kapı ödülleri.'), true],
  ['etkinlikler', N('Etkinlikler'), 'calendar', N('Bu dünyada hangi etkinlik ne zaman açık; harita etkinliklerinin uzaylıları.'), true],
  ['ekonomi', N('Ödüller ve Ekonomi'), 'star', N('Seviye eşikleri, rütbe puanı formülü ve rütbe eşikleri.'), true],
];
const deIkon = (id, cls = 'de-ikon') => art('ed_' + id, cls);         // bölüm ikonu (gorsel/ed_<bölüm>.webp, OP-009)
const DE_KAPAK_GORSEL = new Set(['standart', 'nebula', 'crimson', 'ice', 'mining', 'crystal', 'toxic', 'void']);   // gorsel/dunya_<kapak>.webp (OP-010)
// replaceChildren null/false'u metin olarak eklerdi ("null"): koşullu çocuklar süzülür
const doldur = (el, ...k) => el.replaceChildren(...k.flat(Infinity).filter(x => x != null && x !== false));
const jp = (...p) => p.map(x => '/' + String(x).replace(/~/g, '~0').replace(/\//g, '~1')).join('');   // JSON Pointer (veri.py)
const deStandart = () => DE.did === 'standart';

function deKapak(kapak, cls = '') {
  const el = h('div', { class: 'de-kapak k-' + (kapak || 'nebula') + ' ' + cls });
  if (DE_KAPAK_GORSEL.has(kapak)) el.style.backgroundImage = 'url(gorsel/dunya_' + kapak + '.webp)';
  else el.append(h('i', { class: 'gz' }), h('i', { class: 'hl' }));      // gezegen ve halka (kodla)
  return el;
}

// ------------------------------------------------------------------ giriş noktası
async function renderDunya() {
  await ogYukle();
  const r = await act(() => api('/api/dunyalar')); if (!r || S.page !== 'dunya') return;
  DE.liste = r;
  if (DE.did && !r.liste.some(w => w.id === DE.did)) DE.did = null;
  if (!DE.did) return deKitaplik();
  deEditor();
}
function deAc(did, bolum) { DE.did = did; DE.bolum = bolum || 'genel'; DE.uzayli = null; DE.sec = {}; renderDunya(); }

// ================================================================== KİTAPLIK
function deKitaplik() {
  const r = DE.liste, ozel = r.liste.filter(w => !w.standart);
  const kart = w => {
    const pilotlar = w.kullananlar || [];
    return h('div', { class: 'de-kart' + (w.standart ? ' std' : ''), onclick: e => { if (!e.target.closest('button')) deAc(w.id); } },
      deKapak(w.kapak, 'buyuk'),
      h('div', { class: 'de-kart-govde' },
        h('div', { class: 'row between', style: { gap: '8px' } }, h('div', { class: 'de-kart-ad' }, w.standart ? icon('lock') : null, w.ad),
          w.standart ? badge(T('Salt okunur'), 'info') : badge(w.degisiklik ? T('{0} değişiklik', w.degisiklik) : T('Değişiklik yok'), w.degisiklik ? 'orange' : '')),
        h('div', { class: 'de-kart-acik muted small' }, w.aciklama || T('Açıklama yok.')),
        h('div', { class: 'de-kart-pilot' }, pilotlar.length ? [icon('users'), h('span', null, pilotlar.slice(0, 3).map(p => p.pilot || p.ad).join(', ')
          + (pilotlar.length > 3 ? ' +' + (pilotlar.length - 3) : ''))] : h('span', { class: 'dim' }, T('Varsayılan dünyası bu olan pilot yok'))),
        h('div', { class: 'row', style: { gap: '6px', marginTop: 'auto' } },
          btn(w.standart ? T('İncele') : T('Düzenle'), () => deAc(w.id), 'sm primary', w.standart ? 'search' : 'edit'),
          btn(T('Pilota ata'), ev => deAtaMenu(ev.currentTarget, w), 'sm', 'users'),
          h('span', { class: 'spacer' }),
          btn('', ev => deDunyaMenu(ev.currentTarget, w), 'sm ghost icon', 'more', { title: T('Diğer') }))));
  };
  const yeni = h('button', { class: 'de-kart yeni', type: 'button', onclick: () => deYeniDunya() },
    h('div', { class: 'de-yeni-ic' }, icon('plus')), h('b', null, T('Yeni dünya')), h('span', { class: 'muted small' }, T('Standart dünyadan başla ya da bir dünyayı kopyala.')));
  const pilotSatir = k => {
    const sel = h('select', { class: 'input', onchange: e => act(() => api('/api/kayitlar/dunya', { id: k.id, dunya: e.target.value }),
      T('{0}: varsayılan dünya değişti.', k.pilot || k.ad)).then(x => { if (x) { DE.liste = x; deKitaplik(); poll(); } }) },
      r.liste.map(w => h('option', { value: w.id, selected: w.id === k.dunya }, w.ad)));
    return h('tr', null, h('td', null, h('b', null, k.pilot || '?'), ' ', badge(k.firma || '?', firmaCls(k.firma)), k.aktif ? ' ' : null,
      k.aktif ? badge(T('Etkin kayıt'), 'ok') : null), h('td', { class: 'muted' }, k.ad), h('td', null, lvl(k.seviye)), h('td', null, sel));
  };
  doldur($('#content'), h('div', { class: 'stack' },
    h('div', { class: 'de-giris card' },
      h('div', null, h('h2', null, icon('globe'), T('Dünyalar')),
        h('p', { class: 'desc', style: { maxWidth: '640px', marginBottom: '0' } }, T('Bir dünya, oyunun haritalarını, uzaylılarını, görevlerini, mağazasını ve açık artırmasını kendine göre değiştirdiğin bir evrendir. Her pilot kendi varsayılan dünyasına girer; OYNA o dünyayı açar. Standart dünya korunur: değişikliklerini saklamak için yeni bir dünya oluşturursun.'))),
      h('div', { class: 'row wrap', style: { gap: '8px' } }, btn(T('Yeni dünya'), () => deYeniDunya(), 'primary', 'plus'),
        btn(T('İçe aktar'), () => deIceri(), '', 'upload')),
      art('dron_editor', 'de-giris-art')),
    h('div', { class: 'de-izgara' }, r.liste.map(kart), yeni),
    !ozel.length ? h('div', { class: 'card de-bos' }, art('bos_dunya', 'de-bos-art'), h('div', null, T('Henüz kendi dünyan yok. Standart dünyayı açıp dilediğini değiştir, sonra "Yeni dünya olarak kaydet" de; ya da "Yeni dünya" ile boş bir kopyadan başla.'))) : null,
    r.kayitlar.length ? h('div', { class: 'card' }, h('h2', null, icon('users'), T('Pilotların dünyaları')),
      h('p', { class: 'desc' }, T('Her kayıt OYNA\'ya basınca kendi varsayılan dünyasına girer. Arkadaşlarınla oynarken host\'un dünyası herkese uygulanır.')),
      h('table', { class: 'table' }, h('thead', null, h('tr', null, [T('Pilot'), T('Kayıt'), T('Seviye'), T('Varsayılan dünya')].map(x => h('th', null, x)))),
        h('tbody', null, r.kayitlar.map(pilotSatir)))) : null));
}

function deAtaMenu(anchor, w) {
  const ks = DE.liste.kayitlar;
  if (!ks.length) return toast(T('Önce bir kayıt oluştur.'), 'info');
  popMenu(anchor, ks.map(k => ({ label: (k.pilot || k.ad) + (k.dunya === w.id ? '  ✓' : ''), ic: k.dunya === w.id ? 'check' : 'users',
    fn: () => act(() => api('/api/kayitlar/dunya', { id: k.id, dunya: w.id }), T('{0} artık "{1}" dünyasına girer.', k.pilot || k.ad, w.ad))
      .then(x => { if (x) { DE.liste = x; poll(); S.page === 'dunya' && (DE.did ? deEditor() : deKitaplik()); } }) })));
}

function deDunyaMenu(anchor, w) {
  const items = [
    { label: w.standart ? T('İncele') : T('Düzenle'), ic: 'edit', fn: () => deAc(w.id) },
    { label: T('Kopyala'), ic: 'copy', fn: async () => {
      const ad = await promptBox(T('Dünyayı kopyala'), T('Yeni dünyanın adı'), w.standart ? T('Yeni dünya') : T('{0} (kopya)', w.ad)); if (ad == null) return;
      const x = await act(() => api('/api/dunya/kopyala', { id: w.id, ad }), T('Kopyalandı.')); if (x) { DE.liste = x; deKitaplik(); } } },
    { label: T('Paylaş / dışa aktar'), ic: 'download', fn: () => deDisari(w) },
  ];
  if (!w.standart) items.push({ label: T('Yeniden adlandır'), ic: 'edit', fn: () => deAdDegistir(w) }, '-',
    { label: T('Sil'), ic: 'trash', danger: true, fn: async () => {
      if (!await confirmBox(T('"{0}" silinsin mi?', w.ad), T('Dünya silinir; varsayılan dünyası bu olan pilotlar standart dünyaya döner. Silinen dünya save/dunyalar/_silinenler klasöründe saklanır.'), { ok: T('Sil'), danger: true })) return;
      const x = await act(() => api('/api/dunya/sil', { id: w.id }), T('Dünya silindi.')); if (x) { DE.liste = x; if (DE.did === w.id) DE.did = null; renderDunya(); } } });
  popMenu(anchor, items);
}

async function deAdDegistir(w) {
  const ad = await promptBox(T('Yeniden adlandır'), T('Dünyanın adı'), w.ad); if (ad == null) return;
  const x = await act(() => api('/api/dunya/guncelle', { id: w.id, ad }), T('Kaydedildi.')); if (x) { DE.liste = x; renderDunya(); }
}

// yeni dünya: ad, açıklama, kapak, başlangıç (standart ya da bir dünya); taslaktan=true ise standart dünyanın taslağı
function deYeniDunya({ taslaktan = false } = {}) {
  const w = { ad: '', aciklama: '', kapak: 'nebula', kaynak: 'standart', kayit: null };
  const aktif = DE.liste.kayitlar.find(k => k.aktif);
  const ad = h('input', { class: 'input', placeholder: T('Örn. Zor Uzay, Avcı Cenneti'), maxlength: 40, oninput: e => { w.ad = e.target.value; } });
  const acik = h('textarea', { class: 'input', rows: 2, maxlength: 240, placeholder: T('Bu dünyada ne farklı? (isteğe bağlı)'), oninput: e => { w.aciklama = e.target.value; } });
  const kapaklar = h('div', { class: 'de-kapaklar' });
  const cizKapak = () => doldur(kapaklar, ...DE.liste.kapaklar.filter(k => k !== 'standart').map(k =>
    h('button', { type: 'button', class: 'de-kapak-sec' + (w.kapak === k ? ' on' : ''), onclick: () => { w.kapak = k; cizKapak(); } }, deKapak(k))));
  cizKapak();
  const kaynak = taslaktan ? null : h('select', { class: 'input', onchange: e => { w.kaynak = e.target.value; } },
    DE.liste.liste.map(x => h('option', { value: x.id }, x.standart ? T('Standart dünya (boş başla)') : T('Kopyala: {0}', x.ad))));
  const ata = aktif ? h('label', { class: 'row', style: { gap: '8px', cursor: 'pointer' } }, h('label', { class: 'switch' },
    h('input', { type: 'checkbox', checked: true, onchange: e => { w.kayit = e.target.checked ? aktif.id : null; } }), h('span')),
    h('span', null, T('{0} bu dünyaya girsin (varsayılan dünyası olsun)', aktif.pilot || aktif.ad))) : null;
  if (aktif) w.kayit = aktif.id;
  const m = modal({ title: taslaktan ? T('Yeni dünya olarak kaydet') : T('Yeni dünya'), wide: true,
    sub: taslaktan ? T('Standart dünyada yaptığın {0} değişiklik bu dünyaya taşınır; standart dünya olduğu gibi kalır.', DE.ozet?.degisiklik || 0) : null,
    body: h('div', { class: 'stack', style: { gap: '14px' } }, taslaktan ? art('dron_kayit', 'de-kayit-art') : null, field(T('Ad'), ad), field(T('Açıklama'), acik),
      field(T('Kapak'), kapaklar), kaynak ? field(T('Başlangıç'), kaynak) : null, ata),
    foot: [btn(T('Vazgeç'), () => m.close(), 'ghost'), btn(T('Oluştur'), async () => {
      const x = await act(() => api('/api/dunya/olustur', Object.assign({}, w, { taslaktan })), T('Dünya oluşturuldu: {0}', w.ad.trim()));
      if (!x) return;
      m.close(); DE.liste = x; poll(); deAc(x.yeni, taslaktan ? DE.bolum : 'genel');
    }, 'primary', 'check')] });
}

// ================================================================== EDİTÖR
async function deEditor() {
  const oz = await act(() => api('/api/dunya?dunya=' + encodeURIComponent(DE.did))); if (!oz || S.page !== 'dunya') return;
  DE.ozet = oz;
  const kok = h('div', { class: 'stack', id: 'de-kok' });
  doldur($('#content'), kok);
  kok.append(deCubuk(), h('div', { id: 'de-uyari' }), h('div', { class: 'de-duzen' }, deMenu(), h('div', { class: 'de-alan', id: 'de-alan' })));
  deUyari();
  deBolumCiz();
}

function deCubuk() {
  const w = DE.ozet;
  return h('div', { class: 'card de-cubuk' },
    btn('', () => { DE.did = null; renderDunya(); }, 'ghost icon', 'arrowL', { title: T('Dünyalar') }),
    deKapak(w.kapak, 'kucuk'),
    h('div', { class: 'de-cubuk-ad' }, h('div', { class: 'row', style: { gap: '8px' } }, h('b', null, w.ad),
      w.standart ? badge([icon('lock'), T('Standart · salt okunur')], 'info') : badge(T('Özel dünya'), 'orange')),
      h('div', { class: 'muted small ellipsis' }, w.aciklama || (w.standart ? '' : T('Açıklama yok.')))),
    h('span', { class: 'spacer' }),
    h('span', { class: 'de-kayit', id: 'de-kayit' }),
    btn(T('Dünya değiştir'), ev => popMenu(ev.currentTarget, DE.liste.liste.map(x => ({ label: x.ad + (x.id === DE.did ? '  ✓' : ''),
      ic: x.standart ? 'lock' : 'globe', fn: () => deAc(x.id, DE.bolum) }))), 'sm', 'refresh'),
    btn('', ev => deDunyaMenu(ev.currentTarget, DE.liste.liste.find(x => x.id === DE.did) || w), 'sm ghost icon', 'more', { title: T('Diğer') }));
}

function deKayitDurumu(d) {
  DE.durum = d;
  const el = $('#de-kayit'); if (!el) return;
  el.className = 'de-kayit ' + d;
  doldur(el, ...(d === 'kaydediliyor' ? [h('span', { class: 'spin' }), T('Kaydediliyor…')] : d === 'kaydedildi'
    ? [icon('check'), deStandart() ? T('Taslağa yazıldı') : T('Kaydedildi')] : []));
}

function deUyari() {
  const el = $('#de-uyari'); if (!el) return;
  const w = DE.ozet, out = [];
  if (w.standart) out.push(h('div', { class: 'de-taslak' + (w.degisiklik ? ' dolu' : '') }, art('dron_kilit', 'de-taslak-art'),
    h('div', null, h('b', null, w.degisiklik ? T('{0} değişiklik kaydedilmedi', w.degisiklik) : T('Standart dünya düzenlenemez')),
      h('div', { class: 'small' }, w.degisiklik ? T('Standart dünya korunur. Bu değişiklikleri saklamak için onları yeni bir dünyaya kaydet.')
        : T('Dilediğini değiştirebilirsin: değişiklikler bir taslakta tutulur, oyuna geçmesi için yeni bir dünya olarak kaydedersin.'))),
    w.degisiklik ? btn(T('Taslağı at'), async () => {
      if (await confirmBox(T('Taslak atılsın mı?'), T('Standart dünyada yaptığın {0} değişiklik silinir.', w.degisiklik), { ok: T('At'), danger: true }))
        act(() => api('/api/dunya/taslak_at', {}), T('Taslak atıldı.')).then(x => x && deEditor());
    }, 'sm ghost', 'trash') : null,
    btn(T('Yeni dünya olarak kaydet'), () => deYeniDunya({ taslaktan: true }), 'sm orange', 'save', { disabled: !w.degisiklik })));
  if (w.sunucu_bu_dunyada && !w.yeniden_gerekli) out.push(h('div', { class: 'alert bilgi' }, icon('zap'),
    h('div', null, T('Sunucu bu dünyayla açık: mağaza ve açık artırma değişiklikleri oyunda hemen geçerli. Öteki bölümlerdeki değişiklikler için sunucu yeniden başlamalı.'))));
  if (w.sunucu_bu_dunyada && w.yeniden_gerekli) out.push(h('div', { class: 'alert uyari' }, icon('alert'),
    h('div', null, T('Bazı değişiklikler sunucu yeniden başlayınca geçerli olur (oyun kapalıyken OYNA kendiliğinden yeniden başlatır). Mağaza ve açık artırma değişiklikleri zaten oyunda.')),
    btn(T('Sunucuyu yeniden başlat'), async () => {
      if (await confirmBox(T('Sunucu yeniden başlatılsın mı?'), T('Oyundaysan bağlantın kopar; istemci yeniden bağlanır. Kaydın korunur.'), { ok: T('Yeniden başlat') }))
        act(() => api('/api/dunya/sunucu_yeniden', {}), T('Sunucu yeniden başlatıldı.')).then(x => x && deEditor());
    }, 'sm', 'refresh')));
  doldur(el, ...out);
  el.style.display = out.length ? '' : 'none';
}

function deMenu() {
  return h('nav', { class: 'de-menu', id: 'de-menu' }, DE_BOLUMLER.map(([id, ad, ic, , hazir]) => {
    const n = DE.ozet.bolumler[id] || 0;
    return h('button', { type: 'button', class: (DE.bolum === id ? 'on ' : '') + (hazir ? '' : 'yakinda'), 'data-b': id, disabled: !hazir,
      title: hazir ? null : T('Yakında'), onclick: () => { DE.bolum = id; DE.sec = {}; deMenuSay(); deBolumCiz(); } },
      deIkon(id), h('span', null, T(ad)), hazir ? (n ? h('span', { class: 'de-say' }, n) : null) : h('span', { class: 'de-yakinda' }, T('Yakında')));
  }));
}
function deMenuSay() {
  document.querySelectorAll('#de-menu button').forEach(b => {
    b.classList.toggle('on', b.dataset.b === DE.bolum);
    const n = DE.ozet.bolumler[b.dataset.b] || 0, s = b.querySelector('.de-say');
    if (b.disabled) return;
    if (n && s) s.textContent = n; else if (n) b.append(h('span', { class: 'de-say' }, n)); else if (s) s.remove();
  });
}

function deBolumCiz() {
  const b = DE_BOLUMLER.find(x => x[0] === DE.bolum) || DE_BOLUMLER[0];
  const alan = $('#de-alan'); if (!alan) return;
  alan.parentNode.classList.toggle('dar', b[0] === 'haritalar');          // harita tuvaline yer: menü simge şeridi
  doldur(alan, h('div', { class: 'empty' }, h('div', { class: 'spin', style: { margin: '30px auto' } })));
  ({ genel: deGenel, haritalar: deHaritalar, uzaylilar: deUzaylilar, gorevler: deGorevler, magaza: deMagaza, muzayede: deMuzayede, kutular: deKutular, kapilar: deKapilar, etkinlikler: deEtkinlikler, ekonomi: deEkonomi }[b[0]])(alan, b);
}
const deBaslik = (b, ...ekler) => h('div', { class: 'row between wrap de-bolum-bas' }, h('div', null, h('h2', null, deIkon(b[0], 'de-ikon buyuk'), T(b[1])),
  h('div', { class: 'muted small' }, T(b[3]))), h('div', { class: 'row wrap', style: { gap: '8px' } }, ...ekler));

// değişiklik: yama (dosya + yol -> tam değer); standartta taslağa. Gecikmeli (aynı anahtar için son değer gider).
function deYama(dosya, yol, deger, { ms = 450, sonra } = {}) {
  const k = dosya + yol;
  clearTimeout(DE.zam[k]); deKayitDurumu('kaydediliyor');
  return new Promise(res => {
    DE.zam[k] = setTimeout(async () => {
      delete DE.zam[k];
      const r = await act(() => api('/api/dunya/yama', { dunya: DE.did, dosya, yol, deger }));
      if (r) { DE.ozet = Object.assign(DE.ozet, r); deMenuSay(); deUyari(); deKayitDurumu('kaydedildi'); if (sonra) sonra(r); }
      else deKayitDurumu('hazir');
      res(r);
    }, ms);
  });
}
async function deGeriAl(dosya, yol, bolum) {
  const r = await act(() => api('/api/dunya/geri_al', { dunya: DE.did, dosya, yol, bolum }), T('Standarda döndürüldü.'));
  if (r) { DE.ozet = Object.assign(DE.ozet, r); deMenuSay(); deUyari(); }
  return r;
}

// sayı alanı: −/+ düğmeleri, elle yazım; değişince cb(değer)
function deSayi(v, cb, { min = 0, max = 1e9, adim = 1, gen = 92 } = {}) {
  const inp = h('input', { class: 'input num', type: 'number', min, max, step: adim, value: v, style: { width: gen + 'px' } });
  const set = x => { x = Math.max(min, Math.min(max, Math.round(+x || 0))); inp.value = x; cb(x); };
  inp.addEventListener('change', () => set(inp.value));
  return h('div', { class: 'de-sayi' }, h('button', { type: 'button', onclick: () => set(+inp.value - adim), tabindex: -1 }, icon('minus')), inp,
    h('button', { type: 'button', onclick: () => set(+inp.value + adim), tabindex: -1 }, icon('plus')));
}
// "standart: X" ipucu ve tek tıkla geri alma
const deStd = (std, simdi, geri, fmt = fmtN) => std == null || JSON.stringify(std) === JSON.stringify(simdi) ? null
  : h('button', { type: 'button', class: 'de-std', title: T('Standart değere döndür'), onclick: geri }, icon('undo'), T('Standart: {0}', fmt(std)));

// ================================================================== ORTAK SEÇİCİLER
const ESYA_KATEGORI = [['hepsi', N('Hepsi')], ['ammunition', N('Cephane')], ['equipment', N('Ekipman')], ['ship', N('Gemiler')],
  ['drone', N('Dronlar')], ['resource', N('Kaynaklar')], ['booster', N('Boosterlar')], ['currency', N('Para')], ['diger', N('Diğer')]];
const esyaKat = l => { const p = l.split('_')[0]; return ESYA_KATEGORI.some(k => k[0] === p) ? p : 'diger'; };

async function esyaSec(baslik = T('Eşya seç')) {
  if (!DE.esyalar) { const r = await act(() => api('/api/dunya/esyalar')); if (!r) return null; DE.esyalar = r.esyalar; }
  return new Promise(res => {
    let kat = 'hepsi', q = '', sinir = 120, done = false;
    const izgara = h('div', { class: 'de-secici-izgara' });
    const ciz = () => {
      const s = q.trim().toLowerCase();
      const list = DE.esyalar.filter(l => (kat === 'hepsi' || esyaKat(l) === kat) && (!s || l.includes(s) || esyaAdi(l).toLowerCase().includes(s)));
      doldur(izgara, ...list.slice(0, sinir).map(l => h('button', { type: 'button', class: 'de-secici-oge', title: l,
        onclick: () => { done = true; m.close(); res(l); } }, oyunIkon(l, 44, null, 'box'), h('span', null, esyaAdi(l)))),
        list.length > sinir ? h('button', { type: 'button', class: 'btn sm de-daha', onclick: () => { sinir += 240; ciz(); } }, T('{0} eşya daha', fmtN(list.length - sinir))) : null,
        !list.length ? h('div', { class: 'empty small muted' }, T('Eşleşen eşya yok.')) : null);
    };
    const seg = h('div', { class: 'seg' }, ESYA_KATEGORI.map(([k, ad]) => h('button', { class: k === kat ? 'on info' : '', onclick: e => {
      kat = k; seg.querySelectorAll('button').forEach(b => b.classList.remove('on', 'info')); e.currentTarget.classList.add('on', 'info'); ciz(); } }, T(ad))));
    const ara = h('input', { class: 'input', placeholder: T('Ad ya da kimlikle ara…'), oninput: e => { q = e.target.value; sinir = 120; ciz(); } });
    const m = modal({ title: baslik, wide: true, onclose: () => { if (!done) res(null); }, body: h('div', { class: 'stack', style: { gap: '10px' } },
      ara, seg, !OG.dizin ? h('div', { class: 'small muted' }, T('Oyunun görselleri, oyun bir kez BepInEx ile açılınca hazırlanır.')) : null, izgara) });
    ciz();
  });
}

async function uzayliListesi() {
  if (!DE.uzayli) { const r = await act(() => api('/api/dunya/bolum?bolum=uzaylilar&dunya=' + encodeURIComponent(DE.did))); if (!r) return null; DE.uzayli = r.uzaylilar; }
  return DE.uzayli;
}
const npcIkon = (u, boy) => u && u.ikon && OG.dizin?.sprite[u.ikon] ? sprite(u.ikon, boy) : h('span', { class: 'sprite bos de-npc-bos', style: { width: boy + 'px', height: boy + 'px' } }, icon('alien'));
const npcAdi = u => (u?.ad || '').replace(/^[-=\[\]:.{}\s]+|[-=\[\]:.{}\s]+$/g, '') || u?.tip || '?';

async function uzayliSec(baslik = T('Uzaylı seç'), { kimlikli = false, sayisal = false } = {}) {
  const liste = await uzayliListesi(); if (!liste) return null;
  return new Promise(res => {
    let q = '', filtre = 'harita', done = false;
    const izgara = h('div', { class: 'de-secici-izgara npc' });
    const ciz = () => {
      const s = q.trim().toLowerCase();
      const l = liste.filter(u => (!kimlikli || u.npc_kimlik != null) && (!sayisal || /^\d+$/.test(u.tip)) && (filtre === 'hepsi' || (filtre === 'harita' ? u.nerede.length || u.yeni : u.etkinlik))
        && (!s || npcAdi(u).toLowerCase().includes(s)));
      doldur(izgara, ...l.map(u => h('button', { type: 'button', class: 'de-secici-oge', onclick: () => { done = true; m.close(); res(u); } },
        npcIkon(u, 44), h('span', null, npcAdi(u)), h('small', { class: 'muted' }, T('Can {0}', fmtN(u.hp))))),
        !l.length ? h('div', { class: 'empty small muted' }, T('Eşleşen uzaylı yok.')) : null);
    };
    const seg = h('div', { class: 'seg' }, [['harita', N('Haritalarda doğanlar')], ['etkinlik', N('Etkinlik')], ['hepsi', N('Hepsi')]].map(([k, ad]) =>
      h('button', { class: k === filtre ? 'on info' : '', onclick: e => { filtre = k; seg.querySelectorAll('button').forEach(b => b.classList.remove('on', 'info')); e.currentTarget.classList.add('on', 'info'); ciz(); } }, T(ad))));
    const m = modal({ title: baslik, wide: true, onclose: () => { if (!done) res(null); }, body: h('div', { class: 'stack', style: { gap: '10px' } },
      h('input', { class: 'input', placeholder: T('Uzaylı ara…'), oninput: e => { q = e.target.value; ciz(); } }), seg, izgara) });
    ciz();
  });
}

let DE_HARITALAR = null;
async function haritaSec(baslik, secili = [], { coklu = true } = {}) {
  if (!DE_HARITALAR) { const r = await act(() => api('/api/dunya/bolum?bolum=haritalar&dunya=' + encodeURIComponent(DE.did))); if (!r) return null; DE_HARITALAR = r.haritalar; }
  return new Promise(res => {
    const sec = new Set(secili.map(String)); let done = false;
    const grup = h('div', { class: 'de-harita-cipleri' });
    const ciz = () => doldur(grup, ...DE_HARITALAR.map(x => h('button', { type: 'button', class: 'de-hcip f-' + x.firma + (sec.has(x.ad) ? ' on' : ''),
      onclick: () => { if (!coklu) { done = true; m.close(); return res([x.ad]); } sec.has(x.ad) ? sec.delete(x.ad) : sec.add(x.ad); ciz(); } }, x.ad)));
    const m = modal({ title: baslik, wide: true, onclose: () => { if (!done) res(null); }, body: h('div', { class: 'stack', style: { gap: '10px' } },
      coklu ? h('div', { class: 'small muted' }, T('Hiçbiri seçilmezse her haritada geçerli.')) : null, grup),
      foot: coklu ? [btn(T('Temizle'), () => { sec.clear(); ciz(); }, 'ghost'), btn(T('Tamam'), () => { done = true; m.close(); res([...sec]); }, 'primary')] : null });
    ciz();
  });
}

// ================================================================== GENEL BAKIŞ
function deGenel(alan, b) {
  const w = DE.ozet;
  const kapaklar = h('div', { class: 'de-kapaklar' });
  const cizKapak = () => doldur(kapaklar, ...DE.liste.kapaklar.filter(k => k !== 'standart').map(k =>
    h('button', { type: 'button', class: 'de-kapak-sec' + (w.kapak === k ? ' on' : ''), disabled: w.standart, onclick: () =>
      act(() => api('/api/dunya/guncelle', { id: w.id, kapak: k })).then(x => { if (x) { DE.liste = x; w.kapak = k; cizKapak(); $('#de-kok .de-cubuk .de-kapak').replaceWith(deKapak(k, 'kucuk')); } }) }, deKapak(k))));
  cizKapak();
  const metaKaydet = (alanAdi, v) => act(() => api('/api/dunya/guncelle', { id: w.id, [alanAdi]: v })).then(x => { if (x) { DE.liste = x; w[alanAdi] = v; deKayitDurumu('kaydedildi'); } });
  const kart = h('div', { class: 'card de-genel-kart' }, deKapak(w.kapak, 'buyuk'),
    h('div', { class: 'stack', style: { gap: '12px' } },
      w.standart ? h('div', null, h('h3', { class: 'de-h3' }, icon('lock'), w.ad), h('p', { class: 'muted' }, w.aciklama))
        : [field(T('Ad'), h('input', { class: 'input', value: w.ad, maxlength: 40, onchange: e => metaKaydet('ad', e.target.value).then(() => deEditor()) })),
          field(T('Açıklama'), h('textarea', { class: 'input', rows: 2, maxlength: 240, onchange: e => metaKaydet('aciklama', e.target.value) }, w.aciklama || '')),
          field(T('Kapak'), kapaklar)],
      h('div', { class: 'row wrap small muted', style: { gap: '14px' } }, w.olusturma ? h('span', null, T('Oluşturuldu {0}', fmtWhen(w.olusturma))) : null,
        w.guncelleme ? h('span', null, T('Son değişiklik {0}', fmtWhen(w.guncelleme))) : null)));
  const bolumler = h('div', { class: 'card' }, h('h2', null, icon('layers'), T('Değişiklikler')),
    h('p', { class: 'desc' }, w.degisiklik ? T('Bu dünyada standarttan farklı olanlar. Bir bölümü tek tıkla standarda döndürebilirsin.') : T('Bu dünya henüz standart dünyayla aynı. Soldaki bölümlerden düzenlemeye başla.')),
    h('div', { class: 'de-ozet-izgara' }, DE_BOLUMLER.filter(x => x[0] !== 'genel').map(x => {
      const n = w.bolumler[x[0]] || 0;
      return h('div', { class: 'de-ozet-kutu' + (n ? ' dolu' : '') + (x[4] ? '' : ' yakinda') },
        h('div', { class: 'row', style: { gap: '8px' } }, deIkon(x[0], 'de-ikon orta'), h('b', null, T(x[1]))),
        h('div', { class: 'de-ozet-say' }, x[4] ? (n ? T('{0} değişiklik', n) : T('Standart')) : T('Yakında')),
        h('div', { class: 'row', style: { gap: '6px' } }, x[4] ? btn(T('Aç'), () => { DE.bolum = x[0]; deMenuSay(); deBolumCiz(); }, 'sm', 'chevR') : null,
          n ? btn('', async () => {
            if (await confirmBox(T('{0} standarda dönsün mü?', T(x[1])), T('Bu bölümdeki {0} değişiklik silinir.', n), { ok: T('Standarda döndür'), danger: true }))
              deGeriAl(null, null, x[0]).then(r => r && deBolumCiz());
          }, 'sm ghost icon', 'undo', { title: T('Standarda döndür') }) : null));
    })));
  const kul = (DE.liste.liste.find(x => x.id === w.id) || {}).kullananlar || [];
  const pilotlar = h('div', { class: 'card' }, h('h2', null, icon('users'), T('Bu dünyada oynayanlar')),
    h('p', { class: 'desc' }, kul.length ? T('Bu pilotlar OYNA\'ya basınca bu dünyaya girer.') : T('Henüz bu dünyayı varsayılan yapan pilot yok.')),
    h('div', { class: 'chips' }, kul.map(p => h('span', { class: 'chip' }, icon('users'), p.pilot || p.ad))),
    h('div', { class: 'row', style: { marginTop: '12px' } }, btn(T('Pilota ata'), ev => deAtaMenu(ev.currentTarget, w), 'sm', 'users')));
  doldur(alan, h('div', { class: 'stack' }, kart, bolumler, pilotlar,
    h('div', { class: 'alert bilgi' }, icon('info'), h('div', null, T('İstemcinin sınırları: yeni harita ya da yeni eşya eklenemez (ikisi de oyunun kendi dosyalarında). Yeni uzaylılar var olan bir modelin yeni değerlerle kopyasıdır; adları oyunda görünür.')))));
}

// ================================================================== UZAYLILAR
const ORE_ADI = { 0: 'resource_ore_prometium', 1: 'resource_ore_endurium', 2: 'resource_ore_terbium', 3: 'resource_ore_xenomit', 4: 'resource_ore_prometid',
  5: 'resource_ore_duranium', 6: 'resource_ore_promerium', 7: 'resource_ore_seprom', 8: 'resource_ore_palladium', 28: 'resource_ore_osmium' };
const ODUL_ALAN = [['ep', N('Deneyim'), 'kaynak_deneyim'], ['onur', N('Onur'), 'kaynak_onur'], ['kredi', N('Kredi'), 'kaynak_kredi'], ['uridyum', N('Uridyum'), 'kaynak_uridyum']];

async function deUzaylilar(alan, b) {
  DE.uzayli = null;
  const liste = await uzayliListesi(); if (!liste || DE.bolum !== 'uzaylilar') return;
  const f = DE.sec.uz || (DE.sec.uz = { q: '', filtre: 'harita', secili: null });
  const izgara = h('div', { class: 'de-npc-liste' }), detay = h('div', { class: 'de-detay' });
  const maxHp = Math.max(...liste.map(u => u.hp)), olcek = v => Math.max(3, Math.log10(1 + v) / Math.log10(1 + maxHp) * 100);   // can/kalkan çubuğu (logaritmik)
  const ciz = () => {
    const s = f.q.trim().toLowerCase();
    const l = liste.filter(u => (f.filtre === 'hepsi' || (f.filtre === 'harita' ? u.nerede.length || u.yeni : f.filtre === 'etkinlik' ? u.etkinlik
      : f.filtre === 'degisti' ? u.degisti : u.yeni)) && (!s || npcAdi(u).toLowerCase().includes(s)));
    doldur(izgara, ...l.map(u => h('button', { type: 'button', class: 'de-npc' + (f.secili === u.tip ? ' on' : '') + (u.degisti ? ' degisti' : ''),
      onclick: () => { f.secili = u.tip; ciz(); } }, npcIkon(u, 40),
      h('div', { class: 'de-npc-ad' }, h('b', null, npcAdi(u)), h('div', { class: 'de-cubuklar' },
        h('i', { class: 'hp', style: { width: olcek(u.hp) + '%' } }), h('i', { class: 'sh', style: { width: olcek(u.kalkan) + '%' } }))),
      u.yeni ? badge(T('Yeni'), 'orange') : u.saldirgan ? h('span', { class: 'de-saldirgan', title: T('Saldırgan') }, icon('zap')) : null)),
      !l.length ? h('div', { class: 'empty small muted' }, T('Eşleşen uzaylı yok.')) : null);
    const u = liste.find(x => x.tip === f.secili) || l[0];
    if (u && !f.secili) { f.secili = u.tip; izgara.querySelector('.de-npc')?.classList.add('on'); }
    doldur(detay, u ? uzayliDetay(u, liste, ciz) : h('div', { class: 'empty muted' }, T('Soldan bir uzaylı seç.')));
  };
  const seg = h('div', { class: 'seg' }, [['harita', N('Haritalarda')], ['etkinlik', N('Etkinlik')], ['degisti', N('Değiştirilenler')], ['yeni', N('Yeni')], ['hepsi', N('Hepsi')]].map(([k, ad]) =>
    h('button', { class: f.filtre === k ? 'on info' : '', onclick: () => { f.filtre = k; deBolumCiz(); } }, T(ad))));
  doldur(alan, h('div', { class: 'card' }, deBaslik(b, h('input', { class: 'input', style: { width: '200px' }, placeholder: T('Uzaylı ara…'), value: f.q, oninput: e => { f.q = e.target.value; ciz(); } }), seg),
    h('div', { class: 'de-iki' }, izgara, detay)));
  ciz();
}

function uzayliDetay(u, liste, yenile) {
  const t = JSON.parse(JSON.stringify(u.tam)), std = u.standart;
  const yol = jp('tipler', u.tip);
  const kaydet = () => {
    Object.assign(u, { ad: t.ad, hp: t.hp, kalkan: t.kalkan, hasar: t.hasar, hiz: t.hiz, saldirgan: t.saldirgan, odul: t.odul, kargo: t.kargo, tam: t, degisti: true });
    deYama('npc.json', yol, t);
  };
  const geri = async () => { if (await deGeriAl('npc.json', yol)) { DE.uzayli = null; deBolumCiz(); } };
  const satir = (ad, alanAdi, opts) => h('div', { class: 'de-alan-satir' + (std && std[alanAdi] !== t[alanAdi] ? ' degisti' : '') },
    h('label', null, ad), deSayi(t[alanAdi], v => { t[alanAdi] = v; kaydet(); yenileSatirlar(); }, opts),
    std ? deStd(std[alanAdi], t[alanAdi], () => { t[alanAdi] = std[alanAdi]; kaydet(); yenileSatirlar(); }) : null);
  const kutu = h('div', { class: 'stack', style: { gap: '8px' } });
  const yenileSatirlar = () => doldur(kutu, 
    satir(T('Can'), 'hp', { max: 50000000, adim: 100, gen: 110 }), satir(T('Kalkan'), 'kalkan', { max: 50000000, adim: 100, gen: 110 }),
    satir(T('Hasar'), 'hasar', { max: 1000000, adim: 10 }), satir(T('Hız'), 'hiz', { max: 2000, adim: 5 }),
    h('div', { class: 'de-alan-satir' + (std && std.saldirgan !== t.saldirgan ? ' degisti' : '') }, h('label', null, T('Saldırgan')),
      h('label', { class: 'switch' }, h('input', { type: 'checkbox', checked: t.saldirgan, onchange: e => { t.saldirgan = e.target.checked; kaydet(); yenileSatirlar(); } }), h('span')),
      h('span', { class: 'small muted' }, t.saldirgan ? T('Seni görünce saldırır.') : T('Yalnız saldırınca karşılık verir.'))),
    h('div', { class: 'de-ara-baslik' }, T('Öldürme ödülü')),
    h('div', { class: 'de-odul-izgara' }, ODUL_ALAN.map(([k, ad, g]) => h('div', { class: 'de-odul' + (std && (std.odul || {})[k] !== t.odul[k] ? ' degisti' : '') },
      art(g, 'de-odul-ikon'), h('div', null, h('div', { class: 'small muted' }, T(ad)), deSayi(t.odul[k] || 0, v => { t.odul[k] = v; kaydet(); }, { max: 1e9, adim: k === 'uridyum' ? 1 : 10, gen: 86 }))))),
    h('div', { class: 'de-ara-baslik' }, T('Kargo kutusu (cevher)')),
    h('div', { class: 'de-kargo' }, Object.entries(ORE_ADI).filter(([i]) => t.kargo[i] || +i < 8).map(([i, loot]) =>
      h('div', { class: 'de-kargo-oge' + (t.kargo[i] ? ' var' : '') }, oyunIkon(loot, 26, null, 'box'), h('span', { class: 'small' }, esyaAdi(loot)),
        deSayi(t.kargo[i] || 0, v => { if (v) t.kargo[i] = v; else delete t.kargo[i]; kaydet(); }, { max: 100000, adim: 1, gen: 64 })))));
  yenileSatirlar();
  const adInp = h('input', { class: 'input de-ad-inp', value: t.ad, maxlength: 60, onchange: e => { t.ad = e.target.value; kaydet(); } });
  const yeniTuret = async () => {
    const ad = await promptBox(T('Yeni uzaylı türet'), T('Yeni uzaylının oyunda görünen adı'), '-=[ ' + npcAdi(u) + ' X ]=-'); if (ad == null) return;
    const n = Math.max(0, ...liste.filter(x => x.tip.startsWith('ozel_')).map(x => +x.tip.slice(5) || 0)) + 1;
    const yeni = Object.assign(JSON.parse(JSON.stringify(t)), { ad, model: t.model || u.tip, npc_kimlik: null, _kaynak: 'Dünya Editörü: ' + u.tip });
    delete yeni.npc_kimlik; delete yeni.etkinlik; delete yeni.haritalar;
    const r = await deYama('npc.json', jp('tipler', 'ozel_' + n), yeni, { ms: 0 });
    if (r) { toast(T('Yeni uzaylı oluşturuldu. Haritalar bölümünden bir haritanın doğma listesine ekleyebilirsin.'), 'ok'); DE.uzayli = null; DE.sec.uz.secili = 'ozel_' + n; DE.sec.uz.filtre = 'yeni'; deBolumCiz(); }
  };
  return h('div', { class: 'stack', style: { gap: '14px' } },
    h('div', { class: 'de-detay-bas' }, npcIkon(u, 64), h('div', { style: { flex: 1, minWidth: 0 } }, adInp,
      h('div', { class: 'small muted' }, u.yeni ? T('Yeni uzaylı · model: {0}', u.model) : T('Tür {0}', u.tip), std && std.ad !== t.ad ? [' · ', deStd(std.ad, t.ad, () => { t.ad = std.ad; adInp.value = std.ad; kaydet(); }, x => x)] : null))),
    kutu,
    h('div', { class: 'de-ara-baslik' }, T('Nerede doğar')),
    u.nerede.length ? h('div', { class: 'chips' }, u.nerede.map(m => h('button', { type: 'button', class: 'chip link', onclick: () => {
      const hm = (DE_HARITALAR || []).find(x => x.ad === m); DE.bolum = 'haritalar'; DE.sec = { hr: { secili: hm ? hm.id : null } }; deMenuSay(); deBolumCiz(); } }, icon('map'), m)))
      : h('div', { class: 'small muted' }, T('Hiçbir haritanın doğma listesinde değil.')),
    h('div', { class: 'row wrap', style: { gap: '8px', marginTop: '6px' } },
      btn(T('Bundan yeni uzaylı türet'), yeniTuret, 'sm', 'copy'),
      u.degisti && !u.yeni ? btn(T('Standarda döndür'), geri, 'sm ghost', 'undo') : null,
      u.yeni ? btn(T('Sil'), async () => {
        if (await confirmBox(T('Uzaylı silinsin mi?'), T('Doğma listelerindeki satırları da kalkar.'), { ok: T('Sil'), danger: true })) {
          const r = await deYama('npc.json', yol, { $sil: true }, { ms: 0 }); if (r) { DE.uzayli = null; DE.sec.uz.secili = null; deBolumCiz(); } }
      }, 'sm danger', 'trash') : null));
}

// ================================================================== HARİTALAR
const HR_ARAC = [['sec', N('Seç ve taşı'), 'move'], ['bolge', N('Doğma bölgesi'), 'target'], ['in', N('İn (sabit doğma noktası)'), 'nest'], ['guvenli', N('Güvenli bölge'), 'shield']];
const HR_KATMAN = [['izgara', N('Izgara')], ['engel', N('Engeller')], ['guvenli', N('Güvenli bölgeler')], ['portal', N('Portallar')], ['bolge', N('Doğma bölgeleri')], ['in', N('İnler')]];
const HR_FIRMA = { mmo: N('MMO'), eic: N('EIC'), vru: N('VRU'), savas: N('Savaş'), korsan: N('Korsan'), bl: N('Black Light'), diger: N('Diğer') };

async function deHaritalar(alan, b) {
  const r = await act(() => api('/api/dunya/bolum?bolum=haritalar&dunya=' + encodeURIComponent(DE.did))); if (!r || DE.bolum !== 'haritalar') return;
  DE_HARITALAR = r.haritalar;
  await uzayliListesi();
  const f = DE.sec.hr || (DE.sec.hr = {});
  f.arac = f.arac || 'sec'; f.katman = f.katman || { izgara: true, engel: true, guvenli: true, portal: true, bolge: true, in: true };
  if (!f.secili || !r.haritalar.some(x => x.id === f.secili)) f.secili = r.haritalar[0]?.id;
  const gruplar = {};
  r.haritalar.forEach(x => (gruplar[x.firma] = gruplar[x.firma] || []).push(x));
  const liste = h('div', { class: 'de-hliste' }, Object.entries(gruplar).map(([fi, xs]) => h('div', { class: 'de-hgrup' },
    h('div', { class: 'de-hgrup-ad f-' + fi }, T(HR_FIRMA[fi] || fi)),
    h('div', { class: 'de-hgrup-ic' }, xs.map(x => h('button', { type: 'button', class: 'de-hcip f-' + x.firma + (x.id === f.secili ? ' on' : '') + (x.degisti ? ' degisti' : ''),
      title: T('{0} uzaylı', fmtN(x.uzayli)), onclick: () => { f.secili = x.id; f.nesne = null; deBolumCiz(); } }, x.ad))))));
  const tuval = h('div', { class: 'de-tuval-kart' }), panel = h('div', { class: 'de-hpanel' });
  doldur(alan, h('div', { class: 'card de-harita-kart' }, deBaslik(b), liste, h('div', { class: 'de-harita' }, tuval, panel)));
  const hm = await act(() => api('/api/dunya/harita?dunya=' + encodeURIComponent(DE.did) + '&id=' + f.secili)); if (!hm || DE.bolum !== 'haritalar') return;
  haritaEditor(hm, tuval, panel, f);
}

function haritaEditor(hm, tuval, panel, f) {
  const [W, H] = hm.boyut, duzen = JSON.parse(JSON.stringify(hm.duzen || {}));
  duzen.guvenli = duzen.guvenli || []; duzen.inler = duzen.inler || {}; duzen.portallar = duzen.portallar || {};
  const npc = hm.npc.map(g => Object.assign({}, g));
  const uz = tip => (DE.uzayli || []).find(u => u.tip === tip);
  const kaydetNpc = () => { deYama('npc.json', jp('haritalar', hm.id, 'npc'), npc.map(g => g.bolge ? { tip: g.tip, adet: g.adet, bolge: g.bolge } : { tip: g.tip, adet: g.adet })); isaretle(); };
  const kaydetDuzen = () => { const d = JSON.parse(JSON.stringify(duzen)); if (!d.guvenli.length) delete d.guvenli; if (!Object.keys(d.inler).length) delete d.inler;
    if (!Object.keys(d.portallar).length) delete d.portallar; deYama('harita_duzeni.json', jp('haritalar', hm.id), d); isaretle(); };
  const isaretle = () => { const c = document.querySelector('.de-hcip.on'); if (c) c.classList.add('degisti'); };

  // ---- tuval (SVG, oyun birimleri)
  const svg = document.createElementNS(SVGNS, 'svg');
  svg.setAttribute('viewBox', `0 0 ${W} ${H}`); svg.setAttribute('class', 'de-svg');
  svg.style.setProperty('--s', W / 21000);      // etiketlerin boyu harita ölçeğiyle
  const el = (tag, at, ...kids) => { const e = document.createElementNS(SVGNS, tag); for (const [k, v] of Object.entries(at || {})) e.setAttribute(k, v); kids.forEach(k => k && e.append(k)); return e; };
  const S1 = W / 21000;            // ölçek: 2x haritada işaretler de büyür
  // tepeden işaret (gorsel/harita_<ad>.webp, OP-011): merkez (x, y), boy oyun birimi
  const isaret = (ad, x, y, boy) => el('image', { href: 'gorsel/harita_' + ad + '.webp', x: x - boy * S1 / 2, y: y - boy * S1 / 2, width: boy * S1, height: boy * S1, class: 'isaret' });
  const nokta = e => { const p = svg.createSVGPoint(); p.x = e.clientX; p.y = e.clientY; const q = p.matrixTransform(svg.getScreenCTM().inverse()); return [Math.round(Math.max(0, Math.min(W, q.x))), Math.round(Math.max(0, Math.min(H, q.y)))]; };
  let surukle = null;
  const surukleBas = (e, nesne, ayarla, bitti) => { e.stopPropagation(); e.preventDefault(); f.nesne = nesne; surukle = { ayarla, bitti, oynadi: false }; svg.setPointerCapture(e.pointerId); cizPanel(); ciz(); };
  svg.addEventListener('pointermove', e => { if (!surukle) return; surukle.oynadi = true; surukle.ayarla(nokta(e)); ciz(); });
  svg.addEventListener('pointerup', () => { if (surukle) { const s = surukle; surukle = null; if (s.oynadi) s.bitti(); cizPanel(); } });
  svg.addEventListener('pointerdown', async e => {
    if (e.target !== svg && !e.target.classList.contains('de-zemin')) return;
    const [x, y] = nokta(e);
    if (f.arac === 'guvenli') { duzen.guvenli.push([x, y, 1500 * S1 | 0]); f.nesne = { tur: 'guvenli', i: duzen.guvenli.length - 1 }; kaydetDuzen(); }
    else if (f.arac === 'bolge' || f.arac === 'in') {
      const adaylar = f.arac === 'bolge' ? npc.filter(g => !g.bolge) : npc;
      if (!adaylar.length) return toast(f.arac === 'bolge' ? T('Bütün türlerin bölgesi var. Önce listeye uzaylı ekle.') : T('Önce listeye uzaylı ekle.'), 'info');
      const sec = adaylar.length === 1 ? adaylar[0] : await new Promise(res => popMenuAt(e.clientX, e.clientY, adaylar.map(g => ({ label: npcAdi(uz(g.tip)) + ' ×' + g.adet, ic: 'alien', fn: () => res(g) }))));
      if (!sec) return;
      if (f.arac === 'bolge') { sec.bolge = [x, y, 2500 * S1 | 0]; f.nesne = { tur: 'bolge', tip: sec.tip }; kaydetNpc(); }
      else { (duzen.inler[sec.tip] = duzen.inler[sec.tip] || []).push([x, y]); f.nesne = { tur: 'in', tip: sec.tip, i: duzen.inler[sec.tip].length - 1 }; kaydetDuzen(); }
    } else { f.nesne = null; }
    cizPanel(); ciz();
  });
  const ciz = () => {
    doldur(svg);
    svg.append(el('rect', { x: 0, y: 0, width: W, height: H, class: 'de-zemin' }));
    if (f.katman.izgara) for (let x = 1000; x < W; x += 1000) svg.append(el('line', { x1: x, y1: 0, x2: x, y2: H, class: x % 5000 ? 'iz' : 'iz kalin' }));
    if (f.katman.izgara) for (let y = 1000; y < H; y += 1000) svg.append(el('line', { x1: 0, y1: y, x2: W, y2: y, class: y % 5000 ? 'iz' : 'iz kalin' }));
    if (f.katman.engel) hm.engeller.forEach(([x0, y0, x1, y1]) => svg.append(el('rect', { x: x0, y: y0, width: x1 - x0, height: y1 - y0, class: 'engel' })));
    if (hm.istasyon) { const [sx, sy] = hm.istasyon; svg.append(el('circle', { cx: sx, cy: sy, r: 1800 * S1, class: 'ist-alan' }), isaret('istasyon', sx, sy, 1100),
      el('text', { x: sx, y: sy + 860 * S1, class: 'etiket' }, document.createTextNode(T('İstasyon')))); }
    if (hm.yapi) svg.append(isaret('gorev_verici', hm.yapi[0], hm.yapi[1], 700));
    if (f.katman.guvenli) duzen.guvenli.forEach((z, i) => { const on = f.nesne?.tur === 'guvenli' && f.nesne.i === i;
      const c = el('circle', { cx: z[0], cy: z[1], r: z[2], class: 'guvenli' + (on ? ' on' : '') });
      c.addEventListener('pointerdown', e => f.arac === 'sec' && surukleBas(e, { tur: 'guvenli', i }, ([x, y]) => { z[0] = x; z[1] = y; }, kaydetDuzen));
      svg.append(c, isaret('guvenli', z[0], z[1], 520)); if (on) svg.append(tutamac(z, () => kaydetDuzen())); });
    if (f.katman.bolge) npc.filter(g => g.bolge).forEach(g => { const z = g.bolge, on = f.nesne?.tur === 'bolge' && f.nesne.tip === g.tip;
      const gr = el('g', { class: 'bolge' + (on ? ' on' : '') + (uz(g.tip)?.saldirgan ? ' saldirgan' : '') });
      gr.append(el('circle', { cx: z[0], cy: z[1], r: z[2] }), el('text', { x: z[0], y: z[1], class: 'etiket ortada' }, document.createTextNode(npcAdi(uz(g.tip)) + ' ×' + g.adet)));
      gr.addEventListener('pointerdown', e => f.arac === 'sec' && surukleBas(e, { tur: 'bolge', tip: g.tip }, ([x, y]) => { z[0] = x; z[1] = y; }, kaydetNpc));
      svg.append(gr); if (on) svg.append(tutamac(z, () => kaydetNpc())); });
    if (f.katman.in) Object.entries(duzen.inler).forEach(([tip, pts]) => pts.forEach((p, i) => { const on = f.nesne?.tur === 'in' && f.nesne.tip === tip && f.nesne.i === i;
      const pg = el('g', { class: 'in' + (on ? ' on' : '') }, el('circle', { cx: p[0], cy: p[1], r: 420 * S1, class: 'in-hale' }), isaret('in', p[0], p[1], 720));
      pg.addEventListener('pointerdown', e => f.arac === 'sec' && surukleBas(e, { tur: 'in', tip, i }, ([x, y]) => { p[0] = x; p[1] = y; }, kaydetDuzen));
      svg.append(pg, el('text', { x: p[0], y: p[1] + 620 * S1, class: 'etiket kucuk' }, document.createTextNode(npcAdi(uz(tip))))); }));
    if (f.katman.portal) hm.portallar.forEach(g => { const on = f.nesne?.tur === 'portal' && f.nesne.key === g.key, r = 330 * S1;
      const gr = el('g', { class: 'portal' + (on ? ' on' : '') + (duzen.portallar[g.key] ? ' tasindi' : '') });
      gr.append(el('circle', { cx: g.x, cy: g.y, r: r * 1.9, class: 'portal-alan' }), el('circle', { cx: g.x, cy: g.y, r: r * 1.25, class: 'portal-hale' }), isaret('portal', g.x, g.y, 900),
        el('text', { x: g.x, y: g.y - r * 2.3, class: 'etiket' }, document.createTextNode('→ ' + g.hedef)));
      gr.addEventListener('pointerdown', e => f.arac === 'sec' && surukleBas(e, { tur: 'portal', key: g.key }, ([x, y]) => { g.x = x; g.y = y; duzen.portallar[g.key] = [x, y]; }, kaydetDuzen));
      svg.append(gr); });
  };
  // yarıçap tutamacı (seçili daire): sağ kenarından sürükle
  const tutamac = (z, bitti) => { const t = el('circle', { cx: z[0] + z[2], cy: z[1], r: 160 * S1, class: 'tutamac' });
    t.addEventListener('pointerdown', e => surukleBas(e, f.nesne, ([x, y]) => { z[2] = Math.max(200, Math.round(Math.hypot(x - z[0], y - z[1]))); }, bitti)); return t; };

  const araclar = h('div', { class: 'de-araclar' }, h('div', { class: 'seg' }, HR_ARAC.map(([k, ad, ic]) => h('button', { class: f.arac === k ? 'on info' : '', title: T(ad),
    onclick: e => { f.arac = k; e.currentTarget.parentNode.querySelectorAll('button').forEach(x => x.classList.toggle('on', x === e.currentTarget)); e.currentTarget.parentNode.querySelectorAll('button').forEach(x => x.classList.toggle('info', x === e.currentTarget)); svg.dataset.arac = k; ipucu(); } },
      k === 'in' || k === 'guvenli' ? art('harita_' + k, 'de-arac-ikon') : icon(ic)))),
    h('span', { class: 'de-arac-ipucu small muted', id: 'de-arac-ipucu' }), h('span', { class: 'spacer' }),
    btn('', ev => popMenu(ev.currentTarget, HR_KATMAN.map(([k, ad]) => ({ label: T(ad) + (f.katman[k] ? '  ✓' : ''), ic: f.katman[k] ? 'check' : 'layers', fn: () => { f.katman[k] = !f.katman[k]; ciz(); } }))), 'sm ghost icon', 'layers', { title: T('Katmanlar') }));
  const ipucu = () => { const e = $('#de-arac-ipucu'); if (e) e.textContent = { sec: T('Nesneleri sürükle; seçili dairenin yarıçapını kenarındaki noktadan değiştir.'),
    bolge: T('Haritaya tıkla: seçtiğin uzaylı türü bu dairenin içinde doğar.'), in: T('Haritaya tıkla: türün sabit doğma noktası (uzaylılar burada belirir).'),
    guvenli: T('Haritaya tıkla: güvenli bölge (uzaylılar saldırmaz, doğmaz).') }[f.arac]; };
  svg.dataset.arac = f.arac;
  doldur(tuval, araclar, h('div', { class: 'de-svg-kap' }, svg), h('div', { class: 'de-tuval-alt small muted' },
    h('span', null, hm.ad + ' · ' + fmtN(W) + ' × ' + fmtN(H)), h('span', { class: 'spacer' }),
    h('span', { class: 'de-lejant' }, art('harita_portal'), T('Portal'), art('harita_guvenli'), T('Güvenli'), h('i', { class: 'l-bolge' }), T('Doğma bölgesi'), art('harita_in'), T('İn'), h('i', { class: 'l-engel' }), T('Engel'))));
  ipucu(); ciz();

  // ---- sağ panel: seçili nesne ya da doğma listesi
  const cizPanel = () => {
    const n = f.nesne, out = [];
    if (n) {
      const geri = btn(T('Seçimi bırak'), () => { f.nesne = null; cizPanel(); ciz(); }, 'sm ghost', 'arrowL');
      if (n.tur === 'portal') {
        const g = hm.portallar.find(x => x.key === n.key);
        out.push(h('div', { class: 'de-ara-baslik' }, T('Portal → {0}', g.hedef)), konum(g, v => { g.x = v[0]; g.y = v[1]; duzen.portallar[g.key] = v; kaydetDuzen(); ciz(); }),
          duzen.portallar[g.key] ? btn(T('Standart yerine döndür'), () => { delete duzen.portallar[g.key]; kaydetDuzen(); toast(T('Portal standart yerinde (sayfayı yenileyince görünür).'), 'info'); }, 'sm ghost', 'undo') : null);
      } else if (n.tur === 'guvenli') {
        const z = duzen.guvenli[n.i];
        out.push(h('div', { class: 'de-ara-baslik' }, T('Güvenli bölge')), konum(z, v => { z[0] = v[0]; z[1] = v[1]; kaydetDuzen(); ciz(); }),
          h('div', { class: 'de-alan-satir' }, h('label', null, T('Yarıçap')), deSayi(z[2], v => { z[2] = v; kaydetDuzen(); ciz(); }, { min: 100, max: 6000, adim: 100 })),
          btn(T('Bölgeyi sil'), () => { duzen.guvenli.splice(n.i, 1); f.nesne = null; kaydetDuzen(); cizPanel(); ciz(); }, 'sm danger', 'trash'));
      } else if (n.tur === 'bolge') {
        const g = npc.find(x => x.tip === n.tip);
        out.push(h('div', { class: 'de-ara-baslik' }, T('Doğma bölgesi')), h('div', { class: 'row', style: { gap: '8px' } }, npcIkon(uz(g.tip), 32), h('b', null, npcAdi(uz(g.tip)) + ' ×' + g.adet)),
          konum(g.bolge, v => { g.bolge[0] = v[0]; g.bolge[1] = v[1]; kaydetNpc(); ciz(); }),
          h('div', { class: 'de-alan-satir' }, h('label', null, T('Yarıçap')), deSayi(g.bolge[2], v => { g.bolge[2] = v; kaydetNpc(); ciz(); }, { min: 200, max: 15000, adim: 100 })),
          h('p', { class: 'small muted' }, T('Uzaylılar bu dairenin içinde doğar ve yeniden doğar; sonra haritada dolaşırlar.')),
          btn(T('Bölgeyi kaldır (haritaya dağılsın)'), () => { delete g.bolge; f.nesne = null; kaydetNpc(); cizPanel(); ciz(); }, 'sm danger', 'trash'));
      } else if (n.tur === 'in') {
        const p = duzen.inler[n.tip][n.i];
        out.push(h('div', { class: 'de-ara-baslik' }, T('İn: {0}', npcAdi(uz(n.tip)))), konum(p, v => { p[0] = v[0]; p[1] = v[1]; kaydetDuzen(); ciz(); }),
          h('p', { class: 'small muted' }, T('Bu türün uzaylıları yalnız inlerinde doğar (birden çok in varsa boş olanda).')),
          btn(T('İni sil'), () => { duzen.inler[n.tip].splice(n.i, 1); if (!duzen.inler[n.tip].length) delete duzen.inler[n.tip]; f.nesne = null; kaydetDuzen(); cizPanel(); ciz(); }, 'sm danger', 'trash'));
      }
      doldur(panel, h('div', { class: 'stack', style: { gap: '10px' } }, geri, ...out));
      return;
    }
    const toplam = npc.reduce((a, g) => a + g.adet, 0);
    const satir = g => { const u = uz(g.tip);
      return h('div', { class: 'de-dogma' }, npcIkon(u, 34), h('div', { class: 'de-dogma-ad' }, h('b', { title: npcAdi(u) }, npcAdi(u)),
        h('div', { class: 'small muted' }, u?.saldirgan ? T('Saldırgan') : T('Barışçıl'), g.bolge ? ' · ' + T('bölgede') : '', duzen.inler[g.tip] ? ' · ' + T('{0} in', duzen.inler[g.tip].length) : ''),
        deSayi(g.adet, v => { g.adet = v; kaydetNpc(); toplamEl.textContent = T('{0} uzaylı', fmtN(npc.reduce((a, x) => a + x.adet, 0))); ciz(); }, { max: 300, gen: 52 })),
        h('div', { class: 'de-dogma-eylem' },
          btn('', () => { if (g.bolge) { f.nesne = { tur: 'bolge', tip: g.tip }; } else { g.bolge = [W / 2 | 0, H / 2 | 0, 2500 * S1 | 0]; f.nesne = { tur: 'bolge', tip: g.tip }; kaydetNpc(); } cizPanel(); ciz(); },
            'sm ghost icon' + (g.bolge ? ' on' : ''), 'target', { title: g.bolge ? T('Bölgeyi seç') : T('Doğma bölgesi ekle') }),
          btn('', () => { npc.splice(npc.indexOf(g), 1); kaydetNpc(); cizPanel(); ciz(); }, 'sm ghost icon', 'x', { title: T('Listeden çıkar') })));
    };
    const toplamEl = h('span', { class: 'badge info' }, T('{0} uzaylı', fmtN(toplam)));
    const std = hm.standart;
    doldur(panel, h('div', { class: 'stack', style: { gap: '10px' } },
      h('div', { class: 'row between' }, h('div', { class: 'de-ara-baslik', style: { margin: 0 } }, T('Doğan uzaylılar')), toplamEl),
      npc.length ? h('div', { class: 'stack', style: { gap: '6px' } }, npc.map(satir)) : h('div', { class: 'small muted' }, T('Bu haritada uzaylı doğmuyor.')),
      btn(T('Uzaylı ekle'), async () => { const u = await uzayliSec(T('Haritaya uzaylı ekle')); if (!u) return;
        const v = npc.find(g => g.tip === u.tip); if (v) v.adet += 5; else npc.push({ tip: u.tip, adet: 10 }); kaydetNpc(); cizPanel(); ciz(); }, 'sm primary', 'plus'),
      h('div', { class: 'de-ara-baslik' }, T('Bonus kutuları')),
      h('div', { class: 'de-alan-satir' }, art('kaynak_kredi', 'de-odul-ikon'), deSayi(hm.bonus_kutu, v => { hm.bonus_kutu = v; deYama('npc.json', jp('haritalar', hm.id, 'bonus_kutu'), v); isaretle(); }, { max: 300, gen: 60 }),
        deStd(std.bonus_kutu, hm.bonus_kutu, () => { hm.bonus_kutu = std.bonus_kutu; deYama('npc.json', jp('haritalar', hm.id, 'bonus_kutu'), std.bonus_kutu); cizPanel(); })),
      h('p', { class: 'small muted' }, T('Adetler Oyun Ayarları\'ndaki uzaylı sayısı ve kutu bolluğu çarpanlarıyla çarpılır.')),
      cevherBlogu(hm, isaretle),
      (hm.degisti.npc || hm.degisti.duzen || hm.degisti.bonus_kutu || hm.cevher.ozel) ? btn(T('Haritayı standarda döndür'), async () => {
        if (!await confirmBox(T('{0} standarda dönsün mü?', hm.ad), T('Doğma listesi, bölgeler, inler, güvenli bölgeler, portal yerleri ve cevherler standart hâline döner.'), { ok: T('Standarda döndür'), danger: true })) return;
        for (const [d, y] of [['npc.json', jp('haritalar', hm.id, 'npc')], ['npc.json', jp('haritalar', hm.id, 'bonus_kutu')], ['harita_duzeni.json', jp('haritalar', hm.id)], ['esyalar.json', hm.cevher.yol]]) await deGeriAl(d, y);
        deBolumCiz(); }, 'sm ghost', 'undo') : null));
  };
  const konum = (v, cb) => h('div', { class: 'de-alan-satir' }, h('label', null, T('Konum')), deSayi(v[0], x => cb([x, v[1]]), { max: W, adim: 100, gen: 76 }),
    deSayi(v[1], y => cb([v[0], y]), { max: H, adim: 100, gen: 76 }));
  cizPanel();
}
function popMenuAt(x, y, items) {
  const a = h('span', { style: { position: 'fixed', left: x + 'px', top: y + 'px', width: '1px', height: '1px' } }); document.body.append(a);
  popMenu(a, items); setTimeout(() => a.remove(), 0);
}

// ================================================================== GÖREVLER
const GV_TUR = { 6: ['alien', N('Öldür'), 'npc'], 27: ['alien', N('Öldür (toplam)'), 'npc'], 67: ['box', N('Topla'), 'esya'], 34: ['map', N('Haritaya git'), 'harita'],
  52: ['cart', N('Cevher sat'), 'cevher'], 55: ['gift', N('Bonus kutusu topla'), null], 51: ['box', N('Kargo kutusu topla'), null], 28: ['users', N('Oyuncu yen'), null],
  2: ['clock', N('Süre sınırı'), 'sure'], 63: ['clock', N('Gerçek zamanlı süre'), 'sure'], 3: ['clock', N('Haritada kal'), 'sure'], 62: ['flag', N('Görev vericiye dön'), null],
  53: ['star', N('Seviyeye ulaş'), null], 35: ['x', N('Öl'), null], 42: ['link', N('Portaldan geç'), null], 80: ['ring', N('Galaksi Kapısı bitir'), null],
  13: ['zap', N('Yol al'), null], 7: ['zap', N('Hasar ver'), null], 9: ['shield', N('Hasar al'), null] };
const GV_FILTRE = [['hepsi', N('Hepsi')], ['ana', N('Ana görevler')], ['tekrar', N('Günlük ve haftalık')], ['etkinlik', N('Etkinlik')], ['degisti', N('Değiştirilenler')], ['yeni', N('Yeni')], ['kapali', N('Kapalı')]];
const ORE_ESKI = { 1: 'resource_ore_prometium', 2: 'resource_ore_endurium', 3: 'resource_ore_terbium', 4: 'resource_ore_xenomit', 11: 'resource_ore_prometid',
  12: 'resource_ore_duranium', 13: 'resource_ore_promerium', 14: 'resource_ore_seprom', 15: 'resource_ore_palladium', 42: 'resource_ore_osmium' };

// görev eşleşmesindeki harita: "@1-1" -> 1-1; "@own X-3" -> kendi X-3 (firmaya göre çözülür)
function haritaEtiket(x) {
  x = String(x).replace(/^@/, '');
  const m = x.match(/^(own|enemy|any) (.+)$/);
  return m ? T({ own: N('Kendi {0}'), enemy: N('Düşman {0}'), any: N('Herhangi {0}') }[m[1]], m[2]) : x;
}
// koşulun hedefi (ne): uzaylı, eşya, cevher, harita adları
function kosulHedefi(c) {
  const t = GV_TUR[c.tur], es = c.eslesme || [];
  if (!t) return '';
  if (t[2] === 'npc') return es.map(k => npcAdi((DE.uzayli || []).find(u => String(u.npc_kimlik) === String(k))) || k).join(', ') || T('uzaylı');
  if (t[2] === 'esya') return es.map(esyaAdi).join(', ');
  if (t[2] === 'cevher') return es.map(k => ORE_ESKI[k] ? esyaAdi(ORE_ESKI[k]) : k).join(', ');
  if (t[2] === 'harita') return es.map(haritaEtiket).join(', ');
  return '';
}
function kosulMetni(c) {
  const t = GV_TUR[c.tur];
  if (!t) return T('Özel koşul (tür {0})', c.tur);
  if (t[2] === 'harita') return kosulHedefi(c);
  const hedef = t[2] === 'sure' ? fmtDur(c.hedef / 1000) : fmtN(c.hedef), ne = kosulHedefi(c);
  return ne ? T('{0} {1}', hedef, ne) : hedef;
}

async function deGorevler(alan, b) {
  await uzayliListesi();
  const r = await act(() => api('/api/dunya/bolum?bolum=gorevler&dunya=' + encodeURIComponent(DE.did))); if (!r || DE.bolum !== 'gorevler') return;
  const f = DE.sec.gv || (DE.sec.gv = { q: '', filtre: 'ana', secili: null, sinir: 150 });
  const liste = h('div', { class: 'de-gliste' }), detay = h('div', { class: 'de-detay' });
  const uygun = g => ({ hepsi: true, ana: !g.havuz && !g.etkinlik && g.turler.includes(2), tekrar: g.havuz || g.turler.some(t => t === 3 || t === 6),
    etkinlik: g.etkinlik || g.turler.includes(5), degisti: g.degisti, yeni: g.yeni, kapali: g.kapali })[f.filtre];
  const ciz = () => {
    const s = f.q.trim().toLowerCase();
    const l = r.gorevler.filter(g => uygun(g) && (!s || g.ad.toLowerCase().includes(s) || String(g.id) === s));
    doldur(liste, ...l.slice(0, f.sinir).map(g => h('button', { type: 'button', class: 'de-gorev' + (f.secili === g.id ? ' on' : '') + (g.degisti ? ' degisti' : '') + (g.kapali ? ' kapali' : ''),
      onclick: () => { f.secili = g.id; ciz(); } }, h('span', { class: 'de-sv' }, g.seviye || '—'),
      h('div', { class: 'de-gorev-ad' }, h('b', null, g.ad), h('div', { class: 'small muted ellipsis' }, g.kosullar.slice(0, 3).map(c => (GV_TUR[c.tur] ? T(GV_TUR[c.tur][1]) : '?') + ' ' + kosulMetni(c)).join(' · '))),
      h('div', { class: 'de-gorev-odul' }, g.oduller.slice(0, 3).map(([l]) => oyunIkon(l, 22, null, 'gift'))),
      g.yeni ? badge(T('Yeni'), 'orange') : g.kapali ? badge(T('Kapalı'), '') : null)),
      l.length > f.sinir ? h('button', { type: 'button', class: 'btn sm de-daha', onclick: () => { f.sinir += 300; ciz(); } }, T('{0} görev daha', fmtN(l.length - f.sinir))) : null,
      !l.length ? h('div', { class: 'empty small muted' }, T('Eşleşen görev yok.')) : null);
    if (!f.secili && l[0]) f.secili = l[0].id;
    if (f.secili) gorevDetay(f.secili, detay, g2 => { Object.assign(r.gorevler.find(x => x.id === g2.id) || {}, g2); ciz(); });
    else doldur(detay, h('div', { class: 'empty muted' }, T('Soldan bir görev seç.')));
  };
  const seg = h('div', { class: 'seg' }, GV_FILTRE.map(([k, ad]) => h('button', { class: f.filtre === k ? 'on info' : '', onclick: () => { f.filtre = k; f.secili = null; deBolumCiz(); } }, T(ad))));
  doldur(alan, h('div', { class: 'card' }, deBaslik(b, h('input', { class: 'input', style: { width: '200px' }, placeholder: T('Görev ara…'), value: f.q, oninput: e => { f.q = e.target.value; ciz(); } }),
    btn(T('Yeni görev'), () => yeniGorev(), 'primary', 'plus')), h('div', { style: { margin: '12px 0' } }, seg), h('div', { class: 'de-iki genis' }, liste, detay)));
  ciz();
}

async function gorevDetay(qid, kutu, guncellendi) {
  if (kutu.dataset.q !== String(qid)) doldur(kutu, h('div', { class: 'empty' }, h('div', { class: 'spin', style: { margin: '30px auto' } })));
  kutu.dataset.q = qid;
  const g = await act(() => api('/api/dunya/gorev?dunya=' + encodeURIComponent(DE.did) + '&id=' + qid)); if (!g || kutu.dataset.q !== String(qid)) return;
  const std = g.standart;
  const kaydet = async (degisiklik, yeniden = true) => {
    deKayitDurumu('kaydediliyor');
    const x = await act(() => api('/api/dunya/gorev', { dunya: DE.did, id: qid, degisiklik }));
    if (!x) return deKayitDurumu('hazir');
    const oz = await api('/api/dunya?dunya=' + encodeURIComponent(DE.did)).catch(() => null); if (oz) { DE.ozet = oz; deMenuSay(); deUyari(); }
    deKayitDurumu('kaydedildi'); guncellendi({ id: x.id, oduller: x.oduller, seviye: x.seviye, kosullar: x.kosullar.map(c => ({ tur: c.tur, hedef: c.hedef, eslesme: c.eslesme })), degisti: x.degisti, kapali: x.kapali, ad: x.ad });
    if (yeniden) gorevDetay(qid, kutu, guncellendi);
  };
  let zam = null;
  const geciktir = (fn, ms = 500) => { clearTimeout(zam); deKayitDurumu('kaydediliyor'); zam = setTimeout(fn, ms); };
  const kosul = (c, i) => {
    const t = GV_TUR[c.tur] || ['info', N('Özel koşul'), null], tur = t[2], sc = std?.kosullar?.[i];
    const altHarita = (c.alt.find(a => a.tur === 77) || {}).eslesme || [];
    const hedefSec = async () => {
      let es = null;
      if (tur === 'npc') { const u = await uzayliSec(T('Hangi uzaylı?'), { kimlikli: true }); if (u) es = [String(u.npc_kimlik)]; }
      else if (tur === 'esya') { const l = await esyaSec(T('Hangi eşya toplanacak?')); if (l) es = [l]; }
      else if (tur === 'cevher') { const l = await new Promise(res => popMenu(kutu.querySelector('.de-kosul[data-i="' + i + '"] .de-kosul-hedef'), Object.entries(ORE_ESKI).map(([k, loot]) => ({ label: esyaAdi(loot), ic: 'box', fn: () => res([k]) })))); es = l; }
      else if (tur === 'harita') { const l = await haritaSec(T('Hangi harita?'), [], { coklu: false }); if (l) es = l; }
      if (es) kaydet({ kosullar: [{ id: c.id, eslesme: es }] });
    };
    const haritaKisit = async () => { const l = await haritaSec(T('Yalnız bu haritalarda'), altHarita.map(x => String(x).replace(/^@/, ''))); if (l) kaydet({ kosullar: [{ id: c.id, harita: l }] }); };
    return h('div', { class: 'de-kosul', 'data-i': i }, h('div', { class: 'de-kosul-ikon' }, icon(t[0])),
      h('div', { class: 'de-kosul-govde' }, h('div', { class: 'small muted' }, T(t[1])),
        h('div', { class: 'row wrap', style: { gap: '8px' } },
          tur === 'sure' ? h('span', { class: 'de-kosul-metin' }, fmtDur(c.hedef / 1000)) : c.tur === 34 ? null : deSayi(c.hedef, v => geciktir(() => kaydet({ kosullar: [{ id: c.id, hedef: v }] }, false)), { min: 0, max: 1e7, gen: 70 }),
          tur && tur !== 'sure' ? h('button', { type: 'button', class: 'chip link de-kosul-hedef', onclick: hedefSec, title: T('Değiştir') },
            tur === 'esya' ? oyunIkon(c.eslesme[0], 20, null, 'box') : tur === 'npc' ? npcIkon((DE.uzayli || []).find(u => String(u.npc_kimlik) === String(c.eslesme[0])), 20) : icon(t[0]),
            kosulHedefi(c) || T('Seç'), icon('edit')) : null,
          ['npc', 'esya', null].includes(tur) && c.tur !== 62 ? h('button', { type: 'button', class: 'chip link', onclick: haritaKisit, title: T('Harita kısıtı') }, icon('map'),
            altHarita.length ? altHarita.map(haritaEtiket).join(', ') : T('Her haritada')) : null,
          sc && sc.hedef !== c.hedef && tur !== 'sure' ? deStd(sc.hedef, c.hedef, () => kaydet({ kosullar: [{ id: c.id, hedef: sc.hedef }] })) : null)));
  };
  const odul = ([l, n], i) => h('div', { class: 'de-odul-cip' }, oyunIkon(l, 36, null, 'gift'), h('div', { class: 'de-odul-cip-ad' }, h('div', { class: 'small ellipsis', title: l }, esyaAdi(l)),
    deSayi(n, v => { g.oduller[i][1] = Math.max(1, v); geciktir(() => kaydet({ oduller: g.oduller }, false)); }, { min: 1, max: 1e9, gen: 84 })),
    btn('', () => { g.oduller.splice(i, 1); kaydet({ oduller: g.oduller }); }, 'sm ghost icon', 'x', { title: T('Ödülü kaldır') }));
  const hizli = [['currency_credits', 10000], ['currency_uridium', 500], ['currency_experience', 5000], ['currency_honour', 100]];
  doldur(kutu, h('div', { class: 'stack', style: { gap: '14px' } },
    h('div', { class: 'de-detay-bas' }, h('div', { class: 'de-gorev-rozet' }, icon('target')), h('div', { style: { flex: 1, minWidth: 0 } },
      g.yeni ? h('input', { class: 'input de-ad-inp', value: g.ad, maxlength: 60, onchange: e => kaydet({ ad: e.target.value }) }) : h('div', { class: 'de-h3' }, g.ad),
      h('div', { class: 'small muted' }, T('Görev {0}', g.id), g.yeni ? ' · ' + T('Bu dünyaya ait') : '', g.degisti && !g.yeni ? ' · ' + T('değiştirildi') : ''))),
    h('div', { class: 'de-ara-baslik' }, T('Oyundaki metin')),
    field(T('Başlık'), h('input', { class: 'input', value: g.baslik, maxlength: 80, placeholder: g.yeni ? T('Başlık yok') : T('Oyunun kendi başlığı'),
      onchange: e => kaydet({ baslik: e.target.value }) })),
    field(T('Açıklama'), h('textarea', { class: 'input', rows: 3, maxlength: 600, placeholder: T('Oyunun kendi açıklaması'), onchange: e => kaydet({ aciklama: e.target.value }) }, g.aciklama)),
    h('div', { class: 'small dim' }, T('Boş bırakırsan oyunun kendi metni görünür. Başlık ve açıklama oyunda OpenOrbit eklentisiyle (BepInEx) gösterilir.')),
    h('div', { class: 'de-alan-satir' }, h('label', null, T('Gereken seviye')), deSayi(g.seviye, v => geciktir(() => kaydet({ seviye: v }, false)), { min: 0, max: 40, gen: 56 }),
      std ? deStd(std.seviye, g.seviye, () => kaydet({ seviye: std.seviye })) : null),
    h('div', { class: 'de-alan-satir' }, h('label', null, T('Görev listede')), h('label', { class: 'switch' }, h('input', { type: 'checkbox', checked: !g.kapali, onchange: e => kaydet({ kapali: !e.target.checked }) }), h('span')),
      h('span', { class: 'small muted' }, g.kapali ? T('Kapalı: görev vericide görünmez (sürüyorsa bitirilebilir).') : T('Açık: koşulları tutan pilot alabilir.'))),
    h('div', { class: 'de-ara-baslik' }, T('Hedefler')),
    g.kosullar.length ? h('div', { class: 'stack', style: { gap: '8px' } }, g.kosullar.map(kosul)) : h('div', { class: 'small muted' }, T('Bu görevin hedefi yok.')),
    h('div', { class: 'de-ara-baslik' }, T('Ödüller')),
    h('div', { class: 'de-oduller' }, g.oduller.map(odul),
      h('button', { type: 'button', class: 'de-odul-ekle', onclick: async () => { const l = await esyaSec(T('Ödül ekle')); if (!l) return; g.oduller.push([l, l.startsWith('currency_') ? 1000 : 1]); kaydet({ oduller: g.oduller }); } }, icon('plus'), T('Ödül ekle'))),
    h('div', { class: 'chips' }, hizli.map(([l, n]) => h('button', { type: 'button', class: 'chip link', onclick: () => { const v = g.oduller.find(o => o[0] === l); if (v) v[1] += n; else g.oduller.push([l, n]); kaydet({ oduller: g.oduller }); } },
      icon('plus'), fmtN(n) + ' ' + esyaAdi(l)))),
    std && JSON.stringify(std.oduller) !== JSON.stringify(g.oduller) ? h('div', null, deStd(std.oduller, g.oduller, () => kaydet({ oduller: std.oduller }), o => T('{0} ödül', o.length))) : null,
    h('div', { class: 'de-ara-baslik' }, T('Önkoşullar')),
    h('div', { class: 'chips' }, g.onceki.map(x => h('span', { class: 'chip' }, icon('target'), g.adlar[x] || x,
      h('button', { type: 'button', class: 'de-cip-x', onclick: () => kaydet({ onceki: g.onceki.filter(y => y !== x) }) }, icon('x')))),
      h('button', { type: 'button', class: 'chip link', onclick: async () => { const q = await gorevSec(); if (q) kaydet({ onceki: [...g.onceki, q.id] }); } }, icon('plus'), T('Önkoşul ekle'))),
    h('div', { class: 'row wrap', style: { gap: '8px', marginTop: '6px' } },
      g.degisti && !g.yeni ? btn(T('Standarda döndür'), async () => { if (await deGeriAl(_gvDosya(g), jp('gorevler', g.id))) { guncellendi({ id: g.id, degisti: false }); gorevDetay(qid, kutu, guncellendi); } }, 'sm ghost', 'undo') : null,
      g.yeni ? btn(T('Görevi sil'), async () => {
        if (!await confirmBox(T('Görev silinsin mi?'), T('Bu dünyaya eklediğin görev silinir.'), { ok: T('Sil'), danger: true })) return;
        const r = await deYama('gorev_ekleri.json', jp('gorevler', g.id), { $sil: true }, { ms: 0 }); if (r) { DE.sec.gv.secili = null; deBolumCiz(); } }, 'sm danger', 'trash') : null)));
}
const _gvDosya = g => g.kaynak === 'ana' ? 'gorevler.json' : 'gorev_ekleri.json';

async function gorevSec() {
  const r = await act(() => api('/api/dunya/bolum?bolum=gorevler&dunya=' + encodeURIComponent(DE.did))); if (!r) return null;
  return new Promise(res => {
    let q = '', done = false;
    const l = h('div', { class: 'de-gliste kisa' });
    const ciz = () => { const s = q.trim().toLowerCase();
      doldur(l, ...r.gorevler.filter(g => !s || g.ad.toLowerCase().includes(s)).slice(0, 120).map(g => h('button', { type: 'button', class: 'de-gorev', onclick: () => { done = true; m.close(); res(g); } },
        h('span', { class: 'de-sv' }, g.seviye || '—'), h('div', { class: 'de-gorev-ad' }, h('b', null, g.ad))))); };
    const m = modal({ title: T('Önkoşul görev'), onclose: () => { if (!done) res(null); }, body: h('div', { class: 'stack', style: { gap: '10px' } },
      h('input', { class: 'input', placeholder: T('Görev ara…'), oninput: e => { q = e.target.value; ciz(); } }), l) });
    ciz();
  });
}

// yeni görev sihirbazı: 1 hedefler, 2 ödüller, 3 ad ve seviye
const YG_SABLON = [['avla', 'alien', N('Avla'), N('Uzaylı öldür')], ['topla', 'box', N('Topla'), N('Eşya ya da cevher topla')], ['kesif', 'map', N('Keşfet'), N('Bir haritaya git')],
  ['sat', 'cart', N('Ticaret'), N('Cevher sat')], ['kutu', 'gift', N('Bonus kutusu'), N('Bonus kutusu topla')], ['kargo', 'box', N('Kargo'), N('Kargo kutusu topla')]];
function yeniGorev() {
  const g = { ad: '', seviye: 1, hedefler: [], oduller: [['currency_credits', 10000], ['currency_experience', 2000]] };
  let adim = 0;
  const govde = h('div'), alt = h('div', { class: 'foot' });
  const m = modal({ title: T('Yeni görev'), wide: true, body: govde });
  m.box.append(alt);
  const hedefSatir = (x, i) => {
    const s = YG_SABLON.find(y => y[0] === x.tur);
    const sec = async () => {
      if (x.tur === 'avla') { const u = await uzayliSec(T('Hangi uzaylı?'), { kimlikli: true }); if (u) { x.eslesme = [String(u.npc_kimlik)]; x.etiket = npcAdi(u); x.ikon = u; } }
      else if (x.tur === 'topla') { const l = await esyaSec(T('Hangi eşya toplanacak?')); if (l) { x.eslesme = [l]; x.etiket = esyaAdi(l); x.loot = l; } }
      else if (x.tur === 'sat') { const l = await new Promise(res => popMenu(govde.querySelector('[data-h="' + i + '"] .de-kosul-hedef'), Object.entries(ORE_ESKI).map(([k, loot]) => ({ label: esyaAdi(loot), ic: 'box', fn: () => res([k, loot]) })))); if (l) { x.eslesme = [l[0]]; x.etiket = esyaAdi(l[1]); x.loot = l[1]; } }
      else if (x.tur === 'kesif') { const l = await haritaSec(T('Hangi harita?'), [], { coklu: false }); if (l) { x.eslesme = l; x.etiket = l[0]; } }
      ciz();
    };
    const secmeli = ['avla', 'topla', 'sat', 'kesif'].includes(x.tur);
    return h('div', { class: 'de-kosul', 'data-h': i }, h('div', { class: 'de-kosul-ikon' }, icon(s[1])), h('div', { class: 'de-kosul-govde' }, h('div', { class: 'small muted' }, T(s[3])),
      h('div', { class: 'row wrap', style: { gap: '8px' } }, x.tur !== 'kesif' ? deSayi(x.hedef, v => { x.hedef = Math.max(1, v); }, { min: 1, max: 1e7, gen: 70 }) : null,
        secmeli ? h('button', { type: 'button', class: 'chip link de-kosul-hedef' + (x.eslesme?.length ? '' : ' bos'), onclick: sec },
          x.loot ? oyunIkon(x.loot, 20, null, 'box') : x.ikon ? npcIkon(x.ikon, 20) : icon(s[1]), x.etiket || T('Seç'), icon('edit')) : null,
        x.tur !== 'kesif' ? h('button', { type: 'button', class: 'chip link', onclick: async () => { const l = await haritaSec(T('Yalnız bu haritalarda'), x.harita || []); if (l) { x.harita = l; ciz(); } } },
          icon('map'), x.harita?.length ? x.harita.join(', ') : T('Her haritada')) : null)),
      btn('', () => { g.hedefler.splice(i, 1); ciz(); }, 'sm ghost icon', 'x'));
  };
  const ciz = () => {
    const adimlar = h('div', { class: 'de-adimlar' }, [N('Hedefler'), N('Ödüller'), N('Ad ve seviye')].map((a, i) => h('div', { class: 'de-adim' + (i === adim ? ' on' : i < adim ? ' bitti' : '') }, h('b', null, i + 1), T(a))));
    let ic;
    if (adim === 0) ic = [h('p', { class: 'desc' }, T('Pilot ne yapsın? Bir ya da birkaç hedef ekle; hepsi tamamlanınca görev biter.')),
      h('div', { class: 'de-sablonlar' }, YG_SABLON.map(([k, ic2, ad, acik]) => h('button', { type: 'button', class: 'de-sablon', onclick: () => {
        g.hedefler.push({ tur: k, hedef: k === 'kesif' ? 1 : k === 'avla' ? 20 : k === 'sat' ? 100 : 10, eslesme: [] }); ciz();
        if (['avla', 'topla', 'kesif'].includes(k)) setTimeout(() => govde.querySelector('[data-h="' + (g.hedefler.length - 1) + '"] .de-kosul-hedef')?.click(), 50); } },
        icon(ic2), h('b', null, T(ad)), h('span', { class: 'small muted' }, T(acik))))),
      g.hedefler.length ? h('div', { class: 'stack', style: { gap: '8px', marginTop: '14px' } }, g.hedefler.map(hedefSatir)) : null];
    else if (adim === 1) ic = [h('p', { class: 'desc' }, T('Görev bitince pilot ne kazansın?')),
      h('div', { class: 'de-oduller' }, g.oduller.map(([l, n], i) => h('div', { class: 'de-odul-cip' }, oyunIkon(l, 36, null, 'gift'), h('div', { class: 'de-odul-cip-ad' }, h('div', { class: 'small ellipsis' }, esyaAdi(l)),
        deSayi(n, v => { g.oduller[i][1] = Math.max(1, v); }, { min: 1, max: 1e9, gen: 84 })), btn('', () => { g.oduller.splice(i, 1); ciz(); }, 'sm ghost icon', 'x'))),
        h('button', { type: 'button', class: 'de-odul-ekle', onclick: async () => { const l = await esyaSec(T('Ödül ekle')); if (l) { g.oduller.push([l, l.startsWith('currency_') ? 1000 : 1]); ciz(); } } }, icon('plus'), T('Ödül ekle')))];
    else ic = [field(T('Görevin adı'), h('input', { class: 'input', value: g.ad, maxlength: 60, placeholder: T('Örn. Streuner Avı'), oninput: e => { g.ad = e.target.value; } })),
      h('div', { class: 'de-alan-satir' }, h('label', null, T('Gereken seviye')), deSayi(g.seviye, v => { g.seviye = v; }, { min: 1, max: 40, gen: 56 })),
      h('div', { class: 'small muted' }, T('Görev, firmanın görev vericisinde (istasyon) listelenir; ad oyunda görevin başlığı olur.'))];
    doldur(govde, h('div', { class: 'stack', style: { gap: '12px' } }, adimlar, ...ic));
    const eksik = adim === 0 && (!g.hedefler.length || g.hedefler.some(x => ['avla', 'topla', 'sat', 'kesif'].includes(x.tur) && !x.eslesme?.length));
    doldur(alt, btn(adim ? T('Geri') : T('Vazgeç'), () => { if (adim) { adim--; ciz(); } else m.close(); }, 'ghost', adim ? 'arrowL' : null),
      adim < 2 ? btn(T('İleri'), () => { adim++; ciz(); }, 'primary', 'arrowR', { disabled: eksik, title: eksik ? T('Her hedef için ne yapılacağını seç.') : null })
        : btn(T('Görevi oluştur'), async () => {
          const x = await act(() => api('/api/dunya/gorev_yeni', { dunya: DE.did, ad: g.ad, seviye: g.seviye, hedefler: g.hedefler.map(y => ({ tur: y.tur, hedef: y.hedef, eslesme: y.eslesme, harita: y.harita })), oduller: g.oduller }), T('Görev oluşturuldu.'));
          if (!x) return;
          m.close(); DE.sec.gv = { q: '', filtre: 'yeni', secili: x.id, sinir: 150 };
          const oz = await api('/api/dunya?dunya=' + encodeURIComponent(DE.did)).catch(() => null); if (oz) { DE.ozet = oz; deMenuSay(); deUyari(); }
          deBolumCiz();
        }, 'primary', 'check'));
  };
  ciz();
}

// ================================================================== MAĞAZA
async function deMagaza(alan, b) {
  const r = await act(() => api('/api/dunya/bolum?bolum=magaza&dunya=' + encodeURIComponent(DE.did))); if (!r || DE.bolum !== 'magaza') return;
  const kats = Object.keys(r.kategoriler);
  if (!kats.length) return doldur(alan, h('div', { class: 'card' }, deBaslik(b), h('div', { class: 'empty muted' }, T('Mağaza kataloğu bulunamadı (data/yanitlar.json).'))));
  const f = DE.sec.mg || (DE.sec.mg = { kat: kats[0], q: '', filtre: 'hepsi' });
  if (!kats.includes(f.kat)) f.kat = kats[0];
  const izgara = h('div', { class: 'mg-izgara de-mg' });
  const fiyatMetni = (u, p) => fmtN(u) + (p === 'C' ? ' C.' : ' U.');
  const ciz = () => {
    const s = f.q.trim().toLowerCase();
    const l = r.kategoriler[f.kat].filter(it => (f.filtre === 'hepsi' || (f.filtre === 'degisti' ? it.dunya : it.dunya?.satista === false)) && (!s || esyaAdi(it.lootId).toLowerCase().includes(s) || it.lootId.includes(s)));
    doldur(izgara, ...l.map(it => { const d = it.dunya || {}, kapali = d.satista === false, degisti = d.fiyat != null;
      return h('button', { type: 'button', class: 'mg-kart de-mg-kart' + (kapali ? ' kapali' : '') + (it.dunya ? ' degisti' : ''), onclick: () => urunDuzenle(it, ciz) },
        oyunIkon(it.lootId, 64, null, 'cart'), h('div', { class: 'mg-ad', title: it.lootId }, esyaAdi(it.lootId)),
        h('div', { class: 'mg-fiyat ' + ((degisti ? d.para : it.para) === 'C' ? 'kre' : 'uri') }, kapali ? T('Satışta değil') : fiyatMetni(degisti ? d.fiyat : it.fiyat, degisti ? d.para : it.para)),
        degisti && !kapali ? h('div', { class: 'small dim de-ustu-cizili' }, fiyatMetni(it.fiyat, it.para)) : null); }),
      !l.length ? h('div', { class: 'empty small muted' }, T('Ürün yok.')) : null);
  };
  const KAT = typeof MG_KATEGORI !== 'undefined' ? MG_KATEGORI : {};
  doldur(alan, h('div', { class: 'stack' }, h('div', { class: 'card' },
    deBaslik(b, h('input', { class: 'input', style: { width: '180px' }, placeholder: T('Ara…'), value: f.q, oninput: e => { f.q = e.target.value; ciz(); } }),
      btn(T('Toplu fiyat'), () => topluFiyat(r.kategoriler[f.kat], ciz), 'sm', 'sliders')),
    h('div', { class: 'row wrap', style: { gap: '10px', marginTop: '12px' } },
      h('div', { class: 'seg' }, kats.map(c => h('button', { class: c === f.kat ? 'on info' : '', onclick: () => { f.kat = c; deBolumCiz(); } }, KAT[c] ? T(KAT[c]) : c,
        r.kategoriler[c].some(it => it.dunya) ? h('span', { class: 'de-nokta' }) : null))),
      h('div', { class: 'seg' }, [['hepsi', N('Hepsi')], ['degisti', N('Değiştirilenler')], ['kapali', N('Satıştan kaldırılanlar')]].map(([k, ad]) =>
        h('button', { class: f.filtre === k ? 'on info' : '', onclick: () => { f.filtre = k; deBolumCiz(); } }, T(ad))))),
    h('p', { class: 'small muted', style: { margin: '10px 0 0' } }, T('Oyun Ayarları\'ndaki mağaza fiyatı çarpanı bu fiyatların üstüne uygulanır. Dronların ve seviyeli P.E.T. ürünlerinin fiyatı kendi kuralıyla işler.'))),
    izgara));
  ciz();
}

function urunDuzenle(it, yenile) {
  const d = Object.assign({}, it.dunya || {}), sabit = it.sabit;
  let fiyat = d.fiyat ?? it.fiyat, para = d.para || it.para, satista = d.satista !== false;
  const kaydet = async () => {
    const deger = {}; if (!sabit && (fiyat !== it.fiyat || para !== it.para)) { deger.fiyat = fiyat; deger.para = para; } if (!satista) deger.satista = false;
    const bos = !Object.keys(deger).length;
    const r = bos ? await deGeriAl('magaza', jp('urunler', it.lootId)) : await deYama('magaza', jp('urunler', it.lootId), deger, { ms: 0 });
    if (r) { it.dunya = bos ? null : deger; yenile(); m.close(); }
  };
  const seg = h('div', { class: 'seg' }, [['C', N('Kredi')], ['U', N('Uridyum')]].map(([k, ad]) => h('button', { class: para === k ? 'on info' : '', disabled: sabit,
    onclick: e => { para = k; seg.querySelectorAll('button').forEach(x => x.classList.toggle('on', x === e.currentTarget)); seg.querySelectorAll('button').forEach(x => x.classList.toggle('info', x === e.currentTarget)); } }, T(ad))));
  const m = modal({ title: esyaAdi(it.lootId), sub: it.lootId, body: h('div', { class: 'stack', style: { gap: '14px' } },
    h('div', { class: 'row', style: { gap: '14px' } }, oyunIkon(it.lootId, 72, null, 'cart'), h('div', { class: 'small muted' }, T('Standart fiyat: {0}', fmtN(it.fiyat) + (it.para === 'C' ? ' C.' : ' U.')))),
    sabit ? h('div', { class: 'alert bilgi' }, icon('info'), h('div', null, T('Bu ürünün fiyatı kendi kuralıyla hesaplanır (dron sayısı, P.E.T. seviyesi); yalnız satıştan kaldırabilirsin.'))) : null,
    h('div', { class: 'de-alan-satir' }, h('label', null, T('Fiyat')), deSayi(fiyat, v => { fiyat = v; }, { min: 0, max: 1e10, adim: para === 'C' ? 1000 : 10, gen: 130 }), seg),
    h('div', { class: 'de-alan-satir' }, h('label', null, T('Satışta')), h('label', { class: 'switch' }, h('input', { type: 'checkbox', checked: satista, onchange: e => { satista = e.target.checked; } }), h('span')),
      h('span', { class: 'small muted' }, T('Kapalıysa mağazada görünmez, satın alınamaz.')))),
    foot: [it.dunya ? btn(T('Standarda döndür'), async () => { if (await deGeriAl('magaza', jp('urunler', it.lootId))) { it.dunya = null; yenile(); m.close(); } }, 'ghost', 'undo') : null,
      h('span', { class: 'spacer' }), btn(T('Vazgeç'), () => m.close(), 'ghost'), btn(T('Kaydet'), kaydet, 'primary', 'check')] });
}

function topluFiyat(urunler, yenile) {
  let yuzde = 100;
  const m = modal({ title: T('Toplu fiyat'), sub: T('Bu kategorideki ürünlerin fiyatını standart fiyatın yüzdesine çeker.'), body: h('div', { class: 'stack', style: { gap: '12px' } },
    h('div', { class: 'de-alan-satir' }, h('label', null, T('Standart fiyatın')), deSayi(yuzde, v => { yuzde = v; }, { min: 0, max: 1000, adim: 10, gen: 70 }), h('span', null, '%')),
    h('div', { class: 'chips' }, [25, 50, 75, 150, 200].map(p => h('button', { type: 'button', class: 'chip link', onclick: e => { yuzde = p; e.currentTarget.closest('.body').querySelector('input').value = p; } }, '%' + p)))),
    foot: [btn(T('Vazgeç'), () => m.close(), 'ghost'), btn(T('Uygula'), async () => {
      m.close(); const l = urunler.filter(it => !it.sabit && it.dunya?.satista !== false);
      for (const it of l) {
        const deger = { fiyat: Math.round(it.fiyat * yuzde / 100), para: it.para };
        const r = yuzde === 100 ? await deGeriAl('magaza', jp('urunler', it.lootId)) : await act(() => api('/api/dunya/yama', { dunya: DE.did, dosya: 'magaza', yol: jp('urunler', it.lootId), deger }));
        if (r) { it.dunya = yuzde === 100 ? null : deger; DE.ozet = Object.assign(DE.ozet, r); }
      }
      deMenuSay(); deUyari(); deKayitDurumu('kaydedildi'); toast(T('{0} ürünün fiyatı güncellendi.', l.length), 'ok'); yenile();
    }, 'primary', 'check')] });
}

// ================================================================== AÇIK ARTIRMA
const DE_MZ_TUR = [['hour', N('Saatlik')], ['day', N('Günlük')], ['week', N('Haftalık')]];
async function deMuzayede(alan, b) {
  const r = await act(() => api('/api/dunya/bolum?bolum=muzayede&dunya=' + encodeURIComponent(DE.did))); if (!r || DE.bolum !== 'muzayede') return;
  const lotlar = r.lotlar;
  const kaydet = () => deYama('sosyal.json', jp('muzayede', 'lotlar'), lotlar.map(l => [l.loot, l.grup, l.tur, l.adet, l.anlik, l.fiyat]));
  const grupOf = loot => loot.startsWith('ammunition_laser') ? 'battery' : loot.startsWith('ammunition_rocket') ? 'rocket' : loot.startsWith('ship_') ? 'ship'
    : loot.startsWith('drone_') ? 'drone' : loot.startsWith('equipment_') ? 'equipment' : loot.startsWith('booster_') ? 'booster' : 'other';
  const f = DE.sec.mz || (DE.sec.mz = { tur: 'hour', q: '' });
  const kolonlar = h('div', { class: 'stack', style: { gap: '10px' } });
  const ciz = () => {
    const s = f.q.trim().toLowerCase(), ls = lotlar.filter(l => l.tur === f.tur && (!s || esyaAdi(l.loot).toLowerCase().includes(s)));
    const sekme = h('div', { class: 'seg' }, DE_MZ_TUR.map(([tur, ad]) => h('button', { class: f.tur === tur ? 'on info' : '', onclick: () => { f.tur = tur; ciz(); } },
      T(ad), ' ', h('span', { class: 'de-say mavi' }, lotlar.filter(l => l.tur === tur).length))));
    const ekle = btn(T('Lot ekle'), async () => {
      const loot = await esyaSec(T('Lot ekle: {0}', T(DE_MZ_TUR.find(x => x[0] === f.tur)[1]))); if (!loot) return;
      if (lotlar.some(l => l.tur === f.tur && l.loot === loot)) return toast(T('Bu eşya bu dönemde zaten var.'), 'info');
      lotlar.push({ loot, grup: grupOf(loot), tur: f.tur, adet: 1, anlik: true, fiyat: 1000 }); kaydet(); ciz(); }, 'sm primary', 'plus');
    doldur(kolonlar, h('div', { class: 'row wrap', style: { gap: '10px' } }, sekme,
      h('input', { class: 'input', style: { width: '180px' }, placeholder: T('Ara…'), value: f.q, oninput: e => { f.q = e.target.value; ciz(); setTimeout(() => kolonlar.querySelector('input.input')?.focus(), 0); } }),
      h('span', { class: 'spacer' }), ekle),
      h('div', { class: 'de-lot-bas small muted' }, h('span'), h('span', null, T('Eşya')), h('span', null, T('Adet')), h('span', null, T('Anında alım')), h('span', null, T('Fiyat (U.)')), h('span')),
      ls.length ? h('div', { class: 'de-lotlar' }, ls.map(l => h('div', { class: 'de-lot' }, oyunIkon(l.loot, 34, null, 'gavel'),
        h('div', { class: 'de-lot-ad', title: l.loot }, esyaAdi(l.loot)),
        deSayi(l.adet, v => { l.adet = Math.max(1, v); kaydet(); }, { min: 1, max: 1e7, gen: 76 }),
        h('label', { class: 'switch' }, h('input', { type: 'checkbox', checked: l.anlik, onchange: e => { l.anlik = e.target.checked; kaydet(); ciz(); } }), h('span')),
        l.anlik ? deSayi(l.fiyat, v => { l.fiyat = v; kaydet(); }, { min: 0, max: 1e9, adim: 100, gen: 86 }) : h('span', { class: 'small dim' }, T('yalnız teklif')),
        btn('', () => { lotlar.splice(lotlar.indexOf(l), 1); kaydet(); ciz(); }, 'sm ghost icon', 'x', { title: T('Lotu kaldır') }))))
        : h('div', { class: 'empty small muted' }, T('Bu dönemde lot yok.')));
  };
  doldur(alan, h('div', { class: 'card' }, deBaslik(b, r.degisti ? btn(T('Standarda döndür'), async () => {
    if (await confirmBox(T('Açık artırma standarda dönsün mü?'), T('Lot listesi oyunun kendi {0} lotuna döner.', r.standart_sayisi), { ok: T('Standarda döndür'), danger: true }))
      if (await deGeriAl('sosyal.json', jp('muzayede', 'lotlar'))) deBolumCiz(); }, 'sm ghost', 'undo') : null),
    h('p', { class: 'small muted', style: { margin: '10px 0 14px' } }, T('Teklifler kredi ile verilir; anında alım uridyumla. Lotlar her dönem (saatin 30. dakikası, 22:30 UTC, pazar 22:30 UTC) yenilenir.')),
    kolonlar));
  ciz();
}

// ---- harita paneli: cevherler (esyalar.json cevherler.haritalar: haritanın adıyla, yoksa harita sınıfınınki)
function cevherBlogu(hm, isaretle) {
  const c = hm.cevher, adet = Object.assign({}, c.adet), kutu = h('div', { class: 'stack', style: { gap: '6px' } });
  const kaydet = () => { c.ozel = true; deYama('esyalar.json', c.yol, adet); isaretle(); ciz(); };
  const ciz = () => {
    const var_ = Object.keys(c.turler).filter(t => adet[t] > 0);
    doldur(kutu, 
      h('div', { class: 'small muted' }, c.ozel ? T('Bu haritaya özel.') : T('{0} sınıfının değerleri (aynı sınıftaki bütün haritalar). Değiştirince yalnız bu haritaya özel olur.', c.sinif)),
      ...var_.map(t => h('div', { class: 'de-cevher' }, oyunIkon(c.turler[t], 24, null, 'box'), h('span', { class: 'small ellipsis' }, esyaAdi(c.turler[t])),
        deSayi(adet[t], v => { adet[t] = v; kaydet(); }, { max: 1000, adim: 5, gen: 52 }))),
      !var_.length ? h('div', { class: 'small dim' }, T('Bu haritada cevher yok.')) : null,
      h('div', { class: 'row wrap', style: { gap: '6px' } },
        btn(T('Cevher ekle'), ev => popMenu(ev.currentTarget, Object.keys(c.turler).filter(t => !(adet[t] > 0)).map(t => ({ label: esyaAdi(c.turler[t]), ic: 'plus',
          fn: () => { adet[t] = 20; kaydet(); } }))), 'sm', 'plus'),
        c.ozel ? btn(T('Sınıfın değerine döndür'), async () => { if (await deGeriAl('esyalar.json', c.yol)) deBolumCiz(); }, 'sm ghost', 'undo') : null),
      h('div', { class: 'de-alan-satir' }, h('label', null, T('Yeniden doğma')), deSayi(c.yeniden_sn[0], v => { c.yeniden_sn[0] = v; yenilenme(); }, { min: 1, max: 3600, gen: 46 }),
        h('span', { class: 'small muted' }, '–'), deSayi(c.yeniden_sn[1], v => { c.yeniden_sn[1] = v; yenilenme(); }, { min: 1, max: 3600, gen: 46 }), h('span', { class: 'small muted' }, T('sn'))),
      h('div', { class: 'small dim' }, T('Yeniden doğma süresi bütün haritalarda geçerli.')));
  };
  const yenilenme = () => deYama('esyalar.json', jp('cevherler', 'yeniden_dogma_sn'), [Math.min(...c.yeniden_sn), Math.max(...c.yeniden_sn)]);
  ciz();
  return h('div', { class: 'stack', style: { gap: '8px' } }, h('div', { class: 'de-ara-baslik' }, T('Cevherler')), kutu);
}

// ================================================================== KUTULAR VE GANİMET
const SINIF_ADI = { 'X-1..X-8': N('Firma haritaları (X-1 – X-8)'), 'X-2..X-8': N('Firma haritaları (X-2 – X-8)'), '4-X': N('Savaş haritaları (4-X)'),
  '5-X': N('Korsan haritaları (5-1 – 5-3)'), '5-4': '5-4', 'BL': 'Black Light' };
// kutunun oyundaki görseli (atlas), yoksa anahtarının simgesi
const KUTU_SPRITE = { PIRATE_BOOTY: 'booty_box_green', PIRATE_BOOTY_GOLD: 'booty_box_gold', PIRATE_BOOTY_RED: 'booty_box_red', PIRATE_BOOTY_BLUE: 'booty_box_blue',
  PIRATE_BOOTY_SILVER: 'booty_box_silver', BLACK_BOOTY_BOX: 'blackBooty_100x100', MASQUE_BOOTY_BOX: 'masqueBooty_100x100' };
const kutuIkon = (k, boy) => OG.dizin?.sprite[KUTU_SPRITE[k.tur]] ? sprite(KUTU_SPRITE[k.tur], boy) : oyunIkon(k.anahtar, boy, null, 'gift');

async function deKutular(alan, b) {
  const r = await act(() => api('/api/dunya/bolum?bolum=kutular&dunya=' + encodeURIComponent(DE.did))); if (!r || DE.bolum !== 'kutular') return;
  const f = DE.sec.kt || (DE.sec.kt = { secili: 'bonus' });
  const liste = h('div', { class: 'de-npc-liste' }), detay = h('div', { class: 'de-detay' });
  const ogeler = [{ id: 'bonus', ad: T('Bonus kutusu'), alt: T('Bütün haritalarda (4-X hariç)'), ikon: 'bonus_box', degisti: r.bonus_degisti },
    { id: 'bonus_4x', ad: T('Zengin bonus kutusu'), alt: T('Savaş haritalarında (4-X)'), ikon: 'bonus_box_green', degisti: r.bonus_4x_degisti },
    ...r.kutular.map(k => ({ id: k.tur, ad: k.ad, alt: !k.yerde ? T('Haritalarda doğmaz') : k.takvim ? T('Etkinlikte') : T('Her zaman'), kutu: k, degisti: k.degisti }))];
  const ciz = () => {
    doldur(liste, ...ogeler.map(o => h('button', { type: 'button', class: 'de-npc' + (f.secili === o.id ? ' on' : '') + (o.degisti ? ' degisti' : ''),
      onclick: () => { f.secili = o.id; ciz(); } }, o.kutu ? kutuIkon(o.kutu, 36) : (OG.dizin?.sprite[o.ikon] ? sprite(o.ikon, 36) : icon('gift')),
      h('div', { class: 'de-npc-ad' }, h('b', null, o.ad), h('div', { class: 'small muted' }, o.alt)))));
    const o = ogeler.find(x => x.id === f.secili) || ogeler[0];
    doldur(detay, o.kutu ? kutuDetay(o, r) : bonusDetay(o, r));
  };
  doldur(alan, h('div', { class: 'card' }, deBaslik(b), h('div', { class: 'de-iki dar-liste' }, liste, detay)));
  ciz();
}

function bonusDetay(o, r) {
  const yol = jp(o.id === 'bonus' ? 'bonus_kutu' : 'bonus_kutu_4x'), rows = r[o.id].map(x => x.slice());
  const kutu = h('div', { class: 'stack', style: { gap: '6px' } });
  const kaydet = () => { o.degisti = true; deYama('npc.json', yol, rows); };
  const ciz = () => doldur(kutu, ...rows.map((x, i) => h('div', { class: 'de-kutu-satir' }, oyunIkon(x[0], 32, null, 'gift'),
    h('div', { class: 'de-kutu-govde' }, h('span', { class: 'de-kutu-ad', title: x[0] }, esyaAdi(x[0])),
      h('div', { class: 'de-kutu-kontrol' }, h('span', { class: 'small muted' }, T('Adet')), deSayi(x[1], v => { x[1] = Math.max(1, v); kaydet(); }, { min: 1, max: 1e7, gen: 70 }),
        h('span', { class: 'de-yuzde' }, '%' + (100 / rows.length).toFixed(1)))),
    btn('', () => { if (rows.length < 2) return toast(T('Bonus kutusunda en az bir ödül olmalı.'), 'info'); rows.splice(i, 1); kaydet(); ciz(); }, 'sm ghost icon', 'x'))),
    h('button', { type: 'button', class: 'de-odul-ekle', onclick: async () => { const l = await esyaSec(T('Ödül ekle')); if (!l) return; rows.push([l, l.startsWith('ammunition_') ? 100 : 1]); kaydet(); ciz(); } },
      icon('plus'), T('Ödül ekle')));
  ciz();
  return h('div', { class: 'stack', style: { gap: '12px' } },
    h('div', { class: 'de-detay-bas' }, OG.dizin?.sprite[o.ikon] ? sprite(o.ikon, 56) : icon('gift'), h('div', null, h('div', { class: 'de-h3' }, o.ad), h('div', { class: 'small muted' }, o.alt))),
    h('p', { class: 'small muted', style: { margin: 0 } }, T('Kutu toplanınca satırlardan biri eşit şansla düşer. Haritadaki kutu sayısı Haritalar bölümünde.')),
    kutu,
    o.degisti ? btn(T('Standarda döndür'), async () => { if (await deGeriAl('npc.json', yol)) deBolumCiz(); }, 'sm ghost', 'undo') : null);
}

function kutuDetay(o, r) {
  const k = JSON.parse(JSON.stringify(o.kutu)), yol = jp('kutular', k.tur);
  const kaydet = () => { o.degisti = true; deYama('kutular.json', yol, { adet: k.adet, yeniden_sn: k.yeniden_sn, haritalar: k.haritalar, odul: k.odul }); };
  const tablo = h('div', { class: 'stack', style: { gap: '6px' } });
  const yuzde = w => { const t = k.odul.reduce((a, x) => a + (+x[2] || 0), 0); return t ? (100 * w / t).toFixed(w * 100 / t < 1 ? 2 : 1) : '0'; };
  const ciz = () => doldur(tablo, ...k.odul.map((x, i) => {
    const paket = x[0] === 'paket';
    const agirlik = h('input', { class: 'input num de-agirlik', type: 'number', min: 0, step: 'any', value: x[2], title: T('Ağırlık'),
      onchange: e => { x[2] = Math.max(0, +e.target.value || 0); kaydet(); ciz(); } });
    return h('div', { class: 'de-kutu-satir' }, paket ? h('span', { class: 'de-paket' }, x[1].slice(0, 4).map(([l]) => oyunIkon(l, 16, null, 'gift'))) : oyunIkon(x[0], 32, null, 'gift'),
      h('div', { class: 'de-kutu-govde' }, h('span', { class: 'de-kutu-ad', title: paket ? x[1].map(([l, n]) => n + ' × ' + l).join('\n') : x[0] }, paket ? T('Paket ({0} eşya)', x[1].length) : esyaAdi(x[0])),
        h('div', { class: 'de-kutu-kontrol' },
          paket ? null : h('span', { class: 'small muted' }, T('Adet')),
          paket ? null : Array.isArray(x[1]) ? [deSayi(x[1][0], v => { x[1][0] = Math.max(1, v); kaydet(); }, { min: 1, max: 1e7, gen: 52 }), '–',
            deSayi(x[1][1], v => { x[1][1] = Math.max(1, v); kaydet(); }, { min: 1, max: 1e7, gen: 52 })]
            : deSayi(x[1], v => { x[1] = Math.max(1, v); kaydet(); }, { min: 1, max: 1e7, gen: 70 }),
          h('span', { class: 'small muted' }, T('Ağırlık')), agirlik, h('span', { class: 'de-yuzde' }, '%' + yuzde(+x[2] || 0)))),
      btn('', () => { if (k.odul.length < 2) return toast(T('Kutuda en az bir ödül olmalı.'), 'info'); k.odul.splice(i, 1); kaydet(); ciz(); }, 'sm ghost icon', 'x'));
  }), h('button', { type: 'button', class: 'de-odul-ekle', onclick: async () => {
    const l = await esyaSec(T('Ödül ekle')); if (!l) return; k.odul.push([l, 1, 5]); kaydet(); ciz(); } }, icon('plus'), T('Ödül ekle')));
  ciz();
  const siniflar = h('div', { class: 'chips' });
  const cizSinif = () => doldur(siniflar, ...r.siniflar.map(s => h('button', { type: 'button', class: 'chip link de-sinif' + (k.haritalar.includes(s) ? ' on' : ''),
    onclick: () => { k.haritalar = k.haritalar.includes(s) ? k.haritalar.filter(x => x !== s) : [...k.haritalar, s]; kaydet(); cizSinif(); } },
    k.haritalar.includes(s) ? icon('check') : icon('plus'), SINIF_ADI[s] ? T(SINIF_ADI[s]) : s)));
  cizSinif();
  return h('div', { class: 'stack', style: { gap: '12px' } },
    h('div', { class: 'de-detay-bas' }, kutuIkon(k, 56), h('div', null, h('div', { class: 'de-h3' }, k.ad),
      h('div', { class: 'small muted' }, T('Açmak için: {0}', esyaAdi(k.anahtar)), k.takvim ? ' · ' + T('yalnız etkinliği sürerken doğar') : ''))),
    h('div', { class: 'de-alan-satir' }, h('label', null, T('Haritada adet')), deSayi(k.adet, v => { k.adet = v; kaydet(); }, { min: 0, max: 100, gen: 56 }),
      h('span', { class: 'small muted' }, T('her haritada aynı anda'))),
    k.yeniden_sn ? h('div', { class: 'de-alan-satir' }, h('label', null, T('Yeniden doğma')),
      deSayi(k.yeniden_sn[0], v => { k.yeniden_sn[0] = v; kaydet(); }, { min: 10, max: 86400, adim: 30, gen: 64 }), '–',
      deSayi(k.yeniden_sn[1], v => { k.yeniden_sn[1] = v; kaydet(); }, { min: 10, max: 86400, adim: 30, gen: 64 }), h('span', { class: 'small muted' }, T('sn'))) : null,
    h('div', { class: 'de-ara-baslik' }, T('Doğduğu haritalar')), siniflar,
    h('div', { class: 'de-ara-baslik' }, T('Ödül tablosu')),
    h('p', { class: 'small muted', style: { margin: 0 } }, T('Açılınca bir satır ağırlığına göre çekilir: ağırlık / toplam ağırlık = şans.')),
    tablo,
    o.degisti ? btn(T('Standarda döndür'), async () => { if (await deGeriAl('kutular.json', yol)) deBolumCiz(); }, 'sm ghost', 'undo') : null);
}

// ================================================================== GALAKSİ KAPILARI
const KAPI_ODUL_ALAN = [['ep', N('Deneyim'), 'kaynak_deneyim'], ['onur', N('Onur'), 'kaynak_onur'], ['uridyum', N('Uridyum'), 'kaynak_uridyum'],
  ['xenomit', N('Xenomit'), 'resource_ore_xenomit'], ['log_disk', N('Seyir diski'), 'resource_logfile'], ['kupon', N('Kupon'), '']];
const ROMEN = n => ['I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII', 'IX', 'X', 'XI', 'XII', 'XIII', 'XIV', 'XV'][n] || String(n + 1);

async function deKapilar(alan, b) {
  const r = await act(() => api('/api/dunya/bolum?bolum=kapilar&dunya=' + encodeURIComponent(DE.did))); if (!r || DE.bolum !== 'kapilar') return;
  const f = DE.sec.kp || (DE.sec.kp = { secili: r.kapilar[0]?.key, acik: {} });
  const liste = h('div', { class: 'de-npc-liste' }), detay = h('div', { class: 'de-detay' });
  const ciz = () => {
    doldur(liste, ...r.kapilar.map(g => h('button', { type: 'button', class: 'de-npc' + (f.secili === g.key ? ' on' : '') + (g.degisti ? ' degisti' : ''),
      onclick: () => { f.secili = g.key; ciz(); } }, art('ed_kapilar', 'de-kapi-ikon'),
      h('div', { class: 'de-npc-ad' }, h('b', null, g.ad), h('div', { class: 'small muted' }, T('{0} dalga · {1} parça', g.dalgalar.length, g.parca))))));
    const g = r.kapilar.find(x => x.key === f.secili) || r.kapilar[0];
    doldur(detay, kapiDetay(g, f));
  };
  doldur(alan, h('div', { class: 'card' }, deBaslik(b), h('div', { class: 'de-iki dar-liste' }, liste, detay)));
  ciz();
}

function kapiDetay(g, f) {
  const yol = jp('kapilar', g.key), std = g.standart;
  const kaydet = () => {
    g.degisti = true;
    return deYama('kapilar.json', yol, { parca: g.parca, can: g.can, odul: Object.assign({}, g.odul, { cephane: g.cephane, sans: g.sans.map(x => ({ adet: x.adet, olasilik: x.olasilik })) }),
      dalgalar: g.dalgalar.map(w => ({ uzaylilar: w.uzaylilar.map(a => ({ tur: a.tur, adet: a.adet, hp: a.hp, kalkan: a.kalkan, hasar: a.hasar, hiz: a.hiz })) })) });
  };
  const satir = (ad, k, opts) => h('div', { class: 'de-alan-satir' + (std && std[k] !== g[k] ? ' degisti' : '') }, h('label', null, ad),
    deSayi(g[k], v => { g[k] = v; kaydet(); }, opts), std ? deStd(std[k], g[k], () => { g[k] = std[k]; kaydet(); deBolumCiz(); }) : null);
  const cephane = h('div', { class: 'de-oduller' });
  const cizCephane = () => doldur(cephane, ...Object.entries(g.cephane).map(([l, n]) => h('div', { class: 'de-odul-cip' }, oyunIkon(l, 32, null, 'gift'),
    h('div', { class: 'de-odul-cip-ad' }, h('div', { class: 'small ellipsis' }, esyaAdi(l)), deSayi(n, v => { g.cephane[l] = Math.max(1, v); kaydet(); }, { min: 1, max: 1e8, adim: 100, gen: 80 })),
    btn('', () => { delete g.cephane[l]; kaydet(); cizCephane(); }, 'sm ghost icon', 'x'))),
    h('button', { type: 'button', class: 'de-odul-ekle', onclick: async () => { const l = await esyaSec(T('Ödül ekle')); if (!l) return; g.cephane[l] = (g.cephane[l] || 0) + 1000; kaydet(); cizCephane(); } },
      icon('plus'), T('Ödül ekle')));
  cizCephane();
  const dalga = (w, n) => {
    const acik = !!f.acik[g.key + n], toplam = w.uzaylilar.reduce((a, x) => a + x.adet, 0);
    const deger = (ad, v, cb, opts) => h('label', { class: 'de-dalga-deger' }, h('span', null, ad), deSayi(v, cb, opts));
    const govde = acik ? h('div', { class: 'de-dalga-govde' }, w.uzaylilar.map(a => h('div', { class: 'de-dalga-satir' }, npcIkon(a, 30),
      h('div', { class: 'de-kutu-govde' }, h('div', { class: 'de-npc-ad' }, h('b', null, npcAdi(a)), a.kalici ? badge(T('Patron'), 'orange') : null,
          a.degisti_tur ? badge(T('Değiştirildi'), 'orange') : null, h('span', { class: 'spacer' }),
          a.sabit ? null : btn(T('Değiştir'), async () => {
            const u = await uzayliSec(T('Bu dalgada hangi uzaylı olsun?'), { sayisal: true }); if (!u) return;
            Object.assign(a, { tur: u.tip, ad: u.ad, ikon: u.ikon, hp: u.hp, kalkan: u.kalkan, hasar: u.hasar, hiz: u.hiz, degisti_tur: true });
            await kaydet(); deBolumCiz(); }, 'sm ghost', 'refresh', { title: T('Uzaylıyı başka türle değiştir (adet ve yer aynı kalır)') })),
        h('div', { class: 'de-kutu-kontrol' },
          deger(T('Adet'), a.adet, v => { a.adet = Math.max(a.en_az, v); kaydet(); ozet.textContent = T('{0} uzaylı', fmtN(w.uzaylilar.reduce((t, x) => t + x.adet, 0))); }, { min: a.en_az, max: 5000, gen: 46 }),
          deger(T('Can'), a.hp, v => { a.hp = v; kaydet(); }, { max: 50000000, adim: 1000, gen: 80 }),
          deger(T('Kalkan'), a.kalkan, v => { a.kalkan = v; kaydet(); }, { max: 50000000, adim: 1000, gen: 80 }),
          deger(T('Hasar'), a.hasar, v => { a.hasar = v; kaydet(); }, { max: 1000000, adim: 50, gen: 62 })))))) : null;
    const ozet = h('span', { class: 'small muted' }, T('{0} uzaylı', fmtN(toplam)));
    return h('div', { class: 'de-dalga' + (acik ? ' acik' : '') }, h('button', { type: 'button', class: 'de-dalga-baslik', onclick: () => { f.acik[g.key + n] = !acik; deBolumCiz(); } },
      icon(acik ? 'chevR' : 'chevR'), h('b', null, T('Dalga {0}', ROMEN(n))), h('span', { class: 'de-dalga-ikonlar' }, w.uzaylilar.slice(0, 6).map(a => npcIkon(a, 22))), h('span', { class: 'spacer' }), ozet), govde);
  };
  return h('div', { class: 'stack', style: { gap: '12px' } },
    h('div', { class: 'de-detay-bas' }, art('ed_kapilar', 'de-kapi-ikon buyuk'), h('div', null, h('div', { class: 'de-h3' }, g.ad), h('div', { class: 'small muted' }, T('{0} dalga', g.dalgalar.length)))),
    satir(T('Gereken parça'), 'parca', { min: 1, max: 10000, gen: 64 }), satir(T('Can'), 'can', { min: 1, max: 100, gen: 50 }),
    h('div', { class: 'de-ara-baslik' }, T('Kapı ödülü')),
    h('div', { class: 'de-odul-izgara' }, KAPI_ODUL_ALAN.filter(([k]) => k in g.odul).map(([k, ad, gor]) => h('div', { class: 'de-odul' + (std && std.odul[k] !== g.odul[k] ? ' degisti' : '') },
      gor.startsWith('kaynak_') ? art(gor, 'de-odul-ikon') : oyunIkon(gor || null, 30, null, 'gift'), h('div', null, h('div', { class: 'small muted' }, T(ad)),
        deSayi(g.odul[k] || 0, v => { g.odul[k] = v; kaydet(); }, { max: 1e10, adim: k === 'ep' ? 10000 : k === 'onur' ? 1000 : 10, gen: 92 }))))),
    h('div', { class: 'de-ara-baslik' }, T('Cephane ve eşya ödülü')), cephane,
    g.sans.length ? [h('div', { class: 'de-ara-baslik' }, T('Şanslı ödüller')), h('div', { class: 'stack', style: { gap: '6px' } }, g.sans.map(x => h('div', { class: 'de-kutu-satir' },
      x.paket ? icon('gift') : oyunIkon(x.esya, 32, null, 'gift'), h('div', { class: 'de-kutu-govde' }, h('span', { class: 'de-kutu-ad' }, x.paket ? T('Cevher paketi') : esyaAdi(x.esya)),
        h('div', { class: 'de-kutu-kontrol' },
          typeof x.adet === 'number' && !x.paket ? [h('span', { class: 'small muted' }, T('Adet')), deSayi(x.adet, v => { x.adet = Math.max(1, v); kaydet(); }, { min: 1, max: 1e7, gen: 60 })] : null,
          h('span', { class: 'small muted' }, T('Şans')), h('input', { class: 'input num de-agirlik', type: 'number', min: 0, max: 100, step: 'any', value: +(x.olasilik * 100).toFixed(3),
            onchange: e => { x.olasilik = Math.max(0, Math.min(100, +e.target.value || 0)) / 100; kaydet(); } }), h('span', { class: 'de-yuzde' }, '%'))), h('span'))))] : null,
    h('div', { class: 'de-ara-baslik' }, T('Dalgalar')),
    h('p', { class: 'small muted', style: { margin: 0 } }, T('Adet değişince dalganın alt grupları orantılı bölünür. Oyun Ayarları\'ndaki dalga uzaylı çarpanı bunun üstüne uygulanır.')),
    h('div', { class: 'stack', style: { gap: '6px' } }, g.dalgalar.map(dalga)),
    g.degisti ? btn(T('Kapıyı standarda döndür'), async () => { if (await deGeriAl('kapilar.json', yol)) deBolumCiz(); }, 'sm ghost', 'undo') : null);
}

// ================================================================== ETKİNLİKLER
const ETK_FILTRE = [['harita', N('Harita etkinlikleri')], ['yillik', N('Yıllık')], ['haftalik', N('Haftalık')], ['degisti', N('Değiştirilenler')]];
const ETK_DURUM = [['takvim', N('Takvime göre'), 'info'], ['acik', N('Hep açık'), 'ok'], ['kapali', N('Kapalı'), 'err']];
const bugun = (gun = 0) => new Date(Date.now() + gun * 86400000).toISOString().slice(0, 10);

async function deEtkinlikler(alan, b) {
  await uzayliListesi();
  const r = await act(() => api('/api/dunya/bolum?bolum=etkinlikler&dunya=' + encodeURIComponent(DE.did))); if (!r || DE.bolum !== 'etkinlikler') return;
  const f = DE.sec.et || (DE.sec.et = { filtre: 'harita', q: '', secili: null, gecmis: false });
  const liste = h('div', { class: 'de-npc-liste' }), detay = h('div', { class: 'de-detay' });
  const ciz = () => {
    const s = f.q.trim().toLowerCase();
    const l = r.etkinlikler.filter(e => (f.filtre === 'degisti' ? e.degisti : e.tur === f.filtre) && (!s || e.ad.toLowerCase().includes(s)));
    doldur(liste, ...l.map(e => h('button', { type: 'button', class: 'de-npc' + (f.secili === e.key ? ' on' : '') + (e.degisti ? ' degisti' : ''),
      onclick: () => { f.secili = e.key; ciz(); } }, e.harita?.uzaylilar[0] ? npcIkon(e.harita.uzaylilar[0], 34) : deIkon('etkinlikler', 'de-kapi-ikon'),
      h('div', { class: 'de-npc-ad' }, h('b', null, e.ad), h('div', { class: 'small muted' },
        e.dunya_durum === 'acik' ? T('Bu dünyada hep açık') : e.dunya_durum === 'kapali' ? T('Bu dünyada kapalı') : T('Takvime göre')))) ),
      !l.length ? h('div', { class: 'empty small muted' }, T('Eşleşen etkinlik yok.')) : null);
    const e = r.etkinlikler.find(x => x.key === f.secili) || l[0];
    if (e && !f.secili) f.secili = e.key;
    doldur(detay, e ? etkinlikDetay(e, r, f) : h('div', { class: 'empty muted' }, T('Soldan bir etkinlik seç.')));
  };
  const seg = h('div', { class: 'seg' }, ETK_FILTRE.map(([k, ad]) => h('button', { class: f.filtre === k ? 'on info' : '', onclick: () => { f.filtre = k; f.secili = null; deBolumCiz(); } }, T(ad))));
  doldur(alan, h('div', { class: 'card' }, deBaslik(b, h('input', { class: 'input', style: { width: '180px' }, placeholder: T('Etkinlik ara…'), value: f.q, oninput: e => { f.q = e.target.value; ciz(); } }), seg),
    h('p', { class: 'small muted', style: { margin: '10px 0 0' } }, T('Kaydın Etkinlikler sayfasında elle açtığın ya da kapattığın etkinlik, dünyanın ayarından önce gelir.')),
    h('div', { class: 'de-iki dar-liste' }, liste, detay)));
  ciz();
}

function etkinlikDetay(e, r, f) {
  const yol = jp('etkinlikler', e.key);
  const kaydet = () => { e.degisti = true; deYama('etkinlikler.json', yol, { dunya_durum: e.dunya_durum, donemler: e.donemler || undefined,
    harita: e.harita ? { haritalar: e.harita.haritalar, uzaylilar: e.harita.uzaylilar.map(a => ({ adet: a.adet })), kota: e.harita.kota, patron: e.harita.patron } : undefined }); };
  const durum = h('div', { class: 'seg' }, ETK_DURUM.map(([k, ad, c]) => h('button', { class: e.dunya_durum === k ? 'on ' + c : '',
    onclick: () => { e.dunya_durum = k; kaydet(); deBolumCiz(); } }, T(ad))));
  const out = [h('div', { class: 'de-detay-bas' }, e.harita?.uzaylilar[0] ? npcIkon(e.harita.uzaylilar[0], 56) : deIkon('etkinlikler', 'de-kapi-ikon buyuk'),
    h('div', null, h('div', { class: 'de-h3' }, e.ad), h('div', { class: 'small muted' }, { harita: T('Harita etkinliği'), yillik: T('Yıllık etkinlik'), haftalik: T('Haftalık etkinlik') }[e.tur]))),
    h('div', { class: 'de-alan-satir' }, h('label', null, T('Bu dünyada')), durum)];
  if (e.donemler) {
    const kutu = h('div', { class: 'stack', style: { gap: '6px' } });
    const cizD = () => {
      const bugunu = bugun();
      const satirlar = e.donemler.map((d, i) => [d, i]).filter(([d]) => f.gecmis || d[0].length === 5 || d[1] >= bugunu);
      doldur(kutu, ...satirlar.map(([d, i]) => {
        const yillik = d[0].length === 5;
        const giris = (j) => h('input', { class: 'input de-tarih', type: yillik ? 'text' : 'date', value: d[j], placeholder: yillik ? T('AA-GG') : null,
          onchange: ev => { d[j] = ev.target.value; kaydet(); } });
        return h('div', { class: 'de-donem' + (!yillik && d[1] < bugunu ? ' gecmis' : '') + (!yillik && d[0] <= bugunu && bugunu <= d[1] ? ' simdi' : '') },
          giris(0), h('span', { class: 'muted' }, '–'), giris(1), yillik ? badge(T('Her yıl'), 'info') : null,
          !yillik && d[0] <= bugunu && bugunu <= d[1] ? badge(T('Şu an'), 'ok') : null, h('span', { class: 'spacer' }),
          btn('', () => { e.donemler.splice(i, 1); kaydet(); cizD(); }, 'sm ghost icon', 'x', { title: T('Dönemi sil') }));
      }), !satirlar.length ? h('div', { class: 'small dim' }, T('Gelecekte dönem yok.')) : null,
      h('div', { class: 'row wrap', style: { gap: '6px' } },
        btn(T('Dönem ekle'), () => { e.donemler.push([bugun(), bugun(7)]); kaydet(); cizD(); }, 'sm', 'plus'),
        btn(T('Her yıl tekrarlanan dönem'), () => { const d = bugun().slice(5); e.donemler.push([d, bugun(7).slice(5)]); kaydet(); cizD(); }, 'sm ghost', 'refresh'),
        h('label', { class: 'row small muted', style: { gap: '6px', cursor: 'pointer' } }, h('input', { type: 'checkbox', checked: f.gecmis, onchange: ev => { f.gecmis = ev.target.checked; cizD(); } }),
          T('Geçmiş dönemleri göster'))));
    };
    cizD();
    out.push(h('div', { class: 'de-ara-baslik' }, T('Dönemler')), h('p', { class: 'small muted', style: { margin: 0 } }, T('Etkinlik bu tarihler arasında açılır (bitiş günü dahil). "Her yıl" dönemleri her yıl aynı günlerde tekrar eder.')), kutu);
  } else if (e.gunler || e.saatler) {
    const GUN = [N('Pzt'), N('Sal'), N('Çar'), N('Per'), N('Cum'), N('Cmt'), N('Paz')];
    out.push(h('div', { class: 'de-ara-baslik' }, T('Haftalık düzen')), h('div', { class: 'small muted' },
      (e.gunler ? e.gunler.map(g => T(GUN[g])).join(', ') : T('Her gün')) + (e.saatler ? ' · ' + e.saatler.map(([a, b2]) => String(a).padStart(2, '0') + ':00–' + String(b2).padStart(2, '0') + ':00').join(', ') : '')),
      h('div', { class: 'small dim' }, T('Haftalık düzen değiştirilemez; "Hep açık" ya da "Kapalı" ile bu dünyada sabitleyebilirsin.')));
  }
  if (e.harita) {
    const hr = e.harita;
    const siniflar = h('div', { class: 'chips' }, r.siniflar.map(m => { const var_ = hr.haritalar.includes(m), olur = hr.secilebilir.includes(m);
      return h('button', { type: 'button', class: 'chip link de-sinif' + (var_ ? ' on' : ''), disabled: !olur && !var_, title: olur ? null : T('Bu etkinliğin bu harita sınıfı için uzaylısı yok'),
        onclick: () => { hr.haritalar = var_ ? hr.haritalar.filter(x => x !== m) : [...hr.haritalar, m]; if (!var_ && hr.kota[m] == null) hr.kota[m] = Math.max(20, ...Object.values(hr.kota)); kaydet(); deBolumCiz(); } },
        var_ ? icon('check') : icon('plus'), m); }));
    out.push(h('div', { class: 'de-ara-baslik' }, T('Harita etkinliği')), h('div', { class: 'small muted' }, T('Etkinliğin uzaylılarının doğduğu harita sınıfları:')), siniflar,
      ...hr.uzaylilar.map(a => h('div', { class: 'de-alan-satir' }, npcIkon(a, 28), h('b', { class: 'small', style: { minWidth: '120px' } }, npcAdi(a)),
        deSayi(a.adet, v => { a.adet = v; kaydet(); }, { max: 200, gen: 56 }), h('span', { class: 'small muted' }, T('haritada aynı anda')))),
      Object.keys(hr.kota).length ? h('div', { class: 'small muted' }, T('Harita başına kota (etkinlik boyunca o haritada en çok doğan):')) : null,
      Object.keys(hr.kota).length ? h('div', { class: 'de-kota' }, hr.haritalar.filter(m => m in hr.kota).map(m => h('label', { class: 'de-dalga-deger' }, h('span', null, m),
        deSayi(hr.kota[m], v => { hr.kota[m] = v; kaydet(); }, { max: 10000, gen: 56 })))) : null,
      hr.patron ? h('div', { class: 'de-alan-satir' }, h('label', null, T('Patron')), h('label', { class: 'de-dalga-deger' }, h('span', null, T('Adet')),
        deSayi(hr.patron.adet, v => { hr.patron.adet = v; kaydet(); }, { max: 50, gen: 46 })),
        h('label', { class: 'de-dalga-deger' }, h('span', null, T('Süre (dk)')), deSayi(Math.round(hr.patron.sure_sn / 60), v => { hr.patron.sure_sn = Math.max(1, v) * 60; kaydet(); }, { min: 1, max: 1440, gen: 52 }))) : null);
  }
  if (e.degisti) out.push(btn(T('Etkinliği standarda döndür'), async () => { if (await deGeriAl('etkinlikler.json', yol)) deBolumCiz(); }, 'sm ghost', 'undo'));
  return h('div', { class: 'stack', style: { gap: '12px' } }, out);
}

// ================================================================== ÖDÜLLER VE EKONOMİ
const RUTBE_FORMUL = [['ep', N('Deneyim puanı başına')], ['onur', N('Onur puanı başına')], ['seviye', N('Seviye başına')], ['npc', N('Uzaylı puanı başına')],
  ['gorev', N('Tamamlanan görev başına')], ['oyuncu', N('Yenilen oyuncu puanı başına')], ['gemi', N('Gemi puanı başına')], ['gun', N('Kayıttan beri geçen gün başına')],
  ['dost', N('Kendi firmandan yok edilen oyuncu başına')], ['olum_dusman', N('Düşmana yenilme başına')], ['olum_radyasyon', N('Radyasyonda ölme başına')],
  ['phoenix', N('Yok edilen Phoenix başına')]];

async function deEkonomi(alan, b) {
  const r = await act(() => api('/api/dunya/bolum?bolum=ekonomi&dunya=' + encodeURIComponent(DE.did))); if (!r || DE.bolum !== 'ekonomi') return;
  const f = DE.sec.ek || (DE.sec.ek = { tum: false });
  const sv = r.seviyeler.map(x => x.slice()), es = r.esikler.slice(), fo = Object.assign({}, r.formul);
  const svKaydet = () => deYama('seviyeler.json', jp('seviyeler'), sv.map(x => x[1]));
  const sinir = f.tum ? sv.length : 26;
  const seviyeler = h('div', { class: 'de-seviye-izgara' }, sv.slice(1, sinir).map((x, i) => h('label', { class: 'de-dalga-deger' + (x[1] !== r.seviyeler_std[i + 1][1] ? ' degisti' : '') },
    h('span', { class: 'de-sv' }, x[0]), deSayi(x[1], v => { x[1] = v; svKaydet(); }, { min: 1, max: 1e15, adim: 1000, gen: 112 }))));
  const yuzde = h('div', { class: 'chips' }, [50, 75, 125, 200].map(p => h('button', { type: 'button', class: 'chip link', onclick: () => {
    sv.forEach((x, i) => { if (i) x[1] = Math.max(sv[i - 1][1] + 1, Math.round(r.seviyeler_std[i][1] * p / 100)); }); svKaydet().then(() => deBolumCiz()); } }, '%' + p)));
  const formul = h('div', { class: 'stack', style: { gap: '4px' } }, RUTBE_FORMUL.filter(([k]) => k in fo).map(([k, ad]) => h('div', { class: 'de-alan-satir' + (fo[k] !== r.formul_std[k] ? ' degisti' : '') },
    h('label', { style: { width: '240px' } }, T(ad)), h('input', { class: 'input num', type: 'number', step: 'any', value: fo[k], style: { width: '110px' },
      onchange: ev => { fo[k] = +ev.target.value || 0; deYama('rutbe.json', jp('formul'), fo); } }),
    deStd(r.formul_std[k], fo[k], () => { fo[k] = r.formul_std[k]; deYama('rutbe.json', jp('formul'), fo).then(() => deBolumCiz()); }, x => String(x)))));
  const esikler = h('div', { class: 'de-seviye-izgara genis' }, es.slice(1).map((n, i) => h('label', { class: 'de-dalga-deger' + (n !== r.esikler_std[i + 1] ? ' degisti' : '') },
    h('span', { class: 'ellipsis', style: { width: '150px' } }, r.rutbeler[i + 1] || i + 2),
    deSayi(n, v => { es[i + 1] = v; deYama('rutbe.json', jp('esikler'), es); }, { min: 1, max: 1e9, adim: 100, gen: 92 }))));
  const geri = (dosya, yol, ad) => btn(T('Standarda döndür'), async () => { if (await deGeriAl(dosya, yol)) deBolumCiz(); }, 'sm ghost', 'undo', { title: ad });
  doldur(alan, h('div', { class: 'stack' },
    h('div', { class: 'card' }, deBaslik(b)),
    h('div', { class: 'card' }, h('div', { class: 'row between wrap' }, h('h2', null, icon('star'), T('Seviye eşikleri')), h('div', { class: 'row', style: { gap: '6px' } }, yuzde, geri('seviyeler.json', jp('seviyeler')))),
      h('p', { class: 'desc' }, T('Her seviyeye ulaşmak için gereken toplam deneyim (EP). Hızlı ilerleme için standart eşiklerin yüzdesini seç.')), seviyeler,
      sv.length > sinir || f.tum ? btn(f.tum ? T('Daha az göster') : T('Bütün seviyeler ({0})', sv.length), () => { f.tum = !f.tum; deBolumCiz(); }, 'sm ghost', 'chevR') : null),
    h('div', { class: 'card' }, h('div', { class: 'row between wrap' }, h('h2', null, icon('shield'), T('Rütbe puanı formülü')), geri('rutbe.json', jp('formul'))),
      h('p', { class: 'desc' }, T('Rütbe puanı bu katsayılarla toplanır; eksi katsayılar puan düşürür.')), formul),
    h('div', { class: 'card' }, h('div', { class: 'row between wrap' }, h('h2', null, icon('shield'), T('Rütbe eşikleri')), geri('rutbe.json', jp('esikler'))),
      h('p', { class: 'desc' }, T('Her rütbe için gereken en az rütbe puanı (tek oyunculu oyunda rütbe bu eşiklere göre verilir).')), esikler),
    h('div', { class: 'alert bilgi' }, icon('info'), h('div', null, T('Günlük giriş takviminin ödülleri oyunun kendi dosyasından gösterildiği için burada değiştirilmez (değişen ödül takvimde eskisi gibi görünürdü).')))));
}

// ================================================================== PAYLAŞIM (dışa / içe aktarma, paylaşım kodu)
async function deDisari(w) {
  const r = await act(() => api('/api/dunya/kod', { dunya: w.id })); if (!r) return;
  const uzun = r.kod.length > 1900;
  const kod = h('textarea', { class: 'input mono de-kod', rows: 4, readonly: true }, r.kod);
  const m = modal({ title: T('"{0}" dünyasını paylaş', w.ad), wide: true, body: h('div', { class: 'stack', style: { gap: '12px' } },
    h('div', { class: 'de-paylas-ozet' }, deKapak(w.kapak, 'kucuk'), h('div', null, h('b', null, w.ad), h('div', { class: 'small muted' },
      w.standart ? T('Standart dünyanın taslağı') : T('{0} değişiklik', w.degisiklik)))),
    h('div', { class: 'de-paylas-yollar' },
      h('div', { class: 'de-paylas-yol' }, icon('download'), h('b', null, T('Dosya olarak')), h('div', { class: 'small muted' }, T('Bir .json dosyası: arkadaşın Dünya Editörü\'nde "İçe aktar" ile ekler.')),
        btn(T('Dosyaya kaydet'), () => act(() => api('/api/dunya/disari', { dunya: w.id })).then(x => { if (x && x.yol) { toast(T('Kaydedildi: {0}', x.yol), 'ok'); m.close(); } }), 'sm primary', 'download')),
      h('div', { class: 'de-paylas-yol' }, icon('copy'), h('b', null, T('Paylaşım kodu')), h('div', { class: 'small muted' },
        uzun ? T('Kod {0} karakter: Discord mesajına sığmaz, dosya olarak paylaş ya da metin dosyası olarak gönder.', fmtN(r.kod.length))
          : T('Kod {0} karakter: sohbete ya da Discord\'a yapıştırabilirsin.', fmtN(r.kod.length))),
        btn(T('Kodu kopyala'), async () => { try { await navigator.clipboard.writeText(r.kod); toast(T('Kod kopyalandı.'), 'ok'); } catch (e) { kod.select(); document.execCommand('copy'); toast(T('Kod kopyalandı.'), 'ok'); } }, 'sm', 'copy'))),
    kod,
    h('div', { class: 'small dim' }, T('Paylaşılan dünya yalnız değişiklikleri taşır; kayıtlar, pilotlar ve ilerleme paylaşılmaz.'))),
    foot: [btn(T('Kapat'), () => m.close(), 'ghost')] });
}

function deIceri() {
  const kod = h('textarea', { class: 'input mono de-kod', rows: 4, placeholder: 'OODUNYA1:…' });
  const sonuc = x => { if (!x || x.iptal) return; m.close(); DE.liste = x; deIceriRaporu(x); };
  const m = modal({ title: T('Dünya içe aktar'), wide: true, body: h('div', { class: 'stack', style: { gap: '12px' } },
    h('div', { class: 'de-paylas-yollar' },
      h('div', { class: 'de-paylas-yol' }, icon('folder'), h('b', null, T('Dosyadan')), h('div', { class: 'small muted' }, T('Paylaşılan .json dosyasını seç.')),
        btn(T('Dosya seç…'), () => act(() => api('/api/dunya/iceri', {})).then(sonuc), 'sm primary', 'upload')),
      h('div', { class: 'de-paylas-yol' }, icon('copy'), h('b', null, T('Paylaşım kodundan')), h('div', { class: 'small muted' }, T('Kodu aşağıya yapıştır.')),
        btn(T('Koddan içe aktar'), () => kod.value.trim() ? act(() => api('/api/dunya/iceri', { kod: kod.value })).then(sonuc) : toast(T('Önce kodu yapıştır.'), 'info'), 'sm', 'upload'))),
    kod, h('div', { class: 'small dim' }, T('İçe aktarılan dünya yeni bir dünya olarak eklenir; hiçbir dünyanın üzerine yazılmaz.'))),
    foot: [btn(T('Vazgeç'), () => m.close(), 'ghost')] });
}

function deIceriRaporu(x) {
  const r = x.rapor || {}, w = x.liste.find(d => d.id === x.yeni);
  const m = modal({ title: T('Dünya içe aktarıldı'), body: h('div', { class: 'stack', style: { gap: '12px' } },
    h('div', { class: 'de-paylas-ozet' }, art('dron_kayit', 'de-rapor-art'), h('div', null, h('b', null, w ? w.ad : x.yeni), h('div', { class: 'small muted' }, T('{0} değişiklik', r.degisiklik || 0)))),
    r.veri_farkli?.length ? h('div', { class: 'alert uyari' }, icon('alert'), h('div', null, T('Bu dünya farklı bir oyun verisiyle hazırlanmış ({0}). Değişiklikler uygulanır ama bazıları beklendiği gibi olmayabilir.', r.veri_farkli.join(', ')))) : null,
    r.atlanan ? h('div', { class: 'alert uyari' }, icon('alert'), h('div', null, T('{0} değişiklik uygulanamadığı için atlandı.', r.atlanan),
      r.sorunlar?.length ? h('ul', { class: 'small de-sorunlar' }, r.sorunlar.map(s2 => h('li', null, s2))) : null)) : null,
    !r.veri_farkli?.length && !r.atlanan ? h('div', { class: 'alert bilgi' }, icon('check'), h('div', null, T('Bütün değişiklikler uygulandı.'))) : null),
    foot: [btn(T('Kapat'), () => { m.close(); renderDunya(); }, 'ghost'), btn(T('Dünyayı aç'), () => { m.close(); deAc(x.yeni); }, 'primary', 'chevR')] });
}

// ================================================================== OYNA SAYFASI: kaydın dünyası
function oynaDunyaCipi(a) {
  const w = a.dunya_bilgi;
  return h('button', { type: 'button', class: 'oy-dunya', title: T('OYNA bu dünyayı açar. Değiştirmek için tıkla.'), onclick: ev => oynaDunyaMenu(ev.currentTarget, a) },
    deKapak(w.kapak, 'mini'), h('span', { class: 'oy-dunya-ad' }, h('small', null, T('Dünya')), h('b', null, w.ad)),
    w.standart ? icon('lock') : w.degisiklik ? badge(T('{0} değişiklik', w.degisiklik), 'orange') : null, icon('chevR'));
}
async function oynaDunyaMenu(anchor, a) {
  const r = await act(() => api('/api/dunyalar')); if (!r) return;
  popMenu(anchor, [...r.liste.map(w => ({ label: w.ad + (w.id === a.dunya_bilgi.id ? '  ✓' : ''), ic: w.standart ? 'lock' : 'globe',
    fn: () => act(() => api('/api/kayitlar/dunya', { id: a.id, dunya: w.id }), T('{0} artık "{1}" dünyasına girer.', a.pilot, w.ad)).then(x => x && poll()) })),
    '-', { label: T('Dünya Editörü'), ic: 'edit', fn: () => { DE.did = a.dunya_bilgi.id; DE.bolum = 'genel'; go('dunya'); } }]);
}

// ARKADAŞLARINLA OYNA > Host: sunucunun dünyası (panel ayarı arkadas_dunya; boş: kaydının dünyası)
function hostDunyaCipi(v) {
  const w = v.dunya.gecerli;
  return h('button', { type: 'button', class: 'oy-dunya', title: T('Sunucu bu dünyayla açılır; misafirler de bu dünyada oynar. Değiştirmek için tıkla.'),
    onclick: ev => popMenu(ev.currentTarget, [{ label: T('Kaydının dünyası ({0})', v.dunya.kaydin.ad) + (!v.dunya.secim ? '  ✓' : ''), ic: 'save', fn: () => hostDunyaSec('') },
      ...v.dunya.liste.map(x => ({ label: x.ad + (v.dunya.secim === x.id ? '  ✓' : ''), ic: x.standart ? 'lock' : 'globe', fn: () => hostDunyaSec(x.id) })), '-',
      { label: T('Dünya Editörü'), ic: 'edit', fn: () => { DE.did = w.id; DE.bolum = 'genel'; go('dunya'); } }]) },
    deKapak(w.kapak, 'mini'), h('span', { class: 'oy-dunya-ad' }, h('small', null, T('Sunucunun dünyası')), h('b', null, w.ad)),
    w.standart ? icon('lock') : w.degisiklik ? badge(T('{0} değişiklik', w.degisiklik), 'orange') : null, icon('chevR'));
}
function hostDunyaSec(id) {
  act(() => api('/api/arkadas/ayarlar', { dunya: id }), ARK.veri?.host?.acik ? T('Sunucu yeniden başlayınca bu dünya açılır.') : T('Kaydedildi.'))
    .then(r => { if (r) { ARK.veri = r; drawArkadas(); } });
}
