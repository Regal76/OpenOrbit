"""Shared-map player laser and ordinary rocket attacks; no PvP reward policy.

World owns request routing, firing visuals, damage/kill attribution and map locks.
Selection is independent of these hostility and protection checks.
"""
import math
import random
import time

import klan as KL
from eski_protokol import legacy


def _denied(key='msg_grp_attack_impossible'):
    return [legacy('0|A|STM|' + key)]


def attack_error(w, other, now):
    """[] permits an enemy attack; otherwise native messages explaining denial.

    Recheck this at every shot/impact: a target can enter DMZ, cloak, jump,
    change diplomacy, or disconnect after the attack request.
    """
    if (other is None or other is w or w.ortak is None or other.ortak is not w.ortak
            or not w.running or not other.running or w.map_id != other.map_id
            or w.hero_dead or other.hero_dead or w.jumping or other.jumping
            or w.reload_pending or other.reload_pending
            or w.oyuncu(other.hid) is not other or other.gizli(now)):
        return _denied()
    if (w.in_pvp_peace(*w.hero_pos(now)) or other.in_pvp_peace(*other.hero_pos(now))
            or now < other.invuln_until or other.invulnerable or other.hero_etki.invulnerable(now)):
        return _denied()
    if w.grup_uyesi(other.hid) or other.grup_uyesi(w.hid):
        return _denied()
    a, b = w.p.d['pilot'], other.p.d['pilot']
    clan = int(a.get('clanId') or 0)
    if clan and clan == int(b.get('clanId') or 0):
        return _denied('friendlyfire_disabled')
    relations = (KL.iliski(w.p, other.p), KL.iliski(other.p, w.p))
    if any(r in (1, 2) for r in relations):
        return _denied('friendlyfire_disabled')
    faction = int(a.get('factionId') or 0)
    if faction and faction == int(b.get('factionId') or 0) and 3 not in relations:
        return _denied('friendlyfire_disabled')
    return []


def _hit(w, other, now, normal, shield=0, atype=1):
    with other.lock:
        if attack_error(w, other, now):
            return
        if atype == 1:
            factor = max(0.0, 1 + other.p.mods().get('alinan_lazer', 0))
            normal, shield = int(round(normal * factor)), int(round(shield * factor))
        if shield > 0:
            before = other.p.d['gemi'].get('shield', 0)
            other.send(other.hurt_hero(shield, atype=atype, source_player=w, now=now, shield_only=True))
            drained = max(0, before - other.p.d['gemi'].get('shield', 0))
            if drained:
                g = w.p.d['gemi']
                w.p.set_hull(shield=g.get('shield', 0) + drained)
                w.send([('AttributeShieldUpdateCommand', {'shieldNow': int(g['shield']), 'shieldMax': int(g.get('shieldMax', 0))})])
        if normal > 0 and not other.hero_dead:
            other.send(other.hurt_hero(normal, atype=atype, source_player=w, now=now))


def laser(w, other, now):
    """One laser tick; World.side_laser owns range, ammo, timing and visuals."""
    err = attack_error(w, other, now)
    if err:
        w.send(err)
        w.laser_stop()
        return
    w.side_laser(now, other.hid, other.hero_pos(now),
                 lambda normal, shield: _hit(w, other, now, normal, shield), pvp=True)
    if other.hero_dead:
        w.laser_stop()


def rocket(w, other, now):
    """Handle ordinary AttackRocketRequest for a player. Returns True.

    NPC special-rocket effects have no player implementation here; report this
    before spending ammo or applying their NPC-target helpers.
    """
    import dunya as D
    err = attack_error(w, other, now)
    if err:
        w.send(err)
        return True
    rocket = w.p.d['secili']['roket']
    if D.SE.special(rocket) or rocket not in D.ESYA['roketler']:
        w.send([('MessageCommand', dict(displayTarget=2, displayStyle=1,
            messageModule=D.mod('WildcardMessageModule', message=D.mod('MessageKeyListWildcardModule',
                wildCardReplacements=[], baseKey='Special rockets against players are not supported.',
                baseKeyType=D.mod('ReplacementTypeModule', typeValue=0), textStyle=0))))])
        return True
    if now < w.rocket_ready - D.ROKET_PAYI:
        return True
    hx, hy = w.hero_pos(now)
    tx, ty = other.hero_pos(now)
    if math.hypot(tx - hx, ty - hy) > D.SAVAS['roket_menzil']:
        w.send([D.range_exceeded(other.hid, D.SAVAS['roket_menzil'], 0)])
        return True
    if w.p.use_ammo(rocket, 1) is None:
        alt, msgs = w.ammo_out('roket', rocket, 1)
        w.send(msgs)
        if not alt or alt not in D.ESYA['roketler'] or D.SE.special(alt) or w.p.use_ammo(alt, 1) is None:
            return True
        rocket = alt
    w.end_invuln(force=True)
    w.abilities.reveal()
    w.items.reveal()
    w.last_combat = now
    w.stop_repair()
    w.p.ach('shot', silah='ROCKET_LAUNCHER')
    mods = w.p.mods()
    ms = int(D.SAVAS['roket_bekleme_ms'] * (0.5 if w.p.premium else 1)
             * (1 + mods.get('roket_bekleme', 0)) * D.EK.rocket_factor(w.p) * D.AY.carpan('roket_bekleme'))
    ms = w.abilities.rocket_ms(ms, now)
    w.rocket_ready = now + ms / 1000
    roll = random.random()
    hit = roll < w.rocket_hit(rocket)
    saved = hit and roll >= w.rocket_hit(rocket, skill=False)
    w.send(w.ammo_msgs(rocket) + [w.rocket_msg(other.hid, hit, D.ESYA['roketler'][rocket].get('kimlik', 1), saved),
        ('MenuItemCooldownGroupTimerCommand', dict(timerState=D.mod('TimerStateModule', timerStateValue=2),
            cooldownType=D.mod('CooldownTypeModule', typeValue=4), maxTime=ms, time=ms))])
    damage = int(D.ESYA['roketler'][rocket].get('hasar', 1000) * random.uniform(0.85, 1.0)
                 * (1 + mods.get('roket', 0)) * (1 + w.p.lab_bonus(1)))
    if w.p.lab_bonus(1):
        w.lab_spend(1)

    def impact():
        impact_now = time.time()
        if hit:
            _hit(w, other, impact_now, damage, atype=0)
        elif not attack_error(w, other, impact_now):
            w.send([('AttackMissedCommand', dict(attackType=D.attack_type(0), targetUserId=other.hid, skillColorId=0))])
    w.later(D.SAVAS['roket_ucus_sn'], impact)
    w.later(ms / 1000, lambda: w.send([('MenuItemCooldownGroupTimerCommand', dict(
        timerState=D.mod('TimerStateModule', timerStateValue=0), cooldownType=D.mod('CooldownTypeModule', typeValue=4),
        maxTime=ms, time=0))]))
    return True
