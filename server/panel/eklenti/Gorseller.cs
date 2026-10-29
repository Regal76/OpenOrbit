// Oyun içi görsellerin dökümü (panelin Mağaza / Hangar / Skylab sayfaları; kullanıcı isteği 2026-10-28): simgeler istemcinin
// Addressables paketindeki sprite atlaslarında (StreamingAssets/aa/BuildTarget/atlas_assets_all.bundle; dokular Crunch / BC7, Python'la
// çözülemiyor). İstemci açılınca atlas sayfaları bir kez Unity'nin kendisiyle PNG'ye çevrilir: <istemci>/BepInEx/openorbit/gorsel/
// (oyunun telifli görselleri: depoya girmez, istemci klasörü .gitignore'da). dizin.json en son yazılır: sprite adı -> [sayfa, x, y, g, y,
// tam g, tam y, ox, oy] (üst sol kökenli piksel; atlaslar dikdörtgen paketli, döndürme yok). Paketin boyutu ve tarihi değişmedikçe
// (ve atlas listesi) değişmedikçe yeniden dökülmez. Atlasın sprite'ları geç bağlanıyor (Sprite.texture boş): sayfalar SpriteAtlas.GetSprites'ın kopyalarından.
// Eşya adları da panelin dillerinde: adlar_<dil>.json (lootId -> ad; istemcinin resource_items'ındaki items_<lootId>_fullname).
// Panelin eşya ipucunun metinleri: metinler_<dil>.json {"e": {lootId: [ad, tür, ipucu açıklaması, açıklama, not, kaynak]},
// "n": {nitelik: ad}} (items_<lootId>_fullname/_short/_tooltip_description/_description/_hint/_sources; nitelik adları
// items_equipment_shipupgrade_modifiertype_<nitelik>: kararsız modül, QFC ve parçacık silahı nitelikleri).
using System;
using System.Collections.Generic;
using System.IO;
using System.Text;
using BepInEx;
using UnityEngine;
using UnityEngine.U2D;
using DarkOrbit;
using Il2CppInterop.Runtime;
using Il2CppInterop.Runtime.InteropTypes.Arrays;

namespace OpenOrbit;

public class GorselDokumu : MonoBehaviour
{
    public GorselDokumu(IntPtr p) : base(p) { }

    static readonly string[] ATLASLAR = { "Items", "hanger", "Shop", "UI", "CommonUI", "Misc", "Boosters", "FeatureMenu" };
    static readonly string[] DILLER = { "tr", "en", "de", "es", "fr", "pl", "pt", "ru" };     // panelin dilleri (panel/dil.py)

    internal static BepInEx.Logging.ManualLogSource Log;
    static string klasor, surum;
    static readonly Queue<Texture2D> sayfalar = new();
    static readonly StringBuilder dizin = new();
    static readonly StringBuilder boyutlar = new();
    static int durum;                   // 0 bekliyor, 1 sayfalar yazılıyor, 2 bitti

    void Update()
    {
        if (durum == 2 || Time.realtimeSinceStartup < 5f)
            return;
        try
        {
            if (durum == 0)
                Basla();
            else if (sayfalar.Count > 0)
                Yaz(sayfalar.Dequeue());
            else
                Bitir();
        }
        catch (Exception e)
        {
            durum = 2;
            Log.LogError("görsel dökümü: " + e);
        }
    }

    static void Basla()
    {
        klasor = Path.Combine(Paths.BepInExRootPath, "openorbit", "gorsel");
        var fi = new FileInfo(Path.Combine(Application.streamingAssetsPath, "aa", "BuildTarget", "atlas_assets_all.bundle"));
        surum = fi.Length + "-" + fi.LastWriteTimeUtc.Ticks + "-" + string.Join(",", ATLASLAR) + "-metin1";   // atlas listesi ya da döküm biçimi değişince de yeniden
        string d = Path.Combine(klasor, "dizin.json");
        if (File.Exists(d) && File.ReadAllText(d).Contains("\"surum\": \"" + surum + "\""))
        {
            durum = 2;
            return;
        }
        Directory.CreateDirectory(klasor);
        var adlar = new HashSet<string>();
        Paket("atlas_assets_all", "Assets/Res/UI/Images/Atlas/Items.spriteatlas", ab => Atlaslar(ab, adlar));
        Paket("localizations_assets_all", "Assets/Res/Localization/Data/en/data/resource_items.asset", Adlar);
        Log.LogInfo($"görsel dökümü: {adlar.Count} sprite, {sayfalar.Count} sayfa -> {klasor}");
        durum = 1;
    }

    // Addressables yüklediyse (paketin yüklü adı dosyanınki değil: içindeki bir varlıkla bulunur) o; yoksa biz yükler, işimiz bitince
    // bırakırız (sonra o yükleyebilsin; dokular bellekte kalır)
    static void Paket(string ad, string varlik, Action<AssetBundle> is_)
    {
        AssetBundle ab = null;
        foreach (var b in AssetBundle.GetAllLoadedAssetBundles_Native())
            if (b != null && b.Contains(varlik))
                ab = b;
        bool biz = ab == null;
        if (biz)
            ab = AssetBundle.LoadFromFile(Path.Combine(Application.streamingAssetsPath, "aa", "BuildTarget", ad + ".bundle"));
        if (ab == null)
            throw new FileLoadException("paket yüklenemedi: " + ad);
        try
        {
            is_(ab);
        }
        finally
        {
            if (biz)
                ab.Unload(false);
        }
    }

