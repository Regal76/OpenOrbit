"""Yapay zekâlı rakip oyuncu gemileri (PvP botlar).

Haritalarda (normal uzay haritaları ve savaş haritaları) dolaşan, gerçek oyuncu gemisi modeli,
unvanı, klan etiketi, dronları ve rütbesiyle görünen rakip firma pilotları (MMO / EIC / VRU).
Oyuncuyu fark edince ya da oyuncu saldırınca savaşır; x4/RSB-75 lazer kombosu, roket ve roketatar
salvosu atar, Insta-Shield ve yetenek kullanır. Yok edilince kargo kutusu ve yüksek PvP ödülü
(EP, Onur, Kredi, Uridyum) verir.
"""
import math, os, random, time

import ayar as AY
import durum as DURUM
from eski_protokol import legacy


def mod(name, **f):
    f['_'] = name
    return f

BOT_UID_BASE = 200000000

BOT_SHIPS = {
    'ship_goliath-plus': {
        'hp': 950000, 'shield': 1150000, 'speed': 540,
        'min_dmg': 68000, 'max_dmg': 96000, 'formation': 13,   # Ring
        'shield_absorb': 0.85,
    },
    'ship_solace-plus': {
        'hp': 1000000, 'shield': 1050000, 'speed': 530,
        'min_dmg': 64000, 'max_dmg': 92000, 'formation': 12,   # Heart
        'has_heal': True, 'shield_absorb': 0.85,
    },
    'ship_pusat-plus': {
        'hp': 720000, 'shield': 800000, 'speed': 585,
        'min_dmg': 80000, 'max_dmg': 112000, 'formation': 14,  # Drill
        'shield_absorb': 0.80,
    },
    'ship_spectrum-plus': {
        'hp': 950000, 'shield': 1600000, 'speed': 515,
        'min_dmg': 56000, 'max_dmg': 82000, 'formation': 13,   # Ring
        'shield_absorb': 0.90,
    },
    'ship_cyborg': {
        'hp': 880000, 'shield': 980000, 'speed': 535,
        'min_dmg': 72000, 'max_dmg': 102000, 'formation': 14,  # Drill
        'shield_absorb': 0.85,
    },
    'ship_centurion': {
        'hp': 900000, 'shield': 950000, 'speed': 540,
        'min_dmg': 70000, 'max_dmg': 98000, 'formation': 12,   # Heart
        'shield_absorb': 0.85,
    },
    'ship_orcus': {
        'hp': 880000, 'shield': 1100000, 'speed': 535,
        'min_dmg': 68000, 'max_dmg': 96000, 'formation': 12,   # Heart
        'shield_absorb': 0.85,
    },
    'ship_berserker': {
        'hp': 1250000, 'shield': 850000, 'speed': 510,
        'min_dmg': 66000, 'max_dmg': 92000, 'formation': 12,   # Heart
        'shield_absorb': 0.85,
    },
    'ship_solaris-plus': {
        'hp': 950000, 'shield': 980000, 'speed': 530,
        'min_dmg': 68000, 'max_dmg': 95000, 'formation': 14,   # Drill
        'shield_absorb': 0.85,
    },
    'ship_tartarus-plus': {
        'hp': 880000, 'shield': 900000, 'speed': 570,
        'min_dmg': 64000, 'max_dmg': 90000, 'formation': 15,   # Wheel
        'shield_absorb': 0.85,
    },
    'ship_diminisher': {
        'hp': 850000, 'shield': 920000, 'speed': 530,
        'min_dmg': 66000, 'max_dmg': 96000, 'formation': 14,   # Drill
        'shield_absorb': 0.85,
    },
    'ship_sentinel': {
        'hp': 850000, 'shield': 1350000, 'speed': 530,
        'min_dmg': 60000, 'max_dmg': 88000, 'formation': 13,   # Ring
        'shield_absorb': 0.88,
    },
}

FORMATIONS = [12, 13, 14, 15, 19]  # Heart, Ring, Drill, Wheel, Star
DRONE_DESIGNS = [6, 6, 6, 2, 1]    # Spartan (çoğunluk), Hercules, Havoc

BOT_TITLES = [
    (1138, 'title_achievement_multi-dimensional-pilot'),
    (1149, 'title_achievement_pvp_destroy-player-2'),
    (1163, 'title_achievement_summerevent-2013-war-veteran-1'),
    (1136, 'title_achievement_misc_legacy_starbornecommander'),
    (1049, 'title_achievement_event_domination_reoccurring-hidden-hunter'),
    (1066, 'title_achievement_event_mwg-merc-elite'),
    (1094, 'title_achievement_springfight-2012-hunter'),
    (1147, 'title_achievement_playtime-pvpmap'),
]

