"""Oyun içi komut sistemi: sohbet ve konsol komutları (!give, .give, give, !help).

NOT: İstemcinin yerleşik AChat kodu '/' ile başlayan komutları (ör: /give) yerel olarak
yakalayıp kendi yardım listesini ekrana basar ve sunucuya göndermez.
Bu nedenle oyun içi komutlar '!' veya '.' ile başlar (ör: !give veya .give) ya da doğrudan
'give' ile yazılabilir.

Kullanım:
  !give [oyuncu] <eşya> [adet]
  !give uridium 100000
  !give Regal 50000 uridium
  !give ul-nidhogg-solace-plus 5
  !give all x4 50000
  !help
"""
import json, os, re, shlex, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, 'data')

# Sık kullanılan eşya ve para kısayolları
ALIASES = {
    # Para / Puan
    'uridium': 'currency_uridium', 'uri': 'currency_uridium', 'u': 'currency_uridium',
    'credits': 'currency_credits', 'credit': 'currency_credits', 'kredi': 'currency_credits', 'c': 'currency_credits',
    'experience': 'currency_experience', 'exp': 'currency_experience', 'ep': 'currency_experience', 'xp': 'currency_experience',
    'honour': 'currency_honour', 'honor': 'currency_honour', 'onur': 'currency_honour',
    
    # Kapı / Log / Jeton
    'logdisk': 'resource_logfile', 'logdisks': 'resource_logfile', 'log_disk': 'resource_logfile', 'logfile': 'resource_logfile', 'log': 'resource_logfile',
    'extra_energy': 'resource_extra-energy', 'energy': 'resource_extra-energy', 'gg_energy': 'resource_extra-energy',
    'token': 'resource_collectable_armory-token', 'armory_token': 'resource_collectable_armory-token',
    'mega': 'resource_collectable_armory-token-mega', 'mega_token': 'resource_collectable_armory-token-mega', 'mega_armory_token': 'resource_collectable_armory-token-mega',
    
    # Anahtarlar
    'booty_key': 'resource_booty-key', 'key': 'resource_booty-key', 'green_key': 'resource_booty-key', 'bk-100': 'resource_booty-key',
    'red_key': 'resource_booty-key-red', 'bk-101': 'resource_booty-key-red',
    'blue_key': 'resource_booty-key-blue', 'bk-102': 'resource_booty-key-blue',
    'apocalypse_key': 'resource_booty-key-apocalypse',
    'blacklight_key': 'resource_booty-key-blacklight', 'prometheus_key': 'resource_booty-key-blacklight',
    
    # Lazerler
    'prometheus': 'equipment_weapon_laser_pr-l', 'prom': 'equipment_weapon_laser_pr-l', 'pr-l': 'equipment_weapon_laser_pr-l',
    'lf4': 'equipment_weapon_laser_lf-4', 'lf-4': 'equipment_weapon_laser_lf-4',
    'lf5': 'equipment_weapon_laser_lf-5', 'lf-5': 'equipment_weapon_laser_lf-5',
    'lf3': 'equipment_weapon_laser_lf-3', 'lf-3': 'equipment_weapon_laser_lf-3',
    'leg-nidhogg': 'equipment_weapon_cannon_leg-nidhogg', 'leg_nidhogg': 'equipment_weapon_cannon_leg-nidhogg',
    'ul-nidhogg': 'equipment_weapon_cannon_ul-nidhogg', 'ul_nidhogg': 'equipment_weapon_cannon_ul-nidhogg',
    
    # Kırıcılar (Cannon Shields - MR-C / MR-T)
    'mr-c01': 'equipment_cannon_shield_mr-c01', 'mrc01': 'equipment_cannon_shield_mr-c01',
    'mr-c02': 'equipment_cannon_shield_mr-c02', 'mrc02': 'equipment_cannon_shield_mr-c02',
    'mr-c03': 'equipment_cannon_shield_mr-c03', 'mrc03': 'equipment_cannon_shield_mr-c03',
    'mr-c04': 'equipment_cannon_shield_mr-c04', 'mrc04': 'equipment_cannon_shield_mr-c04',
    'mr-c05': 'equipment_cannon_shield_mr-c05', 'mrc05': 'equipment_cannon_shield_mr-c05',
    'mr-c06': 'equipment_cannon_shield_mr-c06', 'mrc06': 'equipment_cannon_shield_mr-c06',
    'mr-t01': 'equipment_cannon_shield_mr-t01', 'mrt01': 'equipment_cannon_shield_mr-t01',
    'mr-t02': 'equipment_cannon_shield_mr-t02', 'mrt02': 'equipment_cannon_shield_mr-t02',
    'mr-t03': 'equipment_cannon_shield_mr-t03', 'mrt03': 'equipment_cannon_shield_mr-t03',
    'mr-t04': 'equipment_cannon_shield_mr-t04', 'mrt04': 'equipment_cannon_shield_mr-t04',
    'mr-t05': 'equipment_cannon_shield_mr-t05', 'mrt05': 'equipment_cannon_shield_mr-t05',
    'mr-t06': 'equipment_cannon_shield_mr-t06', 'mrt06': 'equipment_cannon_shield_mr-t06',

    # Cephane
    'x4': 'ammunition_laser_ucb-100', 'ucb-100': 'ammunition_laser_ucb-100', 'ucb100': 'ammunition_laser_ucb-100',
    'rsb': 'ammunition_laser_rsb-75', 'rsb-75': 'ammunition_laser_rsb-75', 'rsb75': 'ammunition_laser_rsb-75',
    'a-bl': 'ammunition_laser_a-bl', 'abl': 'ammunition_laser_a-bl',
    'sab': 'ammunition_laser_sab-50', 'sab-50': 'ammunition_laser_sab-50',
    'x3': 'ammunition_laser_mcb-50', 'mcb-50': 'ammunition_laser_mcb-50',
    'x2': 'ammunition_laser_mcb-25', 'mcb-25': 'ammunition_laser_mcb-25',
    'x1': 'ammunition_laser_lcb-10', 'lcb-10': 'ammunition_laser_lcb-10',
    'plt-3030': 'ammunition_rocket_plt-3030', 'plt3030': 'ammunition_rocket_plt-3030',
    'plt-2021': 'ammunition_rocket_plt-2021', 'plt2021': 'ammunition_rocket_plt-2021',
    'plt-2026': 'ammunition_rocket_plt-2026', 'plt2026': 'ammunition_rocket_plt-2026',
    'emp': 'ammunition_specialammo_emp-01', 'emp-01': 'ammunition_specialammo_emp-01',
    'ish': 'ammunition_specialammo_ish-01', 'ish-01': 'ammunition_specialammo_ish-01',
    
    # Kalkan / Hız
    'b02': 'equipment_generator_shield_sg3n-b02', 'b-02': 'equipment_generator_shield_sg3n-b02',
    'b03': 'equipment_generator_shield_sg3n-b03', 'b-03': 'equipment_generator_shield_sg3n-b03',
    'fs-04': 'equipment_generator_shield_fs-04', 'fs04': 'equipment_generator_shield_fs-04',
    'speed': 'equipment_generator_speed_g3n-7900', 'g3n-7900': 'equipment_generator_speed_g3n-7900',
    
    # Dron ve Tasarımlar
    'hercules': 'drone_designs_hercules', 'havoc': 'drone_designs_havoc', 'spartan': 'drone_designs_spartan',
    'iris': 'drone_iris', 'apis': 'drone_apis', 'zeus': 'drone_zeus',
    
    # Kaynaklar
    'oil': 'resource_collectable_indoctrineoil', 'indoctrine_oil': 'resource_collectable_indoctrineoil',
    'diametrion': 'resource_collectable_diametrion',
    'ether_shard': 'resource_collectable_ether-shard', 'ether': 'resource_collectable_ether-shard',
    'axion': 'resource_collectable_axion-beam-regulator', 'abr': 'resource_collectable_axion-beam-regulator',
    'isochronate': 'resource_collectable_isochronate',
    
    # Gemiler
    'solace-plus': 'ship_solace-plus', 'solace_plus': 'ship_solace-plus',
    'goliath-plus': 'ship_goliath-plus', 'goliath_plus': 'ship_goliath-plus',
    'pusat-plus': 'ship_pusat-plus', 'pusat_plus': 'ship_pusat-plus',
    'citadel-plus': 'ship_citadel-plus', 'citadel_plus': 'ship_citadel-plus',
    'spectrum-plus': 'ship_spectrum-plus', 'spectrum_plus': 'ship_spectrum-plus',
    'solaris-plus': 'ship_solaris-plus', 'solaris_plus': 'ship_solaris-plus',
    'orcus': 'ship_orcus', 'cyborg': 'ship_cyborg', 'venom': 'ship_venom',
    'diminisher': 'ship_diminisher', 'solace': 'ship_solace', 'goliath': 'ship_goliath',

    # Sürücüler (Drives)
    'prime_drive': 'equipment_weapon_drive_igd-p',
    'prime-drive': 'equipment_weapon_drive_igd-p',
    'ignidrive_prime': 'equipment_weapon_drive_igd-p',
    'ignidrive-prime': 'equipment_weapon_drive_igd-p',
    'igd-p': 'equipment_weapon_drive_igd-p',
    'igd_p': 'equipment_weapon_drive_igd-p',
    'ignidrive_apex': 'equipment_weapon_drive_igd-l02',
    'apex_drive': 'equipment_weapon_drive_igd-l02',
    'igd-l02': 'equipment_weapon_drive_igd-l02',
    'ignidrive_lite': 'equipment_weapon_drive_igd-l01',
    'lite_drive': 'equipment_weapon_drive_igd-l01',
    'igd-l01': 'equipment_weapon_drive_igd-l01',

    # Mercekler (Lenses)
    'grav_lens_omega': 'equipment_lens_gl-omega',
    'grav-lens-omega': 'equipment_lens_gl-omega',
    'omega_lens': 'equipment_lens_gl-omega',
    'gl-omega': 'equipment_lens_gl-omega',
    'gl_omega': 'equipment_lens_gl-omega',
    'grav_lens_chron': 'equipment_lens_gl-chron',
    'chronotic_lens': 'equipment_lens_gl-chron',
    'gl-chron': 'equipment_lens_gl-chron',
    'gl_chron': 'equipment_lens_gl-chron',

    # Quantum Fluid Cores (QFC)
    'qfc_ax40': 'equipment_core_ax-40', 'qfc-ax40': 'equipment_core_ax-40',
    'qfc_ax_40': 'equipment_core_ax-40', 'qfc-ax-40': 'equipment_core_ax-40',
    'ax40': 'equipment_core_ax-40', 'ax-40': 'equipment_core_ax-40',
    'qfc_df40': 'equipment_core_df-40', 'qfc-df40': 'equipment_core_df-40',
    'qfc_df_40': 'equipment_core_df-40', 'qfc-df-40': 'equipment_core_df-40',
    'df40': 'equipment_core_df-40', 'df-40': 'equipment_core_df-40',
    'qfc_ax30': 'equipment_core_ax-30', 'qfc-ax30': 'equipment_core_ax-30',
    'ax30': 'equipment_core_ax-30', 'ax-30': 'equipment_core_ax-30',
    'qfc_df30': 'equipment_core_df-30', 'qfc-df30': 'equipment_core_df-30',
    'df30': 'equipment_core_df-30', 'df-30': 'equipment_core_df-30',
    'qfc_ax20': 'equipment_core_ax-20', 'qfc-ax20': 'equipment_core_ax-20',
    'ax20': 'equipment_core_ax-20', 'ax-20': 'equipment_core_ax-20',
    'qfc_df20': 'equipment_core_df-20', 'qfc-df20': 'equipment_core_df-20',
    'df20': 'equipment_core_df-20', 'df-20': 'equipment_core_df-20',
    'qfc_ax10': 'equipment_core_ax-10', 'qfc-ax10': 'equipment_core_ax-10',
    'ax10': 'equipment_core_ax-10', 'ax-10': 'equipment_core_ax-10',
    'qfc_df10': 'equipment_core_df-10', 'qfc-df10': 'equipment_core_df-10',
    'df10': 'equipment_core_df-10', 'df-10': 'equipment_core_df-10',
    'luminaflux': 'resource_collectable_luminaflux-alloy', 'lumi': 'resource_collectable_luminaflux-alloy',

    # CPU'lar (Ekstralar)
    'auto_particle_cannon_cpu': 'equipment_extra_cpu_rg-sl',
    'auto_particle_cannon': 'equipment_extra_cpu_rg-sl',
    'particle_cannon_cpu': 'equipment_extra_cpu_rg-sl',
    'auto_cannon_cpu': 'equipment_extra_cpu_rg-sl',
    'auto_cannon': 'equipment_extra_cpu_rg-sl',
    'rg-sl': 'equipment_extra_cpu_rg-sl', 'rg_sl': 'equipment_extra_cpu_rg-sl',
    'auto_singularity_drive_cpu': 'equipment_extra_cpu_ags-x',
    'auto_singularity_drive': 'equipment_extra_cpu_ags-x',
    'singularity_drive_cpu': 'equipment_extra_cpu_ags-x',
    'auto_drive_cpu': 'equipment_extra_cpu_ags-x',
    'auto_drive': 'equipment_extra_cpu_ags-x',
    'ags-x': 'equipment_extra_cpu_ags-x', 'ags_x': 'equipment_extra_cpu_ags-x',
    'auto_rocket_cpu': 'equipment_extra_cpu_arol-x', 'arol-x': 'equipment_extra_cpu_arol-x', 'arol_x': 'equipment_extra_cpu_arol-x',
    'auto_launcher_cpu': 'equipment_extra_cpu_rllb-x', 'rllb-x': 'equipment_extra_cpu_rllb-x', 'rllb_x': 'equipment_extra_cpu_rllb-x',
    'jump_cpu': 'equipment_extra_cpu_ajp-01', 'ajp-01': 'equipment_extra_cpu_ajp-01',
    'cloak_cpu': 'equipment_extra_cpu_cl04k-xl', 'cloak': 'equipment_extra_cpu_cl04k-xl'
}

