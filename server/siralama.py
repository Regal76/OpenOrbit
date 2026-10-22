"""Sıralama ödülleri (yol haritası Ö1; veri data/sira_odulleri.json <- tools/sira_odulleri.py).

Modun penceresi ödül aralıklarını bilgi komutuyla alır (ranges: RankRewardRangeModule {from, to}); ödül sekmesi her aralık için
RankRewardRequest {ranking: aralığın başı, rankType} gönderir -> reward(): RankRewardCommand {rankType, rewardContentModuleList
[RewardModule {lootId, amount}, RewardTitleModule {titleKey}], rewardRange}. Tablo yoksa None (oturum kayıttaki yanıta bakar).
rankType: 2 Gauntlet of Plutus, 7 Eternal Black Light, 9 Astral Ascension. Tek oyunculuda sıralamada yalnız oyuncu var: tablolar
pencerede görünür, dağıtım bot oyuncularla (Aşama 11).
"""
import json, os

HERE = os.path.dirname(os.path.abspath(__file__))
_P = os.path.join(HERE, 'data', 'sira_odulleri.json')
TABLES = {int(k): v for k, v in json.load(open(_P, encoding='utf8'))['tablolar'].items()} if os.path.exists(_P) else {}
PLUTUS, EBL, ASTRAL = 2, 7, 9
DEFAULT_REWARD, PAYLOAD_ESCORT_REWARD = 3, 6                 # EventRewardConfirmationCommand.RewardType


def mod(name, **f):
    f['_'] = name
    return f


def range_mod(r):
    return mod('RankRewardRangeModule', **{'from': r['den'], 'to': r['e']})


def ranges(rank_type):
    """Pencerenin ödül aralıkları (bilgi komutunun playerRanges / playerRankRanges alanı)."""
    return [range_mod(r) for r in TABLES.get(rank_type, {}).get('araliklar', [])]


def reward(f):
    """RankRewardRequest -> [RankRewardCommand] ya da None (bu rankType'ın tablosu yok)."""
    t = TABLES.get(int(f.get('rankType') or 0))
    if not t:
        return None
    n = int(f.get('ranking') or 0)
    r = next((r for r in t['araliklar'] if r['den'] <= n <= r['e']), None)
    if not r:
        return []
    return [('RankRewardCommand', dict(rankType=int(f['rankType']), rewardContentModuleList=items(r), rewardRange=range_mod(r)))]


def items(r):
    out = [mod('RewardModule', lootId=l, amount=a) for l, a in r['esyalar']]
    if r.get('unvan'):
        out.append(mod('RewardTitleModule', titleKey=r['unvan']))
    return out


def confirmation(rank, reward_type, r):
    """Etkinlik sonu tebrik penceresi: EventRewardConfirmationCommand {ranking, rewardType (komutun kendi RewardType'ı: 3 DEFAULT,
    6 PAYLOAD_ESCORT, ...), reward}; istemci EventRewardData'yla pencereyi açar."""
    return ('EventRewardConfirmationCommand', dict(ranking=int(rank), rewardType=reward_type, reward=items(r)))
