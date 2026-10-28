// Dünya Editörü'nün görev metinleri (2026-10-29): istemci görevin başlığını ve açıklamasını kendi metinlerinden görev kimliğiyle arar
// (DarkOrbit.QuestLocale.GetTitleEx / GetTitle / GetDescriptionEx / GetDescription; Quest.get_Description önce
// GetLabelEx("quest_description", görev, ...) dener, boş değilse GetDescription'a inmez); dünyaya eklenen görevlerin metni yoktu (başlık
// satırı boş, canlı 2026-10-28). Panel OYNA'da dünyanın görev metinlerini <istemci>/BepInEx/openorbit/gorev_metinleri.json'a yazar:
// {"<görev>": {"baslik": "...", "aciklama": "..."}} (panel/dunyalar.gorev_metinleri). Dosya değişince yeniden okunur (en çok saniyede
// bir bakılır); dosyada olmayan görev ve boş alan istemcinin kendi metniyle.
using System;
using System.Collections.Generic;
using System.IO;
using System.Reflection;
using System.Text.Json;
using BepInEx;
using DarkOrbit;
using HarmonyLib;

namespace OpenOrbit;

static class GorevMetinleri
{
    static readonly Dictionary<int, string> basliklar = new(), aciklamalar = new();
    static string yol;
    static DateTime okunan = DateTime.MinValue;
    static long bakilan;

    internal static void Uygula(Harmony h)
    {
        yol = Path.Combine(Paths.BepInExRootPath, "openorbit", "gorev_metinleri.json");
        Type t = typeof(QuestLocale);
        MethodBase baslikEx = AccessTools.Method(t, "GetTitleEx"), baslik = AccessTools.Method(t, "GetTitle"),
            aciklamaEx = AccessTools.Method(t, "GetDescriptionEx"), aciklama = AccessTools.Method(t, "GetDescription"),
            etiket = AccessTools.Method(t, "GetLabelEx");
        Eklenti.Bul(baslikEx, baslik, aciklamaEx, aciklama, etiket);
        h.Patch(baslikEx, prefix: Y(nameof(Baslik)));
        h.Patch(baslik, prefix: Y(nameof(Baslik)));
        h.Patch(aciklamaEx, prefix: Y(nameof(Aciklama)));
        h.Patch(aciklama, prefix: Y(nameof(Aciklama)));
        h.Patch(etiket, prefix: Y(nameof(Etiket)));
    }

    static HarmonyMethod Y(string ad) => new HarmonyMethod(typeof(GorevMetinleri), ad);

    static bool Baslik(int __0, ref string __result) => Ver(basliklar, __0, ref __result);

    static bool Aciklama(int __0, ref string __result) => Ver(aciklamalar, __0, ref __result);

    // GetLabelEx(etiket, görev, metin anahtarı, ...): yalnız açıklama etiketi
    static bool Etiket(string __0, int __1, ref string __result) => __0 != "quest_description" || Ver(aciklamalar, __1, ref __result);

    static bool Ver(Dictionary<int, string> sozluk, int gorev, ref string sonuc)
    {
        Oku();
        if (!sozluk.TryGetValue(gorev, out var metin))
            return true;
        sonuc = metin;
        return false;
    }

    static void Oku()
    {
        long simdi = Environment.TickCount64;
        if (simdi - bakilan < 1000)
            return;
        bakilan = simdi;
        try
        {
            var zaman = File.Exists(yol) ? File.GetLastWriteTimeUtc(yol) : DateTime.MinValue;
            if (zaman == okunan)
                return;
            okunan = zaman;
            basliklar.Clear();
            aciklamalar.Clear();
            if (zaman == DateTime.MinValue)
                return;
            using var belge = JsonDocument.Parse(File.ReadAllText(yol));
            foreach (var g in belge.RootElement.EnumerateObject())
            {
                if (!int.TryParse(g.Name, out int kimlik))
                    continue;
                if (g.Value.TryGetProperty("baslik", out var b) && b.ValueKind == JsonValueKind.String && b.GetString().Length > 0)
                    basliklar[kimlik] = b.GetString();
                if (g.Value.TryGetProperty("aciklama", out var a) && a.ValueKind == JsonValueKind.String && a.GetString().Length > 0)
                    aciklamalar[kimlik] = a.GetString();
            }
        }
        catch (Exception e)
        {
            GorselDokumu.Log?.LogWarning("görev metinleri okunamadı: " + e.Message);
        }
    }
}