_ALL_LOOTS = None


def get_all_loots():
    """Oyundaki bilinen bütün eşya kimlikleri."""
    global _ALL_LOOTS
    if _ALL_LOOTS is not None:
        return _ALL_LOOTS
    loots = set(ALIASES.values())
    for fname in ('esyalar.json', 'istemci_esyalari.json', 'parcacik.json', 'fiyatlar.json'):
        fpath = os.path.join(DATA, fname)
        if not os.path.exists(fpath):
            continue
        try:
            with open(fpath, encoding='utf8') as f:
                d = json.load(f)
            if isinstance(d, dict):
                for k, v in d.items():
                    if isinstance(v, dict):
                        loots.update(str(x) for x in v.keys())
                    elif isinstance(v, list):
                        loots.update(str(x) for x in v if isinstance(x, str))
                if 'esyalar' in d and isinstance(d['esyalar'], dict):
                    loots.update(d['esyalar'].keys())
                if 'toplar' in d and isinstance(d['toplar'], dict):
                    loots.update(d['toplar'].keys())
        except Exception:
            pass
    _ALL_LOOTS = loots
    return _ALL_LOOTS


def resolve_item(query):
    """Kullanıcının yazdığı metni geçerli bir lootId'ye çözümler."""
    if not query:
        return None
    q = query.strip()
    q_low = q.lower()
    q_norm = q_low.replace('-', '_').replace(' ', '_')
    
    # 1. Doğrudan kısayollar
    if q_low in ALIASES:
        return ALIASES[q_low]
    if q_norm in ALIASES:
        return ALIASES[q_norm]
    
    loots = get_all_loots()
    
    # 2. Birebir eşleşme
    for l in loots:
        if l.lower() == q_low:
            return l
            
    # 3. Yaygın ön ekleri deneyerek eşleştirme
    prefixes = [
        'equipment_core_',
        'equipment_lens_', 'equipment_weapon_drive_',
        'equipment_cannon_shield_',
        'equipment_weapon_cannon_', 'equipment_weapon_laser_', 'resource_collectable_',
        'resource_', 'ammunition_laser_', 'ammunition_rocket_', 'ammunition_specialammo_',
        'equipment_generator_shield_', 'equipment_generator_speed_', 'drone_designs_',
        'ship_', 'currency_'
    ]
    for pre in prefixes:
        cand = pre + q_low
        for l in loots:
            if l.lower() == cand:
                return l
                
    # 4. Alt çizgi / tire eşitleme
    q_norm = q_low.replace('-', '_').replace(' ', '_')
    for l in loots:
        if l.lower().replace('-', '_') == q_norm:
            return l
    for pre in prefixes:
        cand_norm = pre + q_norm
        for l in loots:
            if l.lower().replace('-', '_') == cand_norm:
                return l

    # 5. İçerme / arama fallback
    matches = [l for l in loots if q_norm in l.lower().replace('-', '_')]
    if matches:
        return sorted(matches, key=len)[0]
        
    return None


