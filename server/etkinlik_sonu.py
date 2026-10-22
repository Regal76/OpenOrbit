"""Etkinlik sonunda kalan paralar onura (yol haritası E3; Chromin chromin.py'de, Infiltrator Fragment dunya_patronu.py'de).

İstemcinin geçmiş metinleri (history_msg_event_*_honor_converted): Battle Pass Key, Candy Corn ve Golden Candy Corn (halloweenoct2020),
Luminium, Styxus ve Charopos Shard (valentine). Oranlar: Candy Corn 1, Golden Candy Corn 20.000 (darkorbitwiki Trial of Terrors),
Luminium 1 ve en çok 10.000 onur (wiki Empyrian March), Battle Pass Key 5.000 (Immortal Union SSS); Valentine parçalarının oranı
bilinmiyor (uyarlama 1). Resmî sunucu 24-48 saat sonra çevirir; burada etkinlik bitince (oturumun ilk adımında).
Profilde: etkinlik_sonu {etkinlik: dönemin başladığı zaman damgası} (etkinlik sürerken görülenler).
"""
import json

import rutbe as RT
import takvim as TK
from eski_protokol import legacy

# etkinlik -> [(geçmiş metni, {lootId: onur oranı}, onur sınırı)] (Battle Pass Halloween'de: savas_bileti.py)
CONVERT = {
    'halloween': [('history_msg_event_halloweenoct2020_honor_converted',
                   {'resource_collectable_candy-corn': 1, 'resource_collectable_golden-candy-corn': 20000}, None),
                  ('history_msg_event_battle_pass_key_honor_converted', {'resource_battle-pass-key': 5000}, None)],
    'empyrian': [('history_msg_event_luminium_honor_converted', {'resource_collectable_luminium': 1}, 10000)],
    'immortal_union': [('history_msg_event_valentine_honor_converted',
                        {'resource_collectable_styxus-shard': 1, 'resource_collectable_charopos-shard': 1}, None)],
}


class EtkinlikSonu:
    def __init__(self, profil, magaza, log=print):
        self.p, self.m, self.log = profil, magaza, log

    @property
    def st(self):
        return self.p.d.setdefault('etkinlik_sonu', {})

    def tick(self, now):
        msgs = []
        for ev, rows in CONVERT.items():
            if TK.is_active(ev, now):
                if ev not in self.st:
                    with self.p.lock:
                        self.st[ev] = (TK.period(ev, now) or (now,))[0]
                        self.p.dirty = True
                continue
            if ev not in self.st:
                continue
            for text, rates, cap in rows:
                held = {loot: self.p.resource(loot) for loot in rates}
                hon = sum(n * rates[loot] for loot, n in held.items() if n > 0)
                if not hon:
                    continue
                hon = min(hon, cap) if cap else hon
                for loot, n in held.items():
                    if n > 0:
                        self.p.add_resource(loot, -n)
                        msgs += self.m.resource_msgs(loot, 0, -n)
                tot = self.p.gain(onur=hon, neden='event_honor')
                msgs.append(legacy('0|LM|ST|HON|%d|%d' % (hon, tot['onur'])))
                RT.note(self.p, text, args=json.dumps({'%AMOUNT%': str(hon)}))
                self.log('   %s bitti: %s -> %d onur' % (TK.EVENTS[ev]['ad'], {k: n for k, n in held.items() if n > 0}, hon))
            with self.p.lock:
                del self.st[ev]
                self.p.dirty = True
        return msgs
