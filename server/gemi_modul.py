"""Gemi modülleri ve kararsız modüller (yol haritası Aşama 6; veri data/gemi_modulleri.json <- tools/gemi_modulleri.py).

Normal modüller (DMG-CHT01, HP-VP01, SPC-XP01 …): hangarda config'in "upgrades" yuvasına takılır (HangarShipEquipmentMsg.upgrades;
yuva sayısı istemcinin gemi verisinden: çoğu gemide 3, Plus gemilerde 4). Etki yalnız açıklamadaki gemilerde (istemcinin metni
"This ship upgrade module can be used on the following ships: …"); SPC-XP01/02'nin EP'si 16. seviyeye dek.
Kararsız modüller (DMG-X1 … XV03, HP-/SHD-/SPC- serileri): her örneğin rastgele nitelikleri (UnstableAttributeModule {attribute,
boostValue}; adlar istemcinin items_equipment_shipupgrade_modifiertype_* anahtarları) ve geçerli olduğu gemiler (shipDesigns) var;
istemcinin Restabilize penceresi (istekler istemcinin kodundan):
  girişte / değişince       UnstableModulesListCommand {allModules, shardCommand {chipLeft, shardsLeft}}
  UnstableModuleRerollRequest {itemId}        Unstable Shard harcanır, nitelikler ve gemiler yeniden çekilir; öncekiler saklanır
      -> UnstableModuleRestabilizeResultCommand {itemId, oldModule, newModule, success}
  UnstableModuleRestabiliseRequest {itemId, isSalvage}  isSalvage: Salvage Core vb. ödenip önceki nitelikler geri alınır ("Your
      unstable module has been salvaged to retain the same modifiers"); değilse yenisi kalır
  UnstableModuleRecycleRequest {itemId}        modül sökülür, Unstable Shard geri verilir
Değerler (uyarlama; istemcide yok): seri başına artış aralığı (X1 %2-5, X2 %4-8, X3 %2-10; "at least N%" serilerinde N..N+6),
1-2 nitelik, 3-5 gemi (açıklamadaki gemiler öncelikli), 5 Restabilize hakkı, 15 shard, geri dönüşüm 10 shard, saklama 10 Salvage
Core + 100 Polychromium.
Profilde: kararsiz {itemId: {nitelik: [[ad, değer]], gemiler, hak, onceki}}.
"""
import json, os, random, re

import envanter as INV

HERE = os.path.dirname(os.path.abspath(__file__))
M = json.load(open(os.path.join(HERE, 'data', 'gemi_modulleri.json'), encoding='utf8'))['moduller']
ITEMS = json.load(open(os.path.join(HERE, 'data', 'istemci_esyalari.json'), encoding='utf8'))['esyalar']
SHARD, CHIP = 'resource_collectable_unstable-shard', 'resource_collectable_optigrad-chip'
ATTR_KEYS = {'damage': ('lazer', 'roket'), 'dmg_laser': ('lazer',), 'dmg_rockets': ('roket',), 'dmg_npc': ('npc',), 'dmg_pvp': ('pvp',),
             'hitpoints': ('can',), 'shield': ('kalkan',), 'speed': ('hiz',), 'evasion': ('kacinma',), 'hitchance_laser': ('lazer_isabet',),
             'hitchance_rocket': ('roket_isabet',), 'experience': ('ep',), 'honour': ('onur',), 'shield_penetration': ('kalkan_delme',)}
POOL = {'DAMAGE': ['damage', 'dmg_laser', 'dmg_rockets', 'dmg_npc'], 'HP': ['hitpoints'], 'SHIELD': ['shield'],
        'SPECIAL': ['speed', 'evasion', 'hitchance_laser', 'hitchance_rocket', 'experience', 'shield_penetration']}
SERIES = {'x1': (0.02, 0.05), 'x2': (0.04, 0.08), 'x3': (0.02, 0.10), 'xw01': (0.0, 0.15)}
REROLLS, REROLL_COST, RECYCLE, RETAIN = 5, 15, 10, {'resource_collectable_salvage-core': 10, 'resource_collectable_polychromium': 100}
XP_MAX_LEVEL = 16
UPGRADE_SLOTS = 3