def resolve_ship(query):
    """Gemi adını ya da kısaltmasını ship_... lootId'sine dönüştürür."""
    if not query:
        return None
    q = str(query).lower().strip().replace('_', '-')
    # 1. Alias lookup
    for name, loot in ALIASES.items():
        if loot.startswith('ship_'):
            if q == name.replace('_', '-') or q == loot.replace('_', '-') or q == loot.replace('ship_', '').replace('_', '-'):
                return loot
    # 2. Known loots lookup
    for l in get_all_loots():
        if l.startswith('ship_'):
            l_norm = l.lower().replace('_', '-')
            if q == l_norm or q == l_norm.replace('ship-', ''):
                return l
    return None


def find_online_session(oyun, name_or_id):
    """Çevrimiçi oturumu bulur (kullanıcı adı ya da userId)."""
    if not oyun or not hasattr(oyun, 'OTURUMLAR'):
        return None
    target = str(name_or_id).lower()
    for s in list(oyun.OTURUMLAR):
        pr = getattr(s, 'profil', None)
        if not pr:
            continue
        user_name = (pr.d.get('pilot', {}).get('userName') or '').lower()
        user_id = str(pr.user_id)
        if user_name == target or user_id == target:
            return s
    return None


def get_all_usernames(oyun):
    """Bütün bilinen çevrimiçi ve çevrimdışı kullanıcı adları."""
    users = set()
    if oyun and hasattr(oyun, 'OTURUMLAR'):
        for s in list(oyun.OTURUMLAR):
            pr = getattr(s, 'profil', None)
            if pr:
                u = pr.d.get('pilot', {}).get('userName')
                if u:
                    users.add(u)
    # Çevrimdışı yuvalar
    import yollar
    if os.path.isdir(yollar.KAYITLAR):
        for slot in os.listdir(yollar.KAYITLAR):
            p_file = os.path.join(yollar.KAYITLAR, slot, 'profil.json')
            if os.path.isfile(p_file):
                try:
                    with open(p_file, encoding='utf8') as f:
                        d = json.load(f)
                    u = d.get('pilot', {}).get('userName')
                    if u:
                        users.add(u)
                except Exception:
                    pass
    return sorted(users)


def reward_offline_user(username_or_slot, loot_id, amount, ship=None):
    """Çevrimdışı oyuncunun profiline eşyayı ekleyip kaydeder."""
    import yollar
    from profil import Profil
    from magaza import Magaza
    import kapi as KAPI
    import yeni_sistemler as YS
    
    target = username_or_slot.lower()
    slot_path = None
    if os.path.isdir(yollar.KAYITLAR):
        for slot in os.listdir(yollar.KAYITLAR):
            p_file = os.path.join(yollar.KAYITLAR, slot, 'profil.json')
            if os.path.isfile(p_file):
                try:
                    with open(p_file, encoding='utf8') as f:
                        d = json.load(f)
                    u = (d.get('pilot', {}).get('userName') or '').lower()
                    if u == target or slot.lower() == target:
                        slot_path = p_file
                        break
                except Exception:
                    pass
    if not slot_path:
        return False, f"User '{username_or_slot}' not found in saved profiles."
        
    try:
        with open(yollar.sablon('giris.json'), encoding='utf8') as f:
            tohum = json.load(f).get('tohum')
        with open(yollar.sablon('yanitlar.json'), encoding='utf8') as f:
            yanitlar = json.load(f)
        notes = []
        pr = Profil(tohum, slot_path)
        m = Magaza(pr, yanitlar, notes.append)
        m.kapilar = KAPI.Kapilar(pr, notes.append)
        m.yeni = YS.YeniSistemler(pr, m, notes.append)
        
        ship_to_use = ship
        if not ship_to_use:
            try:
                ship_to_use = pr.ship()['lootId']
            except Exception:
                ship_to_use = 'ship_solace'

        if loot_id.startswith('equipment_core_'):
            for _ in range(amount):
                m.yeni.qfc.create(loot_id, ship=ship_to_use)
        else:
            m.reward(loot_id, amount, ship=ship_to_use)
            
        pr.save(force=True)
        return True, f"Granted {amount:,}x {loot_id} (ship: {ship_to_use}) to offline player '{pr.d['pilot'].get('userName', username_or_slot)}' (saved)."
    except Exception as e:
        return False, f"Error saving to offline profile: {e}"


def parse_give_command(cmd_text, sender, online_users, all_users):
    """Komut satırını hedefe, eşyaya, adede ve hedef gemiye ayrıştırır."""
    try:
        parts = shlex.split(cmd_text)[1:]
    except Exception:
        parts = cmd_text.split()[1:]
        
    if not parts:
        return None, None, None, None, (
            "Usage: !give [player] <item> [amount] [ship]\n"
            "Examples:\n"
            "- !give qfc-ax40 solace\n"
            "- !give qfc-df40 solace\n"
            "- !give uridium 100000\n"
            "- !give Regal 50000 uridium\n"
            "- !give ul-nidhogg-solace-plus 5"
        )
        
    target = None
    # 1. 'all' ya da '*' kontrolü
    if parts[0].lower() in ('all', '*', 'herkes'):
        target = 'all'
        parts = parts[1:]
    else:
        # 2. İlk argüman bilinen kullanıcı adı mı?
        match_first = next((u for u in all_users if u.lower() == parts[0].lower()), None)
        if match_first:
            target = match_first
            parts = parts[1:]
        elif len(parts) > 1:
            # 3. Son argüman bilinen kullanıcı adı mı? (ör: !give uridium 50000 Regal)
            match_last = next((u for u in all_users if u.lower() == parts[-1].lower()), None)
            if match_last:
                target = match_last
                parts = parts[:-1]
                
    if not target:
        target = sender

    if not parts:
        return None, None, None, None, "Missing item name. Usage: !give [player] <item> [amount] [ship]"

    amount = 1
    tokens = []
    for p in parts:
        clean = p.rstrip('xX').replace(',', '').replace('.', '')
        if clean.isdigit():
            amount = max(1, min(2_000_000_000, int(clean)))
        else:
            tokens.append(p)
            
    if not tokens:
        return None, None, None, None, "Missing item name. Usage: !give [player] <item> [amount] [ship]"

    target_ship = None
    # Birden fazla token varsa, biri gemi adı/kısaltması mı?
    if len(tokens) > 1:
        for i, t in enumerate(tokens):
            s_cand = resolve_ship(t)
            if s_cand:
                rem = tokens[:i] + tokens[i+1:]
                rem_query = ' '.join(rem)
                rem_item = resolve_item(rem_query)
                if rem_item:
                    target_ship = s_cand
                    tokens = rem
                    break

    item_query = ' '.join(tokens)
    
    # Tek token kontrolü (ör: qfc-ax40-solace)
    if not target_ship and len(tokens) == 1 and ('-' in tokens[0] or '_' in tokens[0]):
        tok = tokens[0]
        parts_tok = tok.replace('_', '-').rsplit('-', 1)
        if len(parts_tok) == 2:
            s_cand = resolve_ship(parts_tok[1])
            i_cand = resolve_item(parts_tok[0])
            if s_cand and i_cand and i_cand.startswith('equipment_core_'):
                target_ship = s_cand
                item_query = parts_tok[0]

    return target, item_query, amount, target_ship, "OK"


