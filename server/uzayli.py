"""Uzaylı yetenekleri (yol haritası Aşama 4): data/uzayli_yetenekleri.json'da istemcinin npcId'siyle tanımlı, haritadaki ve Galaksi
Kapısı'ndaki aynı uzaylıya birlikte uygulanır. dunya.py çağırır: vuruşta (on_hit), her adımda (tick), uzaylının lazer atışında
(laser_factor, after_shot, extra_target), ölümde (on_kill).

Yetenekler (veri alanları uzayli_yetenekleri.json'un açıklamasında):
  çağırma, yenilenme, ölünce doğurma, çağırdıkları yaşarken dokunulmazlık   dunya.py'deki kancalar (Aşama 1); burada öfkeli çağrı
  çağırdıkları yaşarken onarım ve öfke (Battleray)     son sure_sn içinde iki ya da daha çok saldıran (oyuncu + P.E.T.)
  can eşiğinde çağırma (Invoke XVI: 8 Impulse II)      bir kez
  gizlenme bozma (Mindfire Behemoth)                  yakındaki gizli oyuncu görünür olur
  yavaşlatan atış (Barb, Stinger, Saboteur, Behemoth)  isabet eden lazer: hız sınırı (küre, 120) ya da oranla yavaşlatma
  birden çok hedef (Behemoth)                          kritik canda P.E.T.'e de ateş eder
  roket (StreuneR) ve roket fırlatıcı (Annihilator)    ayrı beklemeyle oyuncuya roket
  tekillik (The Stinger)                               saniyede hasar, toplam sınırlı, menzil içinde
  kaybolma (Emperor Lordakium)                         belli hasardan sonra uzağa ışınlanır, iki sahte belirir (vurulunca patlar);
                                                       gizliyken can ve kalkan doldurur
  yapışkan bomba (Emperor Kristallon)                  aralıkla gecikmeli büyük hasar (tek oyunculu: grup boyuna bölünür)
  hız becerisi ve kapsüller (Emperor Sibelon)          kalkanı biterken hızlanır; haritada kapsüller belirir, Emperor toplarsa
                                                       güçlenir (can, kalkan, hasar), oyuncu yakınından geçerse kapsül yok olur
"""
import json, math, os, random, time

HERE = os.path.dirname(os.path.abspath(__file__))
Y = json.load(open(os.path.join(HERE, 'data', 'uzayli_yetenekleri.json'), encoding='utf8'))
ABILITIES = {int(k): v for k, v in Y['yetenekler'].items()}
CAPSULES = Y['kapsul_turleri']
BUFF_CAPSULE = 45                  # AssetTypeModule.AssetType (istemci): BUFF_CAPSULE
RING_RADIUS = 300                  # kapsül toplanınca Emperor'un çevresindeki halka (birim; uyarlama, canlıda ayarlanacak)
EMP_NOISE_SN = 5                   # Behemoth'un gizlenme bozan EMP'sinde mini harita paraziti (saniye; uyarlama)
SINGULARITY_TARGET = 21            # VisualModifierCommand.VisualModifier (istemci): tekilliğin hedefindeki altın girdap
CAPSULE_BASE = 152000000           # kapsül varlık kimlikleri


def mod(name, **f):
    f['_'] = name
    return f


def of(d):
    """NPC türünün yetenekleri: npcId'nin yetenekleri + türün kendi "davranis"ı (ikincisi öncelikli); not alanları ('_') atılır."""
    out = {k: v for k, v in ABILITIES.get(d.get('npc_kimlik'), {}).items() if not k.startswith('_')}
    out.update(d.get('davranis') or {})
    return out


def asset_create(aid, kind, x, y, name='', design=0):
    """Haritaya varlık (kapsül): kayıttaki AssetCreateCommand biçimi (2-1 istasyon taretleri)."""
    return ('AssetCreateCommand', dict(designId=design, clanId=0, showBubble=True, userName=name, assetId=aid, expansionStage=0,
                                       modifier=[], type=mod('AssetTypeModule', typeValue=kind), detectedByWarnRadar=True,
                                       invisible=False, posY=int(y), clanRelation=mod('ClanRelationModule', type=0), clanTag='',
                                       factionId=0, posX=int(x), visibleOnWarnRadar=False))