CLAN_TAGS = ['WAR', 'EIC', 'VRU', 'MMO', 'PVP', 'ELITE', 'STAR', 'DARK', 'APEX', 'TITAN',
             'PRO', 'VOID', 'GHOST', 'STORM', 'VIP', 'RAID', 'CHAMP', 'ZONE', 'KRAK', 'SOL']

NAME_ROOTS = ['Phantom', 'Viper', 'Sniper', 'Destroyer', 'Nemesis', 'Kuzgun', 'Vortex',
              'Spectre', 'Titan', 'Apex', 'Chaos', 'Blaze', 'Storm', 'Nova', 'Draco',
              'Zephyr', 'Kartal', 'Asmodeus', 'Predator', 'Hunter', 'Ranger', 'Gladiator',
              'Warlord', 'Phoenix', 'Raven', 'Reaper', 'Ghost', 'Valkyrie', 'Centurion',
              'Commander', 'Striker', 'Fury', 'Avenger', 'Inferno', 'Eclipse', 'Shadow']


def random_bot_name():
    root = random.choice(NAME_ROOTS)
    style = random.choice(['clean', 'brackets', 'xx', 'star', 'underscore', 'dark', 'pro', 'suffix_tr', 'suffix_num'])
    if style == 'clean':
        return root
    elif style == 'brackets':
        return f"-[ {root} ]-"
    elif style == 'xx':
        return f"xX_{root}_Xx"
    elif style == 'star':
        return f"*{root}*"
    elif style == 'underscore':
        return f"_{root}_"
    elif style == 'dark':
        return f"Dark_{root}"
    elif style == 'pro':
        return f"[PRO] {root}"
    elif style == 'suffix_tr':
        return f"{root}_TR"
    elif style == 'suffix_num':
        return f"{root}_{random.choice(['01', '77', '99', 'Sniper', 'Hunter', 'Pro', 'X'])}"
    return root