def execute_give(target, item_query, amount, sender, oyun=None, target_ship=None):
    """Eşyayı çözümler ve hedefe (çevrimiçi ya da çevrimdışı) verir."""
    loot_id = resolve_item(item_query)
    if not loot_id:
        return f"Item '{item_query}' could not be found. Check the name or lootId. Type !give for help."

    # Herkese verme (all)
    if target == 'all':
        if not oyun or not hasattr(oyun, 'OTURUMLAR'):
            return "No game server instance available for 'all'."
        sessions = [s for s in list(oyun.OTURUMLAR) if getattr(s, 'profil', None) is not None]
        if not sessions:
            return "No players are currently online."
        for s in sessions:
            ship_to_use = target_ship or (s.profil.ship()['lootId'] if callable(getattr(s.profil, 'ship', None)) else 'ship_solace')
            if loot_id.startswith('equipment_core_'):
                msgs = []
                for _ in range(amount):
                    iid = s.magaza.yeni.qfc.create(loot_id, ship=ship_to_use)
                    if s.magaza:
                        msgs += [s.magaza.inv_item(iid, loot_id, 1), s.magaza.pack([s.magaza.hangar_item(iid, loot_id, 1)])]
                from eski_protokol import legacy
                msgs += [legacy('0|LM|ST|LOT|%s|%d' % (loot_id, amount)), s.magaza.yeni.qfc.list_cmd()]
                s.send(msgs, quiet=True)
            else:
                msgs = s.magaza.reward(loot_id, amount, ship=ship_to_use)
                s.send(list(msgs or []) + s.magaza.money_msgs(), quiet=True)
            s.profil.save()
        return f"Granted {amount:,}x {loot_id} to all online players ({len(sessions)} players)."

    # Tek oyuncuya verme
    # 1. Çevrimiçi oturum
    s = find_online_session(oyun, target)
    if s:
        target_name = s.profil.d.get('pilot', {}).get('userName', target)
        ship_to_use = target_ship
        if not ship_to_use:
            try:
                ship_to_use = s.profil.ship()['lootId']
            except Exception:
                ship_to_use = 'ship_solace'

        if loot_id.startswith('equipment_core_'):
            msgs = []
            for _ in range(amount):
                iid = s.magaza.yeni.qfc.create(loot_id, ship=ship_to_use)
                if s.magaza:
                    msgs += [s.magaza.inv_item(iid, loot_id, 1), s.magaza.pack([s.magaza.hangar_item(iid, loot_id, 1)])]
            from eski_protokol import legacy
            msgs += [legacy('0|LM|ST|LOT|%s|%d' % (loot_id, amount)), s.magaza.yeni.qfc.list_cmd()]
            s.send(msgs, quiet=True)
            s.profil.save()
            if target_name.lower() != str(sender).lower() and hasattr(oyun, 'SOHBET') and oyun.SOHBET:
                oyun.SOHBET.duyuru(f"{sender} gave you {amount:,}x {loot_id} bound to {ship_to_use}!", kim=str(s.profil.user_id))
            return f"Successfully granted {amount:,}x {loot_id} bound to {ship_to_use} to {target_name}."

        msgs = s.magaza.reward(loot_id, amount, ship=ship_to_use)
        s.send(list(msgs or []) + s.magaza.money_msgs(), quiet=True)
        s.profil.save()
        if target_name.lower() != str(sender).lower() and hasattr(oyun, 'SOHBET') and oyun.SOHBET:
            oyun.SOHBET.duyuru(f"{sender} gave you {amount:,}x {loot_id}!", kim=str(s.profil.user_id))
        return f"Successfully granted {amount:,}x {loot_id} to {target_name}."

    # 2. Çevrimdışı profil
    ok, msg = reward_offline_user(target, loot_id, amount, ship=target_ship)
    return msg