def asset_remove(aid, kind):
    return ('AssetRemoveCommand', {'assetType': mod('AssetTypeModule', typeValue=kind), 'uid': aid})


class Yetenekler:
    """Bir dünyanın uzaylı yetenekleri (dunya.World.alien)."""

    def __init__(self, world):
        import dunya                # dunya bu modülü içe aktarır; değerleri dünya kurulurken alınır
        self.w = world
        self.S, self.CFG, self.Mover = dunya.SAVAS, dunya.CFG, dunya.Mover
        self.capsules = {}          # kapsül kimliği -> {x, y, tur, sahip}
        self.next_capsule = CAPSULE_BASE
        self.hero_dots = []         # oyuncunun üzerindeki tekillikler: {npc, bitis, kalan, sn_hasar, sonraki}

    # ------------------------------------------------------------ yardımcılar
    def dist(self, n, now):
        hx, hy = self.w.hero_pos(now)
        nx, ny = n.mover.pos(now)
        return math.hypot(nx - hx, ny - hy)

    def hero_open(self, now):
        """Oyuncu uzaylı yeteneklerine açık mı (ölü, atlamada, güvenli bölgede, yerinde tamir koruması değil)."""
        w = self.w
        return not (w.hero_dead or w.jumping or now < w.invuln_until or w.in_peace(*w.hero_pos(now)))

    def adopt(self, parent, child):
        """Uzaylının doğurduğu/çağırdığı: yeniden doğmaz; kapıda dalganın uzaylısı sayılır (dalga o ölmeden bitmez)."""
        child.summoned, child.gate = True, parent.gate
        k = self.w.kapi
        if k and parent.id in k.npcs:
            k.npcs.add(child.id)

    def attacked(self, n, attacker, now):
        n.attackers[attacker or self.w.hid] = now

    def enraged(self, n, now):
        """Öfke (Battleray): son sure_sn içinde en az "saldiran" kadar farklı saldıran (oyuncu ve P.E.T. ayrı sayılır)."""
        o = n.davranis.get('ofke')
        if not o:
            return False
        return sum(1 for t in n.attackers.values() if now - t <= o.get('sure_sn', 10)) >= o.get('saldiran', 2)

    def extra_summons(self, n, now):
        """Öfkeliyken çağırma sınırına eklenen."""
        return n.davranis['ofke'].get('ek_cagri', 0) if self.enraged(n, now) else 0

    # ------------------------------------------------------------ vuruş
    def on_hit(self, n, dmg, attacker, now):
        """Uzaylı vuruldu (hasar uygulandıktan sonra): saldıran, can eşiğinde çağırma, kaybolma."""
        self.attacked(n, attacker, now)
        n.ab.pop('gizli', None)                                  # Emperor Lordakium bulundu: dolum durur
        for i, c in enumerate(n.davranis.get('can_esiginde_cagir', [])):
            key = 'esik_%d' % i
            if key not in n.ab and n.hp <= n.d['hp'] * c['oran']:
                n.ab[key] = now
                self.summon(n, c['tur'], c['adet'], now)
        k = n.davranis.get('kaybolma')
        if k and dmg > 0 and n.alive and n.hp > 0:
            n.ab['kayip'] = n.ab.get('kayip', 0) + dmg
            if n.ab['kayip'] >= k['hasar']:
                n.ab['kayip'] = 0
                self.vanish(n, k, now)

    def summon(self, n, tur, count, now):
        w = self.w
        x, y = n.mover.pos(now)
        for i in range(count):
            a = 2 * math.pi * i / max(1, count)
            c = w.spawn_npc_at(tur, x + math.cos(a) * 300, y + math.sin(a) * 300)
            self.adopt(n, c)
            c.engaged = True
            c.next_think = now
            n.children.add(c.id)
        w.log('   %s %d %s çağırdı (can %%%d)' % (n.d['ad'], count, self.CFG['tipler'][tur]['ad'], 100 * n.hp // max(1, n.d['hp'])))

    def far_spot(self, near, far):
        """Oyuncudan en az "far" uzakta (yoksa en uzak deneme) bir nokta; near: (x, y) yakınında arar (None: haritanın her yeri)."""
        w = self.w
        hx, hy = w.hero_pos()
        best, bd = None, -1
        for _ in range(40):
            if near:
                a, r = random.uniform(0, 2 * math.pi), random.uniform(far * 0.3, far)
                x, y = near[0] + math.cos(a) * r, near[1] + math.sin(a) * r
            else:
                x, y = random.uniform(600, w.map_w - 600), random.uniform(600, w.map_h - 600)
            x, y = min(max(x, 500), w.map_w - 500), min(max(y, 500), w.map_h - 500)
            d = math.hypot(x - hx, y - hy)
            if d >= far:
                return int(x), int(y)
            if d > bd:
                best, bd = (int(x), int(y)), d
        return best

    def vanish(self, n, k, now):
        """Emperor Lordakium: uzağa ışınlanır, iki sahtesi başka yerlerde belirir; oyuncunun seçimi bırakılır."""
        w = self.w
        x, y = self.far_spot(None, k.get('uzaklik', 2500))
        n.mover = self.Mover(x, y)
        n.engaged = False
        n.next_think = now + 2
        n.ab['gizli'] = now
        msgs = []
        if w.target == n.id:
            w.target, w.attacking = None, False
            msgs.append(('ShipDeselectionCommand', {}))
        if n.id in w.visible:
            w.visible.discard(n.id)
            msgs.append(('ShipRemoveCommand', {'userId': n.id}))
        w.send(msgs)
        fake = self.fake_type(n, k)
        for _ in range(k.get('sahte', 2)):
            fx, fy = self.far_spot(None, k.get('uzaklik', 2500))
            f = w.spawn_npc_at(fake, fx, fy)
            f.summoned, f.gate = True, n.gate
            f.ab['omur'] = now + k.get('sahte_omur_sn', 90)
        w.log('   %s kayboldu: (%d,%d), %d sahte' % (n.d['ad'], x, y, k.get('sahte', 2)))

    def fake_type(self, n, k):
        """Sahte Emperor türü (görünüşü gerçeğinin aynısı; 1 can, ateş etmez, ödülsüz, vurulunca patlar)."""
        key = 'sahte_' + n.tip
        if key not in self.CFG['tipler']:
            self.CFG['tipler'][key] = dict(ad=n.d['ad'], model=n.model, hp=1, kalkan=0, hasar=0, hiz=n.d['hiz'], saldirgan=False,
                                      odul=dict(ep=0, onur=0, kredi=0, uridyum=0), kargo={}, sayilmaz=True,
                                      davranis={'olunce_patla': {'hasar': k.get('patlama', 60000),
                                                                 'yaricap': k.get('patlama_yaricap', 500)}})
        return key

    # ------------------------------------------------------------ uzaylının atışı
    def laser_factor(self, n, now):
        """Uzaylının lazer hasarı çarpanı: öfke (Battleray: RSB-75), Emperor Sibelon'un hasar kapsülleri."""
        f = 1 + n.ab.get('hasar_bonus', 0)
        if self.enraged(n, now):
            f *= n.davranis['ofke'].get('hasar_carpani', 1)
        return f

    def after_shot(self, n, now, hit):
        """Uzaylının lazeri oyuncuya isabet etti: yavaşlatan atış."""
        s = n.davranis.get('yavaslatan_atis')
        if not s or not hit or self.w.hero_dead:
            return
        if s.get('menzil') and self.dist(n, now) > s['menzil']:
            return
        w = self.w
        src = 'yavaslatma_%s' % n.tip
        if 'hiz' in s:
            w.hero_etki.remove('hiz_siniri', source=src)          # yenilenir, birikmez
            w.hero_effect('hiz_siniri', s['sn'], s['hiz'], source=src)
        else:
            w.hero_etki.remove('yavas', source=src)
            w.hero_effect('yavas', s['sn'], s['oran'], source=src)

    def extra_target(self, n, now):
        """Birden çok hedef (Mindfire Behemoth): kritik canda P.E.T.'e de ateş eder."""
        c = n.davranis.get('coklu_hedef')
        return bool(c) and n.hp <= n.d['hp'] * c.get('can_orani', 0.25)

    # ------------------------------------------------------------ her adım
    def tick(self, now):
        w = self.w
        for n in list(w.npcs.values()):
            if not n.alive or not n.davranis and not n.ab:
                continue
            if 'omur' in n.ab and now >= n.ab['omur']:
                self.expire(n)
                continue
            d = n.davranis
            if 'cagrilar_yasarken_onarim' in d:
                self.summon_repair(n, now)
            if 'gizlenme_bozar' in d:
                self.uncloak(n, now)
            if 'roket' in d:
                self.rocket(n, now)
            if 'tekillik' in d:
                self.singularity(n, now)
            if 'yapiskan_bomba' in d:
                self.bomb(n, now)
            if 'hiz_becerisi' in d:
                self.speed_skill(n, now)
            if 'kaybolma' in d and n.ab.get('gizli'):
                self.hidden_regen(n, now)
        self.dot_tick(now)
        self.capsule_tick(now)

    def expire(self, n):
        """Ömrü biten (sahte Emperor): sessizce kalkar."""
        w = self.w
        n.alive = False
        w.npcs.pop(n.id, None)
        msgs = []
        if w.target == n.id:
            w.target, w.attacking = None, False
            msgs.append(('ShipDeselectionCommand', {}))
        if n.id in w.visible:
            w.visible.discard(n.id)
            msgs.append(('ShipRemoveCommand', {'userId': n.id}))
        w.send(msgs)

    def summon_repair(self, n, now):
        """Çağırdıkları yaşarken saniyede onarım (Battleray: 600, öfkeliyken 30.000)."""
        if now < n.ab.get('onarim', 0):
            return
        n.ab['onarim'] = now + 1.0
        n.children = {c for c in n.children if c in self.w.npcs and self.w.npcs[c].alive}
        if not n.children or n.hp >= n.d['hp']:
            return
        r = n.davranis['cagrilar_yasarken_onarim']
        amount = n.davranis['ofke'].get('onarim_can_sn', r['can_sn']) if self.enraged(n, now) else r['can_sn']
        n.hp = min(n.d['hp'], n.hp + amount)
        if self.w.target == n.id:
            self.w.send([self.w.selection(n)])

    def uncloak(self, n, now):
        w = self.w
        if not (w.abilities.cloaked(now) or w.items.cloaked()) or w.hero_dead:
            return
        if self.dist(n, now) <= n.davranis['gizlenme_bozar'].get('menzil', 1500):
            w.abilities.reveal()
            w.items.reveal()
            # EMP darbesi (Ö1): istemcinin "EMP Malus Bolt"u mini haritayı parazitler (MapEventsAssemblyHelper.AssembleEmpMalusBolt,
            # 0|n|EMAL|<saniye>; süre uyarlama)
            from eski_protokol import legacy
            w.send([legacy('0|n|EMAL|%d' % EMP_NOISE_SN)])
            w.log('   %s gizlenmeyi bozdu' % n.d['ad'])

    def rocket(self, n, now):
        """Uzaylının roketi ya da roket fırlatıcı salvosu: kendi beklemesiyle, ateş menzilinde."""
        w, r = self.w, n.davranis['roket']
        if (not n.engaged or now < n.ab.get('roket', 0) or n.etki.frozen(now) or not self.hero_open(now)
                or self.dist(n, now) > w.npc_range(n)):
            return
        n.ab['roket'] = now + r.get('bekleme_sn', 8)
        m = w.p.mods()
        hit = random.random() < self.S['roket_isabet'] * (1 - m.get('kacinma', 0)) * (1 - n.etki.accuracy_loss(now))
        flight = self.S['roket_ucus_sn']
        if r.get('firlatici'):
            import savas_esya as SE
            tur = SE.LAUNCHER_AMMO.get('ammunition_rocketlauncher_eco-10', {}).get('tur', 1)
            flight = SE.S['fircatici']['ucus_sn']          # salvo istemcide ~1 sn sonra fırlar (oyuncununki gibi; canlı test H25)
            w.send([('HellstormAttackCommand', dict(attackerId=n.id, targetId=w.hid, hit=hit, currentLoad=r.get('adet', 5),
                                                    rocketType=mod('AmmunitionTypeModule', typeValue=tur)))])
        else:
            from eski_protokol import legacy
            w.send([legacy('0|v|%d|%d|%s|1|0|0' % (n.id, w.hid, 'H' if hit else 'M'))])
        dmg = int(r['hasar'] * random.uniform(0.85, 1.0))
        uid = n.id

        def land():
            if w.hero_dead or w.jumping:
                return
            if not hit:
                w.send([('AttackMissedCommand', dict(attackType=mod('AttackTypeModule', attackTypeValue=0), targetUserId=w.hid,
                                                     skillColorId=0))])
                return
            w.send(w.hurt_hero(dmg, w.npcs.get(uid) or n, atype=0))
        w.later(flight, land)

    def singularity(self, n, now):
        """The Stinger'ın tekilliği başlar: oyuncunun üzerinde saniyede hasar (dot_tick)."""
        t = n.davranis['tekillik']
        if not n.engaged or now < n.ab.get('tekillik', 0) or not self.hero_open(now) or self.dist(n, now) > t['menzil']:
            return
        n.ab['tekillik'] = now + t['bekleme_sn']
        if not any(d_.get('gorsel') for d_ in self.hero_dots):
            self.w.send([self.singularity_visual(True)])    # canlı test H30: hasar vardı, görsel yoktu
        self.hero_dots.append(dict(npc=n.id, bitis=now + t['sure_sn'], kalan=t['azami'], sn_hasar=t['sn_hasar'], sonraki=now + 1.0,
                                   menzil=t['menzil'], gorsel=True))
        self.w.log('   %s tekilliği başladı' % n.d['ad'])

    def singularity_visual(self, on):
        return ('VisualModifierCommand', dict(userId=self.w.hid, modifier=SINGULARITY_TARGET, attribute=0, additionalAttribute='',
                                              count=0, activated=on))

    def dot_tick(self, now):
        w = self.w
        keep = []
        for dot in self.hero_dots:
            n = w.npcs.get(dot['npc'])
            if not n or not n.alive or now >= dot['bitis'] or dot['kalan'] <= 0 or w.hero_dead:
                continue
            keep.append(dot)
            if now < dot['sonraki']:
                continue
            dot['sonraki'] += 1.0
            if self.dist(n, now) > dot['menzil'] or not self.hero_open(now):
                continue
            dmg = min(dot['sn_hasar'], dot['kalan'])
            dot['kalan'] -= dmg
            w.send(w.hurt_hero(dmg, n))
        if any(d_.get('gorsel') for d_ in self.hero_dots) and not any(d_.get('gorsel') for d_ in keep):
            w.send([self.singularity_visual(False)])
        self.hero_dots = keep

    def bomb(self, n, now):
        """Emperor Kristallon'un yapışkan bombası: aralıkla, gecikmeli; tek oyunculu: hasar grup boyuna bölünür."""
        b, w = n.davranis['yapiskan_bomba'], self.w
        if not n.engaged or not self.hero_open(now) or self.dist(n, now) > w.npc_range(n) * 2:
            return
        if 'bomba' not in n.ab:
            n.ab['bomba'] = now + b['aralik_sn']           # ilk bomba savaş başladıktan aralik_sn sonra
            return
        if now < n.ab['bomba']:
            return
        n.ab['bomba'] = now + b['aralik_sn']
        dmg = int(b['hasar'] / max(1, b.get('grup', 1)))
        from eski_protokol import legacy
        w.send([legacy('0|v|%d|%d|H|1|0|0' % (n.id, w.hid))])
        uid = n.id

        def boom():
            if not w.hero_dead and not w.jumping:
                w.send(w.hurt_hero(dmg, w.npcs.get(uid) or n, atype=0))
        w.later(b.get('gecikme_sn', 2), boom)
        w.log('   %s yapışkan bomba (%d hasar)' % (n.d['ad'], dmg))

    def hidden_regen(self, n, now):
        """Gizli Emperor Lordakium saniyede can ve kalkan doldurur."""
        if now < n.ab.get('dolum', 0):
            return
        n.ab['dolum'] = now + 1.0
        k = n.davranis['kaybolma']
        n.hp = min(n.d['hp'], n.hp + k.get('can_sn', 0))
        n.shield = min(n.d['kalkan'], n.shield + k.get('kalkan_sn', 0))

    # ------------------------------------------------------------ Emperor Sibelon: hız ve kapsüller
    def speed_skill(self, n, now):
        h = n.davranis['hiz_becerisi']
        if 'hiz' not in n.ab and n.shield <= n.d['kalkan'] * h.get('kalkan_orani', 0.1):
            n.ab['hiz'] = h['hiz']
            n.ab['kapsul'] = now
            self.w.log('   %s hızlandı (%d)' % (n.d['ad'], h['hiz']))
        k = n.davranis.get('kapsuller')
        if 'hiz' not in n.ab or not k:
            return
        mine = [a for a, c in self.capsules.items() if c['sahip'] == n.id]
        if len(mine) < k['adet'] and now >= n.ab['kapsul']:
            n.ab['kapsul'] = now + k['aralik_sn']
            self.spawn_capsule(n)
            mine = [a for a, c in self.capsules.items() if c['sahip'] == n.id]
        if not mine or n.etki.frozen(now):
            return
        nx, ny = n.mover.pos(now)
        aid = min(mine, key=lambda a: math.hypot(self.capsules[a]['x'] - nx, self.capsules[a]['y'] - ny))
        c = self.capsules[aid]
        d = math.hypot(c['x'] - nx, c['y'] - ny)
        if d <= k.get('toplama_mesafe', 150):
            if 'toplama' not in c:
                c['toplama'] = now + k['toplama_ms'] / 1000.0
                self.w.send([('StartCapsuleCollectCommand', {'collectorId': n.id, 'assetId': aid, 'timer': k['toplama_ms']})])
            elif now >= c['toplama']:
                self.collect_capsule(n, aid, k)
            return
        if n.ab.get('kapsula') != aid or n.mover.t1 <= now:
            n.ab['kapsula'] = aid
            ms = n.mover.go(c['x'], c['y'], n.ab['hiz'] * n.etki.speed_factor(now), now)
            n.next_think = now + ms / 1000.0 + 0.5          # kovalamayı bırakıp kapsüle gider
            self.w.send([('MoveCommand', dict(userId=n.id, x=int(c['x']), y=int(c['y']), timeToTarget=ms))])

    def spawn_capsule(self, n):
        w = self.w
        self.next_capsule += 1
        aid = self.next_capsule
        x, y = self.far_spot(n.mover.pos(time.time()), 2500)
        kind = random.choice(CAPSULES)
        self.capsules[aid] = dict(x=x, y=y, tur=kind, sahip=n.id)
        w.send([asset_create(aid, BUFF_CAPSULE, x, y, name='%s-Buff' % {'can': 'HP', 'kalkan': 'SHD', 'hasar': 'DMG'}[kind],
                             design=CAPSULES.index(kind))])
        w.log('   kapsül belirdi: %s (%d,%d)' % (kind, x, y))

    def drop_capsule(self, aid, why):
        c = self.capsules.pop(aid, None)
        if not c:
            return
        msgs = [asset_remove(aid, BUFF_CAPSULE)]
        if 'toplama' in c:
            msgs.insert(0, ('StopCapsuleCollectCommand', {'collectorId': c['sahip']}))
        self.w.send(msgs)
        self.w.log('   kapsül %s: %s' % (why, c['tur']))

    def collect_capsule(self, n, aid, k):
        """Emperor kapsülü topladı: can/kalkan %10 dolar ya da hasarı artar ve oyuncununki düşer (Emperor ölünce kalkar)."""
        w = self.w
        kind = self.capsules[aid]['tur']
        if kind == 'can':
            n.hp = min(n.d['hp'], n.hp + n.d['hp'] * k['can'])
        elif kind == 'kalkan':
            n.shield = min(n.d['kalkan'], n.shield + n.d['kalkan'] * k['kalkan'])
        else:
            n.ab['hasar_bonus'] = n.ab.get('hasar_bonus', 0) + k['hasar']
            w.hero_effect('zayiflik', 3600, k['hasar'], source='kapsul_%d' % n.id)
        self.drop_capsule(aid, 'toplandı')
        # toplama görseli (Ö1): Emperor'un çevresinde 4 sn'lik parlayan halka; tür 0 hasar (kırmızı), 1 kalkan, 2 can (istemci:
        # EmperorSibelonBuffRingCommandHandler, çap radius x 2; yarıçap uyarlama)
        x, y = n.mover.pos(time.time())
        w.send([('EmperorSibelonBuffRingCommand', dict(avatarId=n.id, type={'hasar': 0, 'kalkan': 1, 'can': 2}[kind], radius=RING_RADIUS,
                                                       x=int(x), y=int(y)))])
        if w.target == n.id:
            w.send([w.selection(n)])

    def capsule_tick(self, now):
        """Oyuncu kapsülün yakınından geçerse kapsül yok olur; sahibi ölen kapsüller kalkar."""
        if not self.capsules:
            return
        w = self.w
        hx, hy = w.hero_pos(now)
        for aid, c in list(self.capsules.items()):
            owner = w.npcs.get(c['sahip'])
            if not owner or not owner.alive:
                self.drop_capsule(aid, 'sahipsiz kaldı')
            elif not w.hero_dead and math.hypot(c['x'] - hx, c['y'] - hy) <= owner.davranis['kapsuller'].get('toplama_mesafe', 150):
                self.drop_capsule(aid, 'oyuncu yok etti')

    def capsule_msgs(self):
        """Harita yeniden yüklenince kapsüller yeniden bildirilir."""
        return [asset_create(aid, BUFF_CAPSULE, c['x'], c['y'], design=CAPSULES.index(c['tur'])) for aid, c in self.capsules.items()]

    # ------------------------------------------------------------ ölüm
    def on_kill(self, n, x, y):
        """Uzaylı öldü: patlayan (sahte Emperor) yakındaki oyuncuyu vurur; DMG kapsülünün oyuncudaki etkisi kalkar."""
        w = self.w
        p = n.davranis.get('olunce_patla')
        msgs = []
        if p and not w.hero_dead:
            hx, hy = w.hero_pos()
            if math.hypot(x - hx, y - hy) <= p['yaricap']:
                msgs += w.hurt_hero(p['hasar'], n, atype=0)
                w.log('   %s patladı: %d hasar' % (n.d['ad'], p['hasar']))
        if w.hero_etki.get('zayiflik'):
            w.hero_etki.remove('zayiflik', source='kapsul_%d' % n.id)
        left = [d for d in self.hero_dots if d['npc'] != n.id]
        if any(d.get('gorsel') for d in self.hero_dots) and not any(d.get('gorsel') for d in left):
            msgs.append(self.singularity_visual(False))                 # tekilliğin sahibi öldü: girdap kalkar
        self.hero_dots = left
        return msgs