def mod(name, **f):
    f['_'] = name
    return f


def is_module(loot):
    return loot in M


def unstable(loot):
    return 'kararsiz' in M.get(loot, {})


def slots(ship_loot):
    """Geminin modül yuvası (istemcinin gemi verisi: ship_upgrades)."""
    return int((ITEMS.get(ship_loot, {}).get('yuvalar') or {}).get('ship_upgrades', UPGRADE_SLOTS))


def ships_for(loot):
    return M.get(loot, {}).get('gemiler', [])


def all_ships():
    """Kararsız modülün çekilebileceği gemiler: sunucunun gemileri (esyalar.json gemiler)."""
    global _SHIPS
    if _SHIPS is None:
        _SHIPS = sorted(json.load(open(os.path.join(HERE, 'data', 'esyalar.json'), encoding='utf8'))['gemiler'])
    return _SHIPS


_SHIPS = None


# ------------------------------------------------------------ kararsız modül değerleri
def roll(loot, rng=random):
    """Kararsız modülün nitelikleri ve gemileri."""
    info = M[loot]
    code = loot.rsplit('-', 1)[-1]
    lo, hi = SERIES.get(code) or ((info['kararsiz']['en_az'], info['kararsiz']['en_az'] + 0.06) if info['kararsiz'].get('en_az')
                                  else (0.03, 0.08))
    pool = POOL.get(info['tur'], POOL['DAMAGE'])
    attrs = rng.sample(pool, min(len(pool), rng.choice((1, 1, 2))))
    vals = [[a, round(rng.uniform(lo, hi), 3)] for a in attrs]
    pref = [s for s in info['kararsiz'].get('tercih', [])]
    rest = [s for s in all_ships() if s not in pref]
    n = rng.randint(3, 5)
    picks = rng.sample(pref, min(len(pref), rng.randint(1, max(1, len(pref))))) if pref else []
    picks += rng.sample(rest, max(0, n - len(picks)))
    return dict(nitelik=vals, gemiler=sorted(set(picks)))


def state(p, iid):
    """Kararsız modül örneğinin kaydı (ilk bakışta çekilir)."""
    d = p.d.setdefault('kararsiz', {})
    rec = d.get(str(iid))
    loot = p.d['esyalar'].get(str(iid))
    if rec is None and loot and unstable(loot):
        rec = d[str(iid)] = dict(roll(loot), hak=REROLLS)
        p.dirty = True
    return rec


def module_msg(p, iid):
    rec, loot = state(p, iid), p.d['esyalar'].get(str(iid))
    return mod('UnstableModuleModule', recycleReturns=RECYCLE, rerollsMax=REROLLS, rerollCost=REROLL_COST, rerollsLeft=rec['hak'],
               retainCost=[mod('LootModule', lootId=l, amount=n, modifier='') for l, n in sorted(RETAIN.items())],
               attributes=[mod('UnstableAttributeModule', attribute=a, boostValue=float(v * 100)) for a, v in rec['nitelik']],
               shipDesigns=list(rec['gemiler']), itemId=int(iid), lootId=loot)


def ship_ids(loots):
    """Hangar ipucunun gemi listesi (HangarShipEquipmentInventoryItem.ships): istemci (TooltipPreparerFactory.ReturnShips) ','
    ile böler, her parçayı sayıya çevirip gemiyi kimliğiyle bulur (GetItemByShipId). Gemi adları (ship_goliath) 0 okunuyordu."""
    return ','.join(str(ITEMS[l]['kimlik']) for l in loots if (ITEMS.get(l) or {}).get('kimlik') is not None)


def modifiers_str(p, iid):
    """Kararsız modülün hangar ipucu nitelikleri: "AD,yüzde;…" (TooltipPreparerFactory.ReturnModifiers: değer tam sayı, metin
    items_equipment_shipupgrade_modifiertype_<ad>). Boşken ipucunun "Tür:" satırı boş kalıyordu (kullanıcı 2026-10-19)."""
    rec = state(p, iid) or {}
    return ';'.join('%s,%d' % (a.upper(), max(1, int(round(v * 100)))) for a, v in rec.get('nitelik', []) if v > 0)