def apply_live_patches():
    """Çalışan dunya modülünü canlı olarak yamalar."""
    try:
        dunya = sys.modules.get('dunya')
        if not dunya or not hasattr(dunya, 'Dunya'):
            return
        
        # 1. shared_view yaması
        def patched_shared_view(self, now, hx, hy):
            msgs = []
            for uid in [u for u in list(self.visible) if u not in self.npcs and u not in getattr(self, 'bots', {})]:
                self.visible.discard(uid)
                if self.target == uid:
                    self.target, self.attacking = None, False
                    msgs.append(('ShipDeselectionCommand', {}))
                msgs.append(('ShipRemoveCommand', {'userId': uid}))
            msgs += [('RemoveCollectableCommand', {'collected': False, 'hash': h}) for h in list(self.seen_items)
                     if h not in self.boxes and h not in self.ores]
            lim = self.abilities.view_factor(now)
            msgs += self.ortak.gorunurluk(self, now, hx, hy, dunya.SAVAS['gorus_mesafesi'] * lim, dunya.SAVAS['gorus_birakma'] * lim)
            if self.secim is not None and self.target == self.secim[1]['userId']:
                w = self.oyuncu(self.target)
                if w is None:
                    self.target, self.attacking, self.secim = None, False, None
                    msgs.append(('ShipDeselectionCommand', {}))
                elif self.oyuncu_secimi(w) != self.secim:
                    self.secim = self.oyuncu_secimi(w)
                    msgs.append(self.secim)
            return msgs

        # 2. kill_bot yaması
        def patched_kill_bot(self, b):
            b.alive = False
            self.bots.pop(b.id, None)
            self.visible.discard(b.id)
            x, y = b.mover.pos(time.time())
            msgs = []
            if self.pet:
                msgs += self.pet.npc_gone(b.id)
            msgs.append(('ShipDestroyedCommand', dict(destroyedUserId=b.id, explosionTypeId=0)))
            if self.target == b.id:
                self.target, self.attacking = None, False
                msgs.append(('ShipDeselectionCommand', {}))
            msgs.append(('ShipRemoveCommand', {'userId': b.id}))

            self.drop_box('FROM_SHIP', x, y, b.cargo, 180)

            form = self.p.mods()
            ep = int(b.reward['ep'] * dunya.AY.carpan('ep') * (1 + form.get('ep', 0)))
            onur = int(b.reward['onur'] * dunya.AY.carpan('onur') * (1 + form.get('onur', 0)))
            kredi = int(b.reward['kredi'] * dunya.AY.carpan('kredi') * (1 + form.get('kredi', 0)))
            uridyum = int(b.reward['uridyum'] * dunya.AY.carpan('uridyum'))

            tot = self.p.gain(ep=ep, onur=onur, kredi=kredi, uridyum=uridyum, neden='bonus_abschussPlayer')
            msgs += self.reward_msgs(tot, ep=ep, onur=onur, kredi=kredi, uridyum=uridyum)
            if self.pet:
                msgs += self.pet.gain_xp(ep)

            msgs += (self.quest('kill_player', faction=b.faction_id, ship=b.ship_type) +
                     self.quest('kill', avatar='PLAYER', faction=b.faction_id, ship=b.ship_type))
            self.p.ach('destroy_player', faction=b.faction_id)
            hero_fac = getattr(self.p, 'faction_id', 1) or 1
            self.schedule(random.uniform(30.0, 60.0), 'bot', hero_fac)
            return msgs

        # 3. kill (regular NPCs) yaması
        def patched_kill(self, n):
            n.alive = False
            self.npcs.pop(n.id, None)
            x, y = n.mover.pos(time.time())
            msgs = []
            pet_stop = self.pet.npc_gone(n.id) if self.pet else []
            if n.d.get('sayilmaz'):
                if n.id in self.visible:
                    self.visible.discard(n.id)
                    msgs += [('ShipDestroyedCommand', dict(destroyedUserId=n.id, explosionTypeId=0)), ('ShipRemoveCommand', {'userId': n.id})]
                if self.target == n.id:
                    self.target, self.attacking = None, False
                    msgs.append(('ShipDeselectionCommand', {}))
                return pet_stop + msgs + self.alien.on_kill(n, x, y)
            if n.id in self.visible:
                self.visible.discard(n.id)
                msgs.append(('ShipDestroyedCommand', dict(destroyedUserId=n.id, explosionTypeId=0)))
            if self.target == n.id:
                self.target, self.attacking = None, False
                msgs.append(('ShipDeselectionCommand', {}))
            msgs.append(('ShipRemoveCommand', {'userId': n.id}))
            msgs = pet_stop + msgs
            self.ofke.kill(self.lasers(), time.time())
            pay = self.paydaslar()
            for w in pay:
                w.npc_reward(n, x, y, len(pay), own=w is self)
            for sp in n.davranis.get('olunce_dogur', []):
                for k in range(sp.get('adet', 1)):
                    a = 2 * math.pi * k / max(1, sp.get('adet', 1))
                    c = self.spawn_npc_at(sp['tur'], x + math.cos(a) * 120, y + math.sin(a) * 120)
                    self.alien.adopt(n, c)
                    c.engaged = n.engaged
            if not n.gate and not n.summoned:
                self.schedule(random.uniform(*self.respawn_range(n)), 'npc', n.tip)
            self.drifter_killed(n)
            return msgs + self.alien.on_kill(n, x, y) + self.etkinlik.on_kill(n, x, y, w=self, pay=pay) + \
                (self.labirent.on_kill(n, x, y) if self.labirent else [])

        # 4. hero_effect, effects_tick, npc_effect (slow/freeze debuff visual and timer)
        def patched_hero_effect(self, kind, sec, value=1.0, source=None):
            e = self.hero_etki.add(kind, sec, value, source)
            msgs = []
            if kind in ('yavas', 'hiz_siniri'):
                ms = int(sec * 1000)
                msgs.append(dunya.legacy('0|n|fx|start|SABOTEUR_DEBUFF|%d' % self.hid))
                msgs.append(('MenuItemCooldownGroupTimerCommand', dict(
                    timerState=dunya.mod('TimerStateModule', timerStateValue=2),
                    cooldownType=dunya.mod('CooldownTypeModule', typeValue=42),
                    maxTime=ms, time=ms)))
                if self.ortak is not None and len(self.ortak.uyeler) > 1:
                    self.ortak.yansit(self, [dunya.legacy('0|n|fx|start|SABOTEUR_DEBUFF|%d' % self.hid)])
            elif kind == 'donuk':
                ms = int(sec * 1000)
                msgs.append(dunya.legacy('0|n|fx|start|ICY_CUBE|%d' % self.hid))
                msgs.append(('MenuItemCooldownGroupTimerCommand', dict(
                    timerState=dunya.mod('TimerStateModule', timerStateValue=2),
                    cooldownType=dunya.mod('CooldownTypeModule', typeValue=49),
                    maxTime=ms, time=ms)))
                if self.ortak is not None and len(self.ortak.uyeler) > 1:
                    self.ortak.yansit(self, [dunya.legacy('0|n|fx|start|ICY_CUBE|%d' % self.hid)])
            if kind in ('yavas', 'donuk', 'hizlanma', 'hiz_siniri') and self.stats_msgs:
                msgs.extend(self.stats_msgs())
            if msgs:
                self.send(msgs)
            return e

        def patched_effects_tick(self, now):
            for n in list(self.npcs.values()):
                if not self.sahibi(n, now):
                    continue
                if n.alive and n.etki.d:
                    for dmg in n.etki.poison_due(now):
                        self.hit_npc(n.id, dmg, 1, hull_only=True)
                    exp = n.etki.expired(now)
                    if 'yavas' in exp and not n.etki.get('yavas'):
                        fx_end = [dunya.legacy('0|n|fx|end|SABOTEUR_DEBUFF|%d' % n.id)]
                        self.send(fx_end)
                        if self.ortak is not None and len(self.ortak.uyeler) > 1:
                            self.ortak.yansit(self, fx_end)
                    if 'donuk' in exp and not n.etki.get('donuk'):
                        fx_end = [dunya.legacy('0|n|fx|end|ICY_CUBE|%d' % n.id)]
                        self.send(fx_end)
                        if self.ortak is not None and len(self.ortak.uyeler) > 1:
                            self.ortak.yansit(self, fx_end)
                if n.alive and 'yenilenme' in n.davranis:
                    self.npc_regen(n, now)
            if self.hero_etki.d:
                exp = self.hero_etki.expired(now)
                msgs = []
                if exp & {'yavas', 'hiz_siniri'} and not (self.hero_etki.get('yavas') or self.hero_etki.get('hiz_siniri')):
                    msgs.append(dunya.legacy('0|n|fx|end|SABOTEUR_DEBUFF|%d' % self.hid))
                    msgs.append(('MenuItemCooldownGroupTimerCommand', dict(
                        timerState=dunya.mod('TimerStateModule', timerStateValue=0),
                        cooldownType=dunya.mod('CooldownTypeModule', typeValue=42),
                        maxTime=0, time=0)))
                    if self.ortak is not None and len(self.ortak.uyeler) > 1:
                        self.ortak.yansit(self, [dunya.legacy('0|n|fx|end|SABOTEUR_DEBUFF|%d' % self.hid)])
                if 'donuk' in exp and not self.hero_etki.get('donuk'):
                    msgs.append(dunya.legacy('0|n|fx|end|ICY_CUBE|%d' % self.hid))
                    msgs.append(('MenuItemCooldownGroupTimerCommand', dict(
                        timerState=dunya.mod('TimerStateModule', timerStateValue=0),
                        cooldownType=dunya.mod('CooldownTypeModule', typeValue=49),
                        maxTime=0, time=0)))
                    if self.ortak is not None and len(self.ortak.uyeler) > 1:
                        self.ortak.yansit(self, [dunya.legacy('0|n|fx|end|ICY_CUBE|%d' % self.hid)])
                if exp & {'yavas', 'donuk', 'hizlanma', 'hiz_siniri', 'zayiflik'} and self.stats_msgs:
                    msgs.extend(self.stats_msgs())
                if msgs:
                    self.send(msgs)

        def patched_npc_effect(self, n, kind, sec, value=1.0, source=None, **extra):
            now = time.time()
            e = n.etki.add(kind, sec, value, source, now, **extra)
            if kind in ('donuk', 'yavas') and n.mover.t1 > now:
                x, y = n.mover.pos(now)
                n.mover = dunya.Mover(x, y)
                n.next_think = now if kind == 'yavas' else now + sec
                if n.id in self.visible:
                    self.send([('MoveCommand', dict(userId=n.id, x=int(x), y=int(y), timeToTarget=0))])
            if kind == 'yavas':
                fx_start = [dunya.legacy('0|n|fx|start|SABOTEUR_DEBUFF|%d' % n.id)]
                self.send(fx_start)
                if self.ortak is not None and len(self.ortak.uyeler) > 1:
                    self.ortak.yansit(self, fx_start)
            elif kind == 'donuk':
                fx_start = [dunya.legacy('0|n|fx|start|ICY_CUBE|%d' % n.id)]
                self.send(fx_start)
                if self.ortak is not None and len(self.ortak.uyeler) > 1:
                    self.ortak.yansit(self, fx_start)
            return e

        dunya.Dunya.shared_view = patched_shared_view
        dunya.Dunya.kill_bot = patched_kill_bot
        dunya.Dunya.kill = patched_kill
        dunya.Dunya.hero_effect = patched_hero_effect
        dunya.Dunya.effects_tick = patched_effects_tick
        dunya.Dunya.npc_effect = patched_npc_effect

        # 5. CBS & Dunya live patches
        cbs_mod = sys.modules.get('cbs')
        if cbs_mod:
            if hasattr(cbs_mod, 'D') and 'rakip' in cbs_mod.D:
                cbs_mod.D['rakip']['hasar_carpani'] = 1.0
                cbs_mod.D['rakip']['deflector_prime_disinda'] = False

            def patched_rival_attackable(self, aid):
                a = self.ast(aid)
                if a.get('sahip') != 'rakip' or a.get('durum') != 'kurulu':
                    return False
                return True

            def patched_asset_attackable(self, uid):
                aid, slot = self.asset_slot(uid)
                if aid is not None and self.rival_attackable(aid):
                    return []
                return [dunya.legacy('0|A|STM|msg_station_not_atackable')]

            def patched_asset_select(self, uid):
                aid, slot = self.asset_slot(uid)
                if aid is None:
                    return []
                a = self.ast(aid)
                y = a.get('yuvalar', {}).get(str(slot))
                if not y:
                    return []
                mh = y.get('azami') or cbs_mod.level_value(cbs_mod.MODS[y['loot']]['can'], y['seviye'])
                return [('ShipSelectionCommand', dict(userId=int(uid), shipType=0, shield=int(y['kalkan']), shieldMax=int(mh * cbs_mod.D['kalkan_orani']),
                                                      hitpoints=int(y['can']), hitpointsMax=int(mh), nanoHull=0, maxNanoHull=0, shieldSkill=False)),
                        self.info_cmd(aid, slot, y)]

            def patched_asset_hit(self, uid, dmg):
                aid, slot = self.asset_slot(uid)
                if aid is None:
                    return []
                a = self.ast(aid)
                a['saldiri'] = time.time()
                msgs = self.damage_module(aid, slot, dmg, self.clan_name())
                b = self.ast(aid)
                y = b.get('yuvalar', {}).get(str(slot)) if b.get('sahip') == 'rakip' else None
                if y:
                    msgs.append(('AttackHitAssetCommand', dict(assetId=int(uid), hitpointsNow=int(y['can']),
                                                               hitpointsMax=int(y.get('azami') or cbs_mod.level_value(cbs_mod.MODS[y['loot']]['can'], y['seviye'])))))
                    if self.world:
                        msgs.append(('AttackHitCommand', dict(
                            attackType=dunya.attack_type(1), attackerId=self.world.hid, victimId=int(uid),
                            victimHitpoints=int(y['can']), victimShield=int(y['kalkan']), victimNanoHull=0,
                            damage=int(dmg), skilled=True, strike=False, cannonType=0)))
                return msgs

            def patched_rival_fire(self, now):
                w = self.world
                if not w or w.hero_dead or getattr(w, 'jumping', False):
                    return []
                hx, hy = w.hero_pos(now)
                by_map = getattr(cbs_mod, 'BY_MAP', {})
                mods = getattr(cbs_mod, 'MODS', {})
                cfg_d = getattr(cbs_mod, 'D', {})
                import ayar as AY_MOD
                cbs_hasar_mult = AY_MOD.carpan('cbs_hasar') if hasattr(AY_MOD, 'carpan') else 1.0
                for aid in by_map.get(int(w.map_id), []):
                    a = self.ast(aid)
                    if a.get('sahip') != 'rakip' or a.get('durum') != 'kurulu':
                        continue
                    for s, y in list(a['yuvalar'].items()):
                        md = mods.get(y['loot'], {})
                        if not md.get('silah') or y['can'] <= 0 or w.hero_dead:
                            continue
                        sx, sy = cbs_mod.satellite_pos(aid, int(s))
                        key = ('rakip', aid, int(s))
                        if math.hypot(sx - hx, sy - hy) > md['menzil'] or now < self.next_shot.get(key, 0):
                            continue
                        self.next_shot[key] = now + md['aralik_sn']
                        uid = cbs_mod.asset_id(aid, int(s))
                        hit = random.random() < md['isabet']
                        if md.get('silah') == 'roket':
                            w.send([dunya.legacy('0|v|%d|%d|%s|1|0|0' % (uid, w.hid, 'H' if hit else 'M'))])
                        else:
                            w.send([('AttackLaserRunCommand', dict(attackerId=uid, targetId=w.hid, laserColor=0, isDiminishedBySkillShield=False,
                                                                   skilledLaser=False, visualType=0))])
                        if hit:
                            lvl_val = cbs_mod.level_value(md['hasar'], y['seviye'])
                            dmg = int(lvl_val * cfg_d['rakip'].get('hasar_carpani', 1.0) * cbs_hasar_mult)
                            import types
                            who = types.SimpleNamespace(id=uid, alive=False, d={'ad': '%s [%s]' % (md['kod'], a.get('rakip', ''))})
                            w.send(w.hurt_hero(dmg, killer=who, cause=cbs_mod.DESTRUCTION_BATTLESTATION, now=now))
                        else:
                            w.send([('AttackMissedCommand', dict(attackType=dunya.attack_type(1 if md.get('silah') != 'roket' else 0), targetUserId=w.hid, skillColorId=0))])
                return []

            cbs_mod.Cbs.rival_attackable = patched_rival_attackable
            cbs_mod.Cbs.asset_attackable = patched_asset_attackable
            cbs_mod.Cbs.asset_select = patched_asset_select
            cbs_mod.Cbs.asset_hit = patched_asset_hit
            cbs_mod.Cbs.rival_fire = patched_rival_fire

        # 6. Dunya player attack live patches
        def patched_laser_start(self, f):
            with self.lock:
                tid = f.get('targetId') or self.target
                b = self.bots.get(tid)
                if b and b.alive:
                    self.end_invuln(force=True)
                    self.abilities.reveal()
                    self.items.reveal()
                    self.target, self.attacking = b.id, True
                    self.next_laser = max(self.next_laser, time.time())
                    self.send([('UIItemAddHighlightCommand', dict(
                        soundModule=dunya.mod('SoundTriggerModule', playSound=False, soundId=0), itemSource=dunya.mod('UiItemSourceModule', itemSource=0),
                        highlightType=dunya.mod('HighlightTypeModule', type=6), itemId=dunya.LASER_AMMO)),
                        dunya.legacy('0|n|LSH|%d|%d' % (b.id, self.hid))])
                    return
                n = self.npcs.get(tid)
                asset = None if n else self.asset_at(tid)
                if not n and not asset and self.oyuncu(tid):
                    self.send([dunya.legacy('0|A|STM|%s' % ('msg_grp_attack_impossible' if self.grup_uyesi(tid) else 'friendlyfire_disabled'))])
                    return
                if (not asset and (not n or not n.alive)) or self.hero_dead:
                    return
                if asset:
                    err = self.asset_targets.asset_attackable(tid)
                    if err:
                        self.send(err)
                        return
                uid = n.id if n else tid
                self.end_invuln(force=True)
                self.abilities.reveal()
                self.items.reveal()
                self.target, self.attacking = uid, True
                self.next_laser = max(self.next_laser, time.time())
                self.send([('UIItemAddHighlightCommand', dict(
                    soundModule=dunya.mod('SoundTriggerModule', playSound=False, soundId=0), itemSource=dunya.mod('UiItemSourceModule', itemSource=0),
                    highlightType=dunya.mod('HighlightTypeModule', type=6), itemId=dunya.LASER_AMMO)),
                    dunya.legacy('0|n|LSH|%d|%d' % (uid, self.hid))])

        def patched_asset_laser(self, now):
            uid = self.target
            pos = self.asset_at(uid)
            if not pos or self.asset_targets.asset_attackable(uid):
                self.laser_stop()
                return
            hx, hy = self.hero_pos(now)
            rng = self.laser_range()
            if math.hypot(pos[0] - hx, pos[1] - hy) > rng:
                if self.range_warned != uid:
                    self.range_warned = uid
                    self.send([dunya.range_exceeded(uid, rng, 1)] + self.combat_state(dunya.COMBAT_OUT_OF_RANGE, now))
                return
            if self.range_warned == uid:
                self.send(self.combat_state(dunya.COMBAT_CONTINUES, now))
            self.range_warned = None
            lasers = self.lasers() + self.drone_lasers()
            ammo = self.p.d['secili']['lazer']
            cooldown = dunya.ESYA['lazer_cephane'].get(ammo, {}).get('aralik_sn')
            if cooldown and now < self.ammo_ready.get(ammo, 0):
                return
            if not lasers or self.p.use_ammo(ammo, len(lasers)) is None:
                if not lasers:
                    self.send([dunya.stm('no_lasers_on_board')])
                    self.laser_stop()
                    return
                alt, msgs = self.ammo_out('lazer', ammo, len(lasers))
                self.send(msgs)
                if not alt:
                    self.laser_stop()
                return
            self.last_combat = now
            self.stop_repair()
            self.next_laser = now + dunya.SAVAS['lazer_aralik_sn']
            if cooldown:
                self.ammo_ready[ammo] = now + cooldown
            self.send(self.ammo_msgs(ammo) + [('AttackLaserRunCommand', dict(attackerId=self.hid, targetId=uid, laserColor=self.laser_color(ammo),
                                                                             isDiminishedBySkillShield=False, skilledLaser=False, visualType=0))])
            self.p.ach('shot', silah='LASER')
            m_ = self.p.mods()
            base_acc = dunya.SAVAS['lazer_isabet'] * (1 + m_.get('isabet', 0) + m_.get('lazer_isabet', 0))
            aim_chance = dunya.AY.chance('oyuncu_isabet', base_acc) if hasattr(dunya.AY, 'chance') else base_acc
            if random.random() < self.items.aim(aim_chance):
                dmg, _ = self.laser_damage(ammo)
                self.send(self.asset_targets.asset_hit(uid, dmg))
            else:
                self.send([('AttackMissedCommand', dict(attackType=dunya.attack_type(1), targetUserId=uid, skillColorId=0))])
            self.items.auto_weapons(None, now, target_id=uid)
            if not self.asset_at(uid):
                self.laser_stop()

        def patched_rocket(self, f):
            with self.lock:
                now = time.time()
                tid = f.get('targetId') or self.target
                n = self.npcs.get(tid) or self.bots.get(tid)
                asset = None if n else self.asset_at(tid)
                if not n and not asset:
                    return
                if n and not n.alive:
                    return
                if asset:
                    err = self.asset_targets.asset_attackable(tid)
                    if err:
                        self.send(err)
                        return
                rocket = self.p.d['secili']['roket']
                import savas_esya as SE_MOD
                special = SE_MOD.special(rocket)
                if (not special and now < self.rocket_ready - dunya.ROKET_PAYI) or self.hero_dead:
                    return
                hx, hy = self.hero_pos(now)
                tx, ty = n.mover.pos(now) if n else asset
                if math.hypot(tx - hx, ty - hy) > dunya.SAVAS['roket_menzil']:
                    self.send([dunya.range_exceeded(tid, dunya.SAVAS['roket_menzil'], 0)])
                    return
                if special:
                    if n:
                        self.items.fire_special(rocket, n, now)
                    return
                if self.p.use_ammo(rocket, 1) is None:
                    alt, msgs = self.ammo_out('roket', rocket, 1)
                    self.send(msgs)
                    if not alt or self.p.use_ammo(alt, 1) is None:
                        return
                    rocket = alt
                if rocket != dunya.IP.PLT_2021 and self.p.ammo(dunya.IP.PLT_2021) > 0:
                    h = self.p.hint(dunya.IP.EQUIP_YOUR_ROCKETS)
                    if h:
                        self.send(h)
                self.end_invuln(force=True)
                self.abilities.reveal()
                self.items.reveal()
                self.last_combat = now
                self.stop_repair()
                self.p.ach('shot', silah='ROCKET_LAUNCHER')
                import ekipman as EK_MOD
                ms = int(dunya.SAVAS['roket_bekleme_ms'] * (0.5 if self.p.premium else 1)
                         * (1 + self.p.mods().get('roket_bekleme', 0))
                         * EK_MOD.rocket_factor(self.p) * dunya.AY.carpan('roket_bekleme'))
                ms = self.abilities.rocket_ms(ms, now)
                self.rocket_ready = now + ms / 1000
                hit = random.random() < self.rocket_hit(rocket)
                target_id = n.id if n else tid
                self.send(self.ammo_msgs(rocket) + [dunya.legacy('0|v|%d|%d|%s|%d|0|0' % (self.hid, target_id, 'H' if hit else 'M',
                                                                                dunya.ESYA['roketler'].get(rocket, {}).get('kimlik', 1))),
                           ('MenuItemCooldownGroupTimerCommand', dict(timerState=dunya.mod('TimerStateModule', timerStateValue=2),
                                                                      cooldownType=dunya.mod('CooldownTypeModule', typeValue=4), maxTime=ms, time=ms))])
                dmg = int(dunya.ESYA['roketler'].get(rocket, {'hasar': 1000})['hasar'] * random.uniform(0.85, 1.0)
                          * (1 + self.p.mods().get('roket', 0) + self.p.mods().get('npc', 0)) * (1 + self.p.lab_bonus(1)))
                if self.p.lab_bonus(1):
                    self.lab_spend(1)
                if hit:
                    if n:
                        self.later(dunya.SAVAS['roket_ucus_sn'], lambda: self.hit_npc(target_id, dmg, 0))
                    else:
                        self.later(dunya.SAVAS['roket_ucus_sn'], lambda: self.send(self.asset_targets.asset_hit(target_id, dmg)))
                else:
                    self.later(dunya.SAVAS['roket_ucus_sn'], lambda: self.send([('AttackMissedCommand', dict(
                        attackType=dunya.attack_type(0), targetUserId=target_id, skillColorId=0))]))
                self.later(ms / 1000, lambda: self.send([('MenuItemCooldownGroupTimerCommand', dict(
                    timerState=dunya.mod('TimerStateModule', timerStateValue=0), cooldownType=dunya.mod('CooldownTypeModule', typeValue=4),
                    maxTime=0, time=0))]))

        dunya.Dunya.laser_start = patched_laser_start
        dunya.Dunya.asset_laser = patched_asset_laser
        dunya.Dunya.rocket = patched_rocket

        def patched_quickslot_start(self):
            n = self.npcs.get(self.target) or self.bots.get(self.target)
            if n and n.alive and not self.hero_dead:
                self.log('   kısayolla saldırı: %s' % n.d['ad'])
                self.laser_start({'targetId': n.id})
            elif self.asset_at(self.target) and not self.hero_dead:
                self.log('   kısayolla saldırı (istasyon varlığı): %s' % self.target)
                self.laser_start({'targetId': self.target})

        dunya.Dunya.quickslot_start = patched_quickslot_start

        # Disable deflector on all active CBS instances in memory and rebind instances
        oyun = sys.modules.get('game')
        if oyun and hasattr(oyun, 'OTURUMLAR'):
            for sess in list(oyun.OTURUMLAR):
                cbs_obj = getattr(sess, 'cbs', None)
                if cbs_obj:
                    for aid_str, ast_rec in getattr(cbs_obj, 'st', {}).get('asteroitler', {}).items():
                        if ast_rec.get('sahip') == 'rakip':
                            ast_rec.setdefault('deflector', {})['acik'] = False
                w = getattr(sess, 'world', None)
                if w and hasattr(w, 'cbs'):
                    for aid_str, ast_rec in getattr(w.cbs, 'st', {}).get('asteroitler', {}).items():
                        if ast_rec.get('sahip') == 'rakip':
                            ast_rec.setdefault('deflector', {})['acik'] = False
    except Exception:
        pass