    static void Atlaslar(AssetBundle ab, HashSet<string> adlar)
    {
        var gorulen = new HashSet<IntPtr>();
        foreach (var o in ab.LoadAllAssets(Il2CppType.Of<SpriteAtlas>()))
        {
            var atlas = o.Cast<SpriteAtlas>();
            if (Array.IndexOf(ATLASLAR, atlas.name) < 0)
                continue;
            var arr = new Il2CppReferenceArray<Sprite>(atlas.spriteCount);
            atlas.GetSprites(arr);
            foreach (var s in arr)
            {
                var t = s.texture;
                string ad = s.name.Replace("(Clone)", "");
                if (t != null && adlar.Add(ad))
                {
                    if (gorulen.Add(t.Pointer))
                    {
                        sayfalar.Enqueue(t);
                        boyutlar.Append(boyutlar.Length > 0 ? ",\n" : "").Append($"  \"{t.name}\": [{t.width}, {t.height}]");
                    }
                    Rect r = s.textureRect, tam = s.rect;
                    Vector2 off = s.textureRectOffset;
                    dizin.Append(dizin.Length > 0 ? ",\n" : "").Append(
                        $"  \"{Kac(ad)}\": [\"{t.name}\", {Y(r.x)}, {Y(t.height - r.y - r.height)}, {Y(r.width)}, {Y(r.height)}, "
                        + $"{Y(tam.width)}, {Y(tam.height)}, {Y(off.x)}, {Y(tam.height - off.y - r.height)}]");
                }
                UnityEngine.Object.Destroy(s);
            }
        }
    }

    static void Adlar(AssetBundle ab)
    {
        foreach (var dil in DILLER)
        {
            var o = ab.LoadAsset("Assets/Res/Localization/Data/" + dil + "/data/resource_items.asset", Il2CppType.Of<LocalizationContainer>());
            if (o == null)
                continue;
            var sb = new StringBuilder();
            var esya = new SortedDictionary<string, string[]>(StringComparer.Ordinal);
            var nitelik = new StringBuilder();
            foreach (var kv in o.Cast<LocalizationContainer>().data)
            {
                if (!kv.key.StartsWith("items_"))
                    continue;
                if (kv.key.EndsWith("_fullname"))
                    sb.Append(sb.Length > 0 ? ",\n" : "").Append($"  \"{Kac(kv.key[6..^9])}\": \"{Kac(kv.value)}\"");
                if (kv.key.StartsWith(NITELIK))
                {
                    nitelik.Append(nitelik.Length > 0 ? ",\n" : "").Append($"  \"{Kac(kv.key[NITELIK.Length..])}\": \"{Kac(kv.value)}\"");
                    continue;
                }
                for (int i = 0; i < EKLER.Length; i++)
                    if (kv.key.EndsWith(EKLER[i]))
                    {
                        string loot = kv.key[6..^EKLER[i].Length];
                        if (!esya.TryGetValue(loot, out var m))
                            esya[loot] = m = new string[EKLER.Length];
                        m[i] = kv.value;
                        break;
                    }
            }
            File.WriteAllText(Path.Combine(klasor, "adlar_" + dil + ".json"), "{\n" + sb + "\n}\n");
            var mb = new StringBuilder();
            foreach (var kv in esya)
                mb.Append(mb.Length > 0 ? ",\n" : "").Append($"  \"{Kac(kv.Key)}\": [")
                  .Append(string.Join(", ", Array.ConvertAll(kv.Value, v => v == null ? "null" : "\"" + Kac(v) + "\""))).Append(']');
            File.WriteAllText(Path.Combine(klasor, "metinler_" + dil + ".json"), "{\"e\": {\n" + mb + "\n},\n\"n\": {\n" + nitelik + "\n}}\n");
        }
    }

    // ipucu metinleri, metinler_<dil>.json'daki sırayla; _tooltip_description _description'dan önce denenir (ikisi de _description ile biter)
    static readonly string[] EKLER = { "_fullname", "_short", "_tooltip_description", "_description", "_hint", "_sources" };
    const string NITELIK = "items_equipment_shipupgrade_modifiertype_";

    static void Yaz(Texture2D t)
    {
        var rt = RenderTexture.GetTemporary(t.width, t.height, 0, RenderTextureFormat.ARGB32, RenderTextureReadWrite.sRGB);
        var once = RenderTexture.active;
        Graphics.Blit(t, rt);
        RenderTexture.active = rt;
        var cikti = new Texture2D(t.width, t.height, TextureFormat.RGBA32, false);
        cikti.ReadPixels(new Rect(0, 0, t.width, t.height), 0, 0);
        cikti.Apply(false);
        RenderTexture.active = once;
        RenderTexture.ReleaseTemporary(rt);
        File.WriteAllBytes(Path.Combine(klasor, t.name + ".png"), ImageConversion.EncodeToPNG(cikti));
        UnityEngine.Object.Destroy(cikti);
    }

    static void Bitir()
    {
        string d = Path.Combine(klasor, "dizin.json");
        File.WriteAllText(d + ".tmp", "{\"surum\": \"" + surum + "\",\n\"sayfalar\": {\n" + boyutlar + "\n},\n\"sprite\": {\n" + dizin + "\n}}\n");
        File.Move(d + ".tmp", d, true);
        dizin.Clear();
        boyutlar.Clear();
        Resources.UnloadUnusedAssets();
        durum = 2;
        Log.LogInfo("görsel dökümü bitti");
    }

    static string Y(float v) => Math.Round(v).ToString(System.Globalization.CultureInfo.InvariantCulture);

    static string Kac(string s) => s.Replace("\\", "\\\\").Replace("\"", "\\\"").Replace("\n", "\\n").Replace("\r", "").Replace("\t", " ");
}