def shard_cmd(p):
    return mod('UnstableModulesShardCommand', chipLeft=p.resource(CHIP), shardsLeft=p.resource(SHARD))


def list_cmd(p, reset=False):
    import parcacik as PC                                       # parçacık topları ve kırıcılar (OptiGrad Chip; Aşama 9b)
    ids = sorted(int(i) for i, l in p.d['esyalar'].items() if unstable(l))
    return ('UnstableModulesListCommand', dict(allModules=[module_msg(p, i) for i in ids] + PC.modules(p), resetUI=reset,
                                                 isDiscountRunning=False, shardCommand=shard_cmd(p)))


# ------------------------------------------------------------ etkiler
def mods(p, ship_loot, iids, level=None):
    """Takılı modüllerin bonusları (yalnız geçerli gemide)."""
    out = {}
    for iid in iids:
        loot = p.d['esyalar'].get(str(iid))
        info = M.get(loot or '')
        if not info:
            continue
        if 'kararsiz' in info:
            rec = state(p, iid)
            if ship_loot not in rec['gemiler']:
                continue
            eff = {}
            for a, v in rec['nitelik']:
                for k in ATTR_KEYS.get(a, ()):
                    eff[k] = eff.get(k, 0) + v
        else:
            if ship_loot not in info['gemiler']:
                continue
            eff = dict(info['etkiler'])
            if 'ep' in eff and loot.startswith('equipment_shipupgrade_spc-xp') and (level or 0) >= XP_MAX_LEVEL:
                eff.pop('ep')                                   # SPC-XP01/02: 16. seviyeye dek
        for k, v in eff.items():
            out[k] = out.get(k, 0) + v
    return out


def equip_allowed(loot, ship_loot):
    """Normal modül yalnız açıklamadaki gemilere takılır; kararsız modül her gemiye (etkisi yalnız kendi gemilerinde)."""
    info = M.get(loot)
    return bool(info) and ('kararsiz' in info or ship_loot in info['gemiler'])