def clean_phantom_ships(oyun=None, target_uid=None):
    """Canlı oturumlardaki hayalet / ölü gemileri istemciden temizler."""
    if not oyun or not hasattr(oyun, 'OTURUMLAR'):
        return 0
    removed_count = 0
    for s in list(oyun.OTURUMLAR):
        w = getattr(s, 'world', None)
        if not w:
            continue
        to_remove = set()
        
        # Belirli bir uid istenmişse
        if target_uid:
            to_remove.add(int(target_uid))
        else:
            # Bilinen bot id aralığı (200000000+) ve ölü / var olmayan botlar
            for uid in list(w.visible):
                if uid >= 200000000 and (uid not in w.bots or not getattr(w.bots[uid], 'alive', False)):
                    to_remove.add(uid)
                elif uid not in w.npcs and uid not in w.bots and uid not in getattr(w, 'oyuncular', {}):
                    to_remove.add(uid)
            
            # 200000001 (xX_Hunter_Xx) gibi bilinen takılı kalan id'ler
            for test_id in range(200000000, 200000025):
                if test_id not in getattr(w, 'bots', {}):
                    to_remove.add(test_id)
                elif not getattr(w.bots[test_id], 'alive', False):
                    to_remove.add(test_id)
                
        if to_remove:
            clean_msgs = []
            for uid in to_remove:
                w.visible.discard(uid)
                clean_msgs.append(('ShipDestroyedCommand', dict(destroyedUserId=uid, explosionTypeId=0)))
                clean_msgs.append(('ShipRemoveCommand', {'userId': uid}))
                removed_count += 1
            s.send(clean_msgs, quiet=True)
    return removed_count


