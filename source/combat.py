from ursina import *
import random

from . import sigmoid, sqdist, fists_base_dmg


# PUBLIC
def tick_mh(char):
    """Increment combat timer by dt. Returns True if we exceeded the weapon's delay"""
    # Add time.dt to combat timer, if flows over max, attempt hit and subtract max
    char.mh_combat_timer += time.dt * get_haste_modifier(char.haste)
    wep = char.equipment['mh']
    delay = get_wpn_delay(wep)
    if char.mh_combat_timer > delay:
        char.mh_combat_timer -= delay
        return True
    return False

def tick_oh(char):
    """Increment char's offhand combat timer by dt. Returns True if we exceeded the weapon's delay"""
    # Add time.dt to combat timer, if flows over max, attempt hit and subtract max
    # * dw_skill / rec_level if slot == oh else 1
    char.oh_combat_timer += time.dt * get_haste_modifier(char.haste)  / 1.5
    wep = char.equipment['oh']
    delay = get_wpn_delay(wep)
    if char.oh_combat_timer > delay:
        char.oh_combat_timer -= delay
        return True
    return False

def attempt_attack(src, tgt, slot):
    """Main auto attack function called by character upon timer reset."""
    # Do a bunch of fancy evasion and accuracy calculations to determine if hit goes through
    if random.random() < sigmoid((src.dex - tgt.ref) / 10):
        # It's a miss
        hitstring = get_melee_hit_string(src, tgt, miss=True)
        hit = False
    else:
        # If hit goes through, do some more fancy calculations to get damage
        wep = src.equipment[slot]
        if wep is not None and "info" not in wep:
            return f"Try hitting {tgt.cname} with something else."
        base_dmg = get_wpn_dmg(wep)
        style = get_wpn_style(wep)

        base_dmg *= 2 * sigmoid(src.str - tgt.armor)
        min_hit = max(0, ceil(base_dmg * 0.5))
        max_hit = max(0, ceil(base_dmg * 1.5))
        dmg = random.randint(min_hit, max_hit)
        hitstring = get_melee_hit_string(src, tgt, style=style, dmg=dmg)
        tgt.reduce_health(dmg)
        hit = True
    return hit, hitstring


# PRIVATE
def get_melee_hit_string(src, tgt, style="fists", dmg=0, miss=False):
    """Produce a string with information about the melee hit.

    style will eventually be used to determine the hit string"""
    if miss:
        return f"{src.cname} attempts to hit {tgt.cname}, but misses!"
    return f"{src.cname} hits {tgt.cname} for {dmg} damage!"

def get_haste_modifier(haste):
    """Convert haste to a multiplicative time modifier"""
    return max(0, 1 + haste / 100)

def get_wpn_dmg(wpn):
    if wpn is None:
        return 1
    info = wpn.get('info', {})
    return info.get('dmg', 1)

def get_wpn_style(wpn):
    if wpn is None:
        return 'fists'
    info = wpn.get('info', {})
    return info.get('style', 'fists')

def get_wpn_range(wpn):
    """Equivalent to wpn['info']['range'] with some precautions"""
    if wpn is None:
        return 1
    info = wpn.get('info', {})
    return info.get('range', 1)

def get_wpn_delay(wpn):
    """Equivalent to wpn['info']['delay'] with some precautions"""
    if wpn is None:
        return 1
    info = wpn.get('info', {})
    return info.get('delay', 1)