class BotPlayer:
    def __init__(self, uid, name, clan_tag, clan_id, faction_id, ship_type, x, y):
        self.id = uid
        self.name = name
        self.clan_tag = clan_tag
        self.clan_id = clan_id
        self.faction_id = faction_id
        self.ship_type = ship_type
        
        cfg = BOT_SHIPS.get(ship_type, BOT_SHIPS['ship_goliath-plus'])
        diff = AY.carpan('bot_zorluk') if hasattr(AY, 'carpan') else 1.0
        
        self.max_hp = int(cfg['hp'] * diff)
        self.hp = self.max_hp
        self.max_shield = int(cfg['shield'] * diff)
        self.shield = self.max_shield
        self.speed = cfg['speed']
        self.min_dmg = int(cfg['min_dmg'] * diff)
        self.max_dmg = int(cfg['max_dmg'] * diff)
        self.laser_damage = (self.min_dmg + self.max_dmg) // 2
        self.laser_color = 3  # UCB-100 x4 beyaz lazer
        self.rocket_damage = int(random.randint(22000, 34000) * diff)
        self.launcher_damage = int(random.randint(48000, 72000) * diff)
        
        self.shield_absorb = cfg.get('shield_absorb', 0.85)
        self.has_heal = cfg.get('has_heal', False)
        self.used_heal = False
        self.used_ish = False
        self.invuln_until = 0.0
        self.shot_count = 0
        
        self.daily_rank = random.randint(15, 20)  # Albay, General, Chief General
        self.formation = cfg.get('formation', random.choice(FORMATIONS))
        self.drone_design = random.choice(DRONE_DESIGNS)
        self.drone_count = 10
        title = random.choice(BOT_TITLES)
        self.title_id = title[0]
        self.title_key = title[1]
        self.gg_done = random.randint(25, 120)
        
        from dunya import Mover
        self.mover = Mover(x, y)
        self.alive = True
        self.engaged = False
        self.target = None
        self.flee = False
        self.spread = random.uniform(-0.6, 0.6)
        self.keep = random.uniform(360, 480)
        self.next_think = time.time() + random.uniform(1.0, 3.0)
        self.next_shot = 0.0
        self.next_rocket = 0.0
        self.next_launcher = time.time() + random.uniform(4.0, 7.0)
        self.next_shield_regen = 0.0
        self.last_hit = 0.0
        self.last_combat = 0.0
        self.etki = DURUM.Etkiler()
        self.is_bot = True
        
        self.d = {
            'ad': f"{self.name} [{self.clan_tag}]",
            'hp': self.max_hp,
            'kalkan': self.max_shield,
            'hasar': self.laser_damage,
            'npc_kimlik': 0
        }
        
        self.cargo = {
            '1': random.randint(300, 500),
            '2': random.randint(300, 500),
            '3': random.randint(300, 500),
            '4': random.randint(80, 150),
            '5': random.randint(80, 150),
            '6': random.randint(50, 100),
            '7': random.randint(50, 120),  # Seprom
            '8': random.randint(40, 90)   # Palladium
        }
        
        self.reward = {
            'ep': random.randint(95000, 160000),
            'onur': random.randint(900, 1800),
            'kredi': random.randint(250000, 450000),
            'uridyum': random.randint(1800, 3500)
        }

    def drone_str(self):
        types = [2] * 8 + [3, 4]  # 8 Iris, 1 Apis, 1 Zeus
        return '|'.join(f'{t}|6|{self.drone_design}|0' for t in types)

    def create_msgs(self, now):
        x, y = self.mover.pos(now)
        create = ('ShipCreateCommand', dict(
            userId=self.id, typeId=self.ship_type, expansionStage=1,
            clanTag=self.clan_tag, userName=self.name, x=int(x), y=int(y),
            factionId=self.faction_id, clanId=self.clan_id, dailyRank=self.daily_rank,
            warnBox=False, clanDiplomacy=mod('ClanRelationModule', type=1),
            galaxyGatesDone=self.gg_done, useSystemFont=True, npc=False, cloaked=False,
            motherShipId=0, positionIndex=0, designSet='', modifier=[],
            minimapStrategyModule=mod('MinimapStrategyModule', minimapStrategy=0),
            specialNpcType=''))
        msgs = [create]
        if self.title_id and self.title_key:
            msgs.append(legacy(f'0|n|t|{self.id}|{self.title_id}|{self.title_key}'))
        msgs.append(legacy(f'0|n|d|{self.id}|{self.formation}|{self.drone_str()}'))
        msgs.append(('ShipUpgradeModuleUpdateCommand', dict(max=3, moduleTypeIds=[1, 2, 3], uid=self.id)))
        if self.mover.t1 > now:
            msgs.append(('MoveCommand', dict(userId=self.id, x=int(self.mover.x1), y=int(self.mover.y1), timeToTarget=int((self.mover.t1 - now) * 1000))))
        return msgs

    def selection_msg(self):
        return ('ShipSelectionCommand', dict(
            userId=self.id, shipType=0, shield=int(self.shield), shieldMax=int(self.max_shield),
            hitpoints=int(self.hp), hitpointsMax=int(self.max_hp), nanoHull=0, maxNanoHull=0,
            shieldSkill=False))

    def think(self, w, now):
        if not self.alive:
            return

        # Savaş dışında hızlı kalkan yenilenmesi
        if not self.engaged and now - self.last_hit > 6.0 and self.shield < self.max_shield:
            self.shield = min(self.max_shield, self.shield + self.max_shield * 0.04)

        # Savaş içinde kalkan jeneratörleri yenilenmesi (Elmas/Kalp formasyonu etkisi)
        if self.engaged and now >= self.next_shield_regen and self.shield < self.max_shield:
            self.next_shield_regen = now + 1.2
            self.shield = min(self.max_shield, self.shield + 12000)

        hx, hy = w.hero_pos(now)
        bx, by = self.mover.pos(now)
        dist = math.hypot(hx - bx, hy - by)
        hero_safe = w.in_peace(hx, hy) or w.hero_dead or w.jumping or w.gizli(now)

        if not self.engaged:
            # Oyuncuyu görünce saldırıya başlama (1200 birim menzil)
            if not hero_safe and dist < 1200 * AY.carpan('npc_fark') and not w.in_peace(bx, by):
                self.engaged = True
                self.target = w.hid
                self.next_think = now
                w.send([legacy(f'0|n|LSH|{w.hid}|{self.id}')])
            elif now >= self.next_think:
                # Rastgele haritada devriye gezme
                r = random.uniform(1000, 3000)
                a = random.uniform(0, 2 * math.pi)
                tx = min(max(bx + math.cos(a) * r, 600), w.map_w - 600)
                ty = min(max(by + math.sin(a) * r, 600), w.map_h - 600)
                if w.in_peace(tx, ty):
                    tx, ty = w.spot_away(hx, hy)
                ms = self.mover.go(tx, ty, self.speed * 0.8 * self.etki.speed_factor(now), now)
                w.send([('MoveCommand', dict(userId=self.id, x=int(tx), y=int(ty), timeToTarget=ms))])
                self.next_think = now + ms / 1000.0 + random.uniform(2.0, 4.0)
            return

        # Savaş durumunda
        if self.engaged:
            if hero_safe or dist > 2800:
                self.engaged = False
                self.target = None
                self.flee = True
                tx, ty = w.spot_away(hx, hy)
                ms = self.mover.go(tx, ty, self.speed, now)
                w.send([('MoveCommand', dict(userId=self.id, x=int(tx), y=int(ty), timeToTarget=ms))])
                self.next_think = now + ms / 1000.0 + random.uniform(3.0, 6.0)
                return

            # Oyuncuyu takip et / çevresinde agresif manevra yap
            if dist > 380 and now >= self.next_think and self.speed > 0:
                a = math.atan2(by - hy, bx - hx) + self.spread
                tx = min(max(hx + math.cos(a) * self.keep, 400), w.map_w - 400)
                ty = min(max(hy + math.sin(a) * self.keep, 400), w.map_h - 400)
                if not w.in_peace(tx, ty):
                    ms = self.mover.go(tx, ty, self.speed * self.etki.speed_factor(now), now)
                    w.send([('MoveCommand', dict(userId=self.id, x=int(tx), y=int(ty), timeToTarget=ms))])
                self.next_think = now + 0.65

            # Lazer atışı (her 1.0 sn): 2x x4 (UCB-100 beyaz) ardından 1x RSB-75 (yeşil/sarı burst) kombosu
            if dist <= 680 and now >= self.next_shot and not hero_safe and now >= w.invuln_until:
                self.next_shot = now + 1.0
                self.last_combat = now
                self.shot_count += 1
                
                is_rsb = (self.shot_count % 3 == 0)
                laser_color = 5 if is_rsb else 3  # 5 = RSB-75, 3 = UCB-100 x4
                
                laser_cmd = ('AttackLaserRunCommand', dict(
                    attackerId=self.id, targetId=w.hid, laserColor=laser_color,
                    isDiminishedBySkillShield=False, skilledLaser=is_rsb, visualType=0))
                
                hit = random.random() < AY.chance('npc_isabet', 0.90)
                if hit:
                    base_dmg = random.randint(self.min_dmg, self.max_dmg)
                    if is_rsb:
                        base_dmg = int(base_dmg * 1.85)  # RSB burst çarpanı
                    dmg = int(base_dmg * AY.carpan('npc_hasar'))
                    w.send(w.hurt_hero(dmg, killer=self, atype=1, msgs=[laser_cmd], now=now))
                else:
                    miss_cmd = ('AttackMissedCommand', dict(
                        attackType=mod('AttackTypeModule', attackTypeValue=1), targetUserId=w.hid, skillColorId=0))
                    w.send([laser_cmd, miss_cmd])

            # Ağır Roket atışı (PLT-3030 / PLT-2021, 2.5 - 3.5 sn bir)
            if dist <= 820 and now >= self.next_rocket and not hero_safe and now >= w.invuln_until:
                self.next_rocket = now + random.uniform(2.5, 3.5)
                self.last_combat = now
                r_type = random.choice([3, 4])  # PLT-2021 veya PLT-3030
                hit = random.random() < 0.90
                w.send([legacy(f'0|v|{self.id}|{w.hid}|{"H" if hit else "M"}|{r_type}|0|0')])
                if hit:
                    r_dmg = int(self.rocket_damage * random.uniform(0.9, 1.15) * AY.carpan('npc_hasar'))
                    w.later(0.8, lambda: w.send(w.hurt_hero(r_dmg, killer=self, atype=0)))
                else:
                    w.later(0.8, lambda: w.send([('AttackMissedCommand', dict(
                        attackType=mod('AttackTypeModule', attackTypeValue=0), targetUserId=w.hid, skillColorId=0))]))

            # Hellstorm Roketatar (HST-2) 5'li Salvo (her 6.5 - 8.5 sn bir)
            if dist <= 750 and now >= self.next_launcher and not hero_safe and now >= w.invuln_until:
                self.next_launcher = now + random.uniform(6.5, 8.5)
                self.last_combat = now
                hit = random.random() < 0.92
                hl_cmd = ('HellstormAttackCommand', dict(
                    attackerId=self.id, targetId=w.hid, hit=hit, currentLoad=5,
                    rocketType=mod('AmmunitionTypeModule', typeValue=21)  # HSTRM-01
                ))
                sound_cmd = legacy(f'0|RL|S|2|7|0')
                w.send([hl_cmd, sound_cmd])
                if hit:
                    hl_dmg = int(self.launcher_damage * random.uniform(0.9, 1.1) * AY.carpan('npc_hasar'))
                    w.later(0.9, lambda: w.send(w.hurt_hero(hl_dmg, killer=self, atype=0)))


def create_bot(w, hero_faction, uid=None):
    """Haritaya ve kahramana göre rakip firma seçerek yeni bir BotPlayer üretir."""
    rival_factions = [f for f in (1, 2, 3) if f != hero_faction] or [2]
    faction_id = random.choice(rival_factions)
    
    uid = uid or (BOT_UID_BASE + len(getattr(w, 'bots', {})) + random.randint(1, 9999))
    name = random_bot_name()
    clan_tag = random.choice(CLAN_TAGS)
    clan_id = 9100 + random.randint(1, 99)
    ship_type = random.choice(list(BOT_SHIPS.keys()))
    
    x, y = w.random_spot()
    return BotPlayer(uid, name, clan_tag, clan_id, faction_id, ship_type, x, y)
