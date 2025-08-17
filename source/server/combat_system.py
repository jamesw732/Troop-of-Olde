from ursina import *

from ..base import *
from ..network import network


dt = 1/5


class CombatSystem(Entity):
    """Ticks combat for all Characters.

    Increments combat timers for all characters that are in combat.
    If timer progresses past weapon's delay, performs an attack.
    """
    def __init__(self, gamestate):
        super().__init__()
        self.chars = gamestate.uuid_to_char.values()

    @every(dt)
    def tick_combat(self):
        for char in self.chars:
            if not char.target or not char.target.alive:
                char.target = None
                char.mh_combat_timer = 0
                char.oh_combat_timer = 0
            elif char.in_combat:
                hit_mh = self.attempt_hit(char, "mh")
                # See if we should progress offhand timer too
                # (if has skill dw):
                mh = char.equipment[slot_to_ind["mh"]]
                mh_is_1h = mh is None or mh.info.get("style", "")[:2] != "2h"
                hit_oh = False
                if mh_is_1h:
                    hit_oh = self.attempt_hit(char, "oh")
                if hit_mh or hit_mh:
                    network.broadcast_cbstate_update(char.target)

    def attempt_hit(self, src, slot):
        """Attempts to hit with one weapon"""
        tgt = src.target
        src_conn = network.uuid_to_connection.get(src.uuid, None)
        tgt_conn = network.uuid_to_connection.get(tgt.uuid, None)
        idx = slot_to_ind[slot]
        wpn = src.equipment[idx]
        # Check whether to attempt to perform an attack or not
        attempting = tick_combat_timer(src, slot, wpn, dt)
        if not attempting:
            return False
        for conn in network.connection_to_uuid:
            network.peer.remote_do_attack_anim(conn, src.uuid, slot)
        # Check whether target his within range and in line of sight
        hittable, msg = get_target_hittable(src, wpn)
        if not hittable:
            if src_conn is not None:
                network.peer.remote_print(src_conn, msg)
            if tgt_conn is not None and tgt_conn is not src_conn:
                network.peer.remote_print(tgt_conn, msg)
            return False
        # Check whether hit goes through
        if random.random() < sigmoid((src.dex - tgt.ref) / 10):
            msg = f"{src.cname} attempts to hit {tgt.cname}, but misses!"
            if src_conn is not None:
                network.peer.remote_print(src_conn, msg)
            return False
        # If hit goes through, get damage and modify health
        dmg = get_damage(src, tgt, wpn, slot)
        tgt.reduce_health(dmg)
        msg = f"{src.cname} hits {tgt.cname} for {dmg} damage!"
        if src_conn is not None:
            network.peer.remote_print(src_conn, msg)
        if tgt_conn is not None and tgt_conn is not src_conn:
            network.peer.remote_print(tgt_conn, msg)
        # Potentially raise skill level
        level_up, skill = get_level_up(src, tgt, wpn)
        if level_up:
            src.skills[skill_to_idx[skill]] += 1
            network.peer.remote_update_skills(src_conn, src.skills)
        return True


def tick_combat_timer(char, slot, wpn, dt):
    delay = get_wpn_delay(wpn)
    tick_amt = dt * get_haste_modifier(char.haste)
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