# ------------------------------------------------------------ istekler
class Moduller:
    def __init__(self, profil, log=print):
        self.p, self.log = profil, log
        self.m = None

    def result(self, iid, old, new, ok=True):
        return ('UnstableModuleRestabilizeResultCommand', dict(itemId=int(iid), oldModule=old, newModule=new, success=ok))

    def reroll(self, f):
        iid = int(f.get('itemId') or 0)
        loot = self.p.d['esyalar'].get(str(iid))
        import parcacik as PC
        if loot and PC.restabilizable(loot):                    # top/kırıcı: OptiGrad Chip ile ek nitelikler
            from eski_protokol import legacy
            res = PC.reroll(self.p, iid)
            if isinstance(res, str):
                return [legacy('0|A|STM|%s' % res), list_cmd(self.p)]
            self.log('   Restabilize: %s -> %s' % (loot, PC.state(self.p, iid)['nitelik']))
            return INV.update_msgs(self.m, self.p, [CHIP]) + self.after(iid, [self.result(iid, *res)])
        if not loot or not unstable(loot):
            from eski_protokol import legacy
            return [legacy('0|A|STM|msg_reroll_error_item')]
        rec = state(self.p, iid)
        if rec['hak'] <= 0:
            from eski_protokol import legacy
            return [legacy('0|A|STM|msg_reroll_error_item')]
        if INV.missing(self.p, {SHARD: REROLL_COST}):
            from eski_protokol import legacy
            return [legacy('0|A|STM|msg_reroll_error_shards'), list_cmd(self.p)]
        old = module_msg(self.p, iid)
        self.p.add_resource(SHARD, -REROLL_COST)
        with self.p.lock:
            rec['onceki'] = dict(nitelik=rec['nitelik'], gemiler=rec['gemiler'])
            rec.update(roll(loot))
            rec['hak'] -= 1
            self.p.dirty = True
        self.log('   Restabilize: %s -> %s %s' % (loot, rec['nitelik'], rec['gemiler']))
        return self.after(iid, [self.result(iid, old, module_msg(self.p, iid))])

    def restabilise(self, f):
        iid = int(f.get('itemId') or 0)
        import parcacik as PC
        if PC.restabilizable(self.p.d['esyalar'].get(str(iid), '')):      # top/kırıcı: eskisine dön ya da yenisi kalsın
            if f.get('isSalvage'):
                PC.revert(self.p, iid)
            else:
                (PC.state(self.p, iid) or {}).pop('onceki', None)
            return self.after(iid, [])
        rec = state(self.p, iid) if str(iid) in self.p.d['esyalar'] else None
        if not rec:
            return []
        if not f.get('isSalvage'):
            with self.p.lock:
                rec.pop('onceki', None)
                self.p.dirty = True
            return [list_cmd(self.p)]
        if not rec.get('onceki'):
            return [list_cmd(self.p)]
        if INV.missing(self.p, RETAIN):
            from eski_protokol import legacy
            return [legacy('0|A|STM|msg_reroll_error_salvage'), list_cmd(self.p)]
        removed = INV.spend(self.p, RETAIN, reason='buy_SPECIAL', detail='salvage')
        old = module_msg(self.p, iid)
        with self.p.lock:
            rec.update(rec.pop('onceki'))
            self.p.dirty = True
        self.log('   Salvage: %s önceki niteliklere döndü' % self.p.d['esyalar'][str(iid)])
        return INV.update_msgs(self.m, self.p, list(RETAIN), removed) + self.after(iid, [self.result(iid, old, module_msg(self.p, iid))])

    def recycle(self, f):
        iid = int(f.get('itemId') or 0)
        loot = self.p.d['esyalar'].get(str(iid))
        import parcacik as PC
        if loot and PC.restabilizable(loot):                    # top/kırıcı: OptiGrad Chip ve yükseltme malzemesinin %80'i
            from eski_protokol import legacy
            got = PC.recycle(self.p, iid)
            if got is None:
                return [legacy('0|A|STM|msg_reroll_error_item'), list_cmd(self.p)]
            msgs = [('InventoryItemRemovedCommand', {'itemId': iid})]
            for l, n in got.items():
                msgs += self.m.reward(l, n) if self.m else []
                if not self.m:
                    self.p.add_resource(l, n)
            self.log('   geri dönüşüm: %s -> %s' % (loot, got))
            return msgs + [('UnstableModuleRecycleResultCommand', dict(itemId=iid, shardCommand=shard_cmd(self.p))), list_cmd(self.p)]
        if not loot or not unstable(loot) or iid in self.p.equipped_ids():
            from eski_protokol import legacy
            return [legacy('0|A|STM|msg_reroll_error_item')]
        with self.p.lock:
            del self.p.d['esyalar'][str(iid)]
            self.p.d.get('kararsiz', {}).pop(str(iid), None)
            self.p.dirty = True
        msgs = [('InventoryItemRemovedCommand', {'itemId': iid})] + (self.m.reward(SHARD, RECYCLE) if self.m else [])
        if not self.m:
            self.p.add_resource(SHARD, RECYCLE)
        self.log('   geri dönüşüm: %s -> %d shard' % (loot, RECYCLE))
        return msgs + [('UnstableModuleRecycleResultCommand', dict(itemId=iid, shardCommand=shard_cmd(self.p))), list_cmd(self.p)]

    def after(self, iid, msgs):
        """Takılı modül değiştiyse hız/kalkan/can yeniden."""
        out = msgs + [list_cmd(self.p)]
        if self.m and iid in self.p.equipped_ids():
            out += [self.m.equipment_cmd()] + self.m.apply_stats()
        return out

    def handle(self, name, f):
        fn = {'UnstableModuleRerollRequest': self.reroll, 'UnstableModuleRestabiliseRequest': self.restabilise,
              'UnstableModuleRecycleRequest': self.recycle}.get(name)
        if name == 'RerollWindowSettingsRequest':
            with self.p.lock:
                self.p.d['reroll_ayar'] = f.get('rerollWindowSettingsModule') or {}
                self.p.dirty = True
            return []
        return fn(f) if fn else None