def handle_chat_command(sohbet, conn, path, msg_text):
    """Sohbetten gelen komutları işler. Komut işlendiyse True döner."""
    text = msg_text.strip()
    if not text:
        return False
        
    cmd_name = text.split()[0].lower()
    
    # Desteklenen komut adları (!give, .give, /give, give, vb.)
    is_give = cmd_name in (
        '!give', '.give', '/give', 'give',
        '!item', '.item', '/item', 'item',
        '!grant', '.grant', '/grant', 'grant'
    )
    is_help = cmd_name in (
        '!help', '.help', '/help', 'help',
        '!?', '.?', '/?', '?',
        '!yardim', '.yardim', '/yardim', 'yardim'
    )
    is_rebind = cmd_name in (
        '!rebind', '.rebind', '/rebind', 'rebind',
        '!qfc-rebind', '.qfc-rebind',
        '!bind', '.bind', '/bind', 'bind'
    )
    is_cbs = cmd_name in (
        '!cbs', '.cbs', '/cbs', 'cbs'
    )
    is_clean = cmd_name in (
        '!clean', '.clean', '/clean', 'clean',
        '!fix', '.fix', '/fix', 'fix',
        '!clear', '.clear', '/clear', 'clear'
    )

    # Canlı modül yamalarını ve ölü bot temizliğini her komutta uygula
    oyun = getattr(sohbet, 'oyun', None) or sys.modules.get('game')
    apply_live_patches()
    clean_phantom_ships(oyun)
    
    if is_cbs:
        sub = text.split()[1].lower() if len(text.split()) > 1 else 'status'
        sender = conn.user.get('userId', 'Pilot') if conn.user else 'Pilot'
        s = find_online_session(oyun, sender)
        if not s or not getattr(s, 'cbs', None):
            sohbet.cevap(conn, path, "CBS: You must be online in-game to manage Clan Battle Stations.")
            return True
        cbs_obj = s.cbs
        st_asts = cbs_obj.st.get('asteroitler', {})
        import harita as H, cbs as CBS_MOD

        if sub in ('status', 'list', 'info'):
            lines = ["--- Clan Battle Stations ---"]
            for aid, a in sorted(st_asts.items(), key=lambda kv: int(kv[0])):
                if a.get('durum') == 'kurulu':
                    m_id = CBS_MOD.AST[int(aid)]['harita']
                    clan = a.get('rakip') if a.get('sahip') == 'rakip' else 'Your Clan'
                    def_state = "ON" if a.get('deflector', {}).get('acik') else "OFF (Attackable!)"
                    lines.append(f"• [{H.name(m_id)}] {CBS_MOD.AST[int(aid)]['ad']} - Clan: {clan} | Deflector: {def_state}")
            if len(lines) == 1:
                lines.append("No active Clan Battle Stations found.")
            lines.append("Commands: !cbs deflector off | !cbs spawn [map]")
            sohbet.cevap(conn, path, "\n".join(lines))
            return True

        elif sub in ('deflector', 'attack', 'attackable'):
            val = text.split()[2].lower() if len(text.split()) > 2 else 'off'
            state = (val == 'on')
            cnt = 0
            for aid, a in st_asts.items():
                if a.get('durum') == 'kurulu' and a.get('sahip') == 'rakip':
                    a.setdefault('deflector', {})['acik'] = state
                    cnt += 1
            s.profil.dirty = True
            s.profil.save()
            if s.world:
                for aid, a in st_asts.items():
                    if a.get('durum') == 'kurulu' and int(CBS_MOD.AST[int(aid)]['harita']) == int(s.world.map_id):
                        s.send(cbs_obj.refresh_assets(int(aid)))
            sohbet.cevap(conn, path, f"CBS: Deflector shields set to {'ON' if state else 'OFF'} across {cnt} rival stations! Attackable: {not state}")
            return True

        elif sub in ('spawn', 'build', 'create'):
            parts = text.split()[2:]
            target_map_name = parts[0].upper() if parts else None
            w = getattr(s, 'world', None)
            target_map_id = None
            if target_map_name:
                for mid in CBS_MOD.BY_MAP:
                    if H.name(mid).upper() == target_map_name:
                        target_map_id = mid
                        break
            if not target_map_id and w:
                target_map_id = int(w.map_id)
            cand_aids = CBS_MOD.BY_MAP.get(target_map_id, [])
            if not cand_aids:
                sohbet.cevap(conn, path, f"CBS: No asteroid exists on map {H.name(target_map_id) if target_map_id else 'unknown'}.")
                return True
            aid = cand_aids[0]
            a = cbs_obj.ast(aid)
            msgs = cbs_obj.rival_build(aid, a, time.time())
            a['deflector']['acik'] = False
            s.profil.dirty = True
            s.profil.save()
            if w and int(w.map_id) == int(CBS_MOD.AST[aid]['harita']):
                s.send(msgs + cbs_obj.refresh_assets(aid))
            sohbet.cevap(conn, path, f"CBS: Successfully established rival station on {H.name(target_map_id)} ({CBS_MOD.AST[aid]['ad']}) with deflector OFF!")
            return True

    if is_clean:
        count = clean_phantom_ships(oyun)
        sohbet.cevap(conn, path, f"Cleaned up floating / dead phantom ships from your screen! (Removed: {count})")
        return True
    
    if is_give:
        sender = conn.user.get('userId', 'Pilot') if conn.user else 'Pilot'
        online_users = []
        if oyun and hasattr(oyun, 'OTURUMLAR'):
            for s in list(oyun.OTURUMLAR):
                pr = getattr(s, 'profil', None)
                if pr:
                    u = pr.d.get('pilot', {}).get('userName')
                    if u: online_users.append(u)
                    
        all_users = get_all_usernames(oyun)
        
        target, item_query, amount, target_ship, status = parse_give_command(text, sender, online_users, all_users)
        if status != "OK":
            sohbet.cevap(conn, path, status)
            return True
            
        result = execute_give(target, item_query, amount, sender, oyun, target_ship=target_ship)
        sohbet.cevap(conn, path, result)
        return True

    if is_rebind:
        sender = conn.user.get('userId', 'Pilot') if conn.user else 'Pilot'
        s = find_online_session(oyun, sender)
        if not s:
            sohbet.cevap(conn, path, "You must be online in-game to use !rebind.")
            return True
            
        parts = text.split()[1:]
        target_ship = resolve_ship(parts[0]) if parts else None
        if not target_ship:
            try:
                target_ship = s.profil.ship()['lootId']
            except Exception:
                target_ship = 'ship_solace'
                
        count = 0
        with s.profil.lock:
            qfcs = s.profil.d.get('qfc', {})
            for iid, rec in qfcs.items():
                if rec.get('gemi') != target_ship:
                    rec['gemi'] = target_ship
                    count += 1
            if count > 0:
                s.profil.dirty = True
                
        if count > 0:
            s.profil.save()
            s.send([s.magaza.yeni.qfc.list_cmd()], quiet=True)
            sohbet.cevap(conn, path, f"Successfully rebound {count} Quantum Fluid Core(s) to {target_ship}!")
        else:
            sohbet.cevap(conn, path, f"All your Quantum Fluid Cores are already bound to {target_ship}.")
        return True

    if is_help:
        help_msg = (
            "Available In-Game Commands:\n"
            "• !give [player] <item> [amount] [ship] - Give anything to any user\n"
            "  (Note: Use !give or .give because client reserves / for help)\n"
            "  Examples:\n"
            "    !give qfc-ax40 solace\n"
            "    !give qfc-df40 solace\n"
            "    !give uridium 100000\n"
            "    !give ul-nidhogg-solace-plus 5\n"
            "    !give all x4 50000\n"
            "• !rebind [ship] - Rebind all existing QFC cores in your inventory to your active ship\n"
            "• !clean (or !fix) - Clean up any floating dead phantom ships from your screen\n"
            "• !cbs - Clan Battle Station status and controls (!cbs, !cbs deflector off, !cbs spawn)\n"
            "• !help - Display this help message"
        )
        sohbet.cevap(conn, path, help_msg)
        return True

    # Bilinmeyen özel ! veya . komutları
    if cmd_name.startswith(('!', '.')):
        sohbet.cevap(conn, path, f"Unknown command: '{cmd_name}'. Type !help for available commands.")
        return True

    return False
