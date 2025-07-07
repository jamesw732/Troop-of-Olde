"""API for handling combat calculations"""
from ursina import *
import random

from .base import sigmoid, sqdist, fists_base_dmg, slot_to_ind


# PUBLIC
def tick_combat_timer(char, slot, wpn):
    delay = get_wpn_delay(wpn)
    tick_amt = time.dt * get_haste_modifier(char.haste)
    if slot == "mh":
        char.mh_combat_timer += tick_amt
        if char.mh_combat_timer >= delay:
            char.mh_combat_timer -= delay
            return True
    if slot == "oh":
        char.oh_combat_timer += tick_amt
        if char.oh_combat_timer >= delay:
            char.oh_combat_timer -= delay
            return True
    return False

def get_target_hittable(src, wpn):
    """Returns a tuple of (hittable, reason) where hittable depends on
    line of sight and whether target is within range, and reason is the
    reason for returning false (violating either "los" or "range")"""
    tgt = src.target
    if not src.get_tgt_los(tgt):
        return (False, f"You can't see {tgt.cname}.")
    atk_range = get_wpn_range(wpn)
    # use center rather than center of feet
    pos_src = src.position + Vec3(0, src.scale_y / 2, 0)
    pos_tgt = tgt.position + Vec3(0, tgt.scale_y / 2, 0)
    ray_dir = pos_tgt - pos_src
    ray_dist = distance(pos_tgt, pos_src)
    # Draw a line between the two
    line1 = raycast(pos_src, direction=ray_dir, distance=ray_dist,
                   traverse_target=src)
    line2 = raycast(pos_tgt, direction=-ray_dir, distance=ray_dist,
                    traverse_target=tgt)
    # ie one char is inside the other
    if not line1.hit or not line2.hit:
        return (True, "")
    point1 = line1.world_point
    point2 = line2.world_point
    # don't compute the distance between their centers,
    # compute the distance between their bodies
    inner_distance = distance(point1, point2)
    in_range = inner_distance <= atk_range
    if in_range:
        return (True, "")
    else:
        return (False, f"{tgt.cname} is out of range!")

def get_damage(src, tgt, wpn, slot):
    base_dmg = get_wpn_dmg(wpn)
    base_dmg *= 2 * sigmoid(src.str - tgt.armor)
    min_hit = max(0, ceil(base_dmg * 0.5))
    max_hit = max(0, ceil(base_dmg * 1.5))
    dmg = random.randint(min_hit, max_hit)
    if slot == "oh":
        dmg = int(0.5 * dmg)
    return dmg

def get_level_up(src, tgt, wpn):
    # Currently depends on src and tgt but unused, will be used eventually
    skill = get_wpn_style(wpn)
    if random.random() > 0.5:
        return True, skill
    return False, skill


# PRIVATE
def get_wpn_delay(wpn):
    """Wrapper for wpn.info['delay']"""
    if wpn is None:
        return 1
    return wpn.info.get('delay', 1)

def get_wpn_range(wpn):
    """Wrapper for wpn.info['range']"""
    if wpn is None:
        return 1
    return wpn.info.get('range', 1)

def get_haste_modifier(haste):
    """Convert haste to a multiplicative time modifier"""
    return max(0, 1 + (haste / 100))

def get_wpn_dmg(wpn):
    """Wrapper for wpn.info['dmg']"""
    if wpn is None:
        return 1
    return wpn.info.get('dmg', 1)

def get_wpn_style(wpn):
    """Wrapper for wpn.info['style']"""
    if wpn is None:
        return 'fists'
    return wpn.info.get('style', 'fists')

