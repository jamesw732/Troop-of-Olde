from ursina import *
from ursina.networking import rpc
import random

from .base import sigmoid, sqdist, fists_base_dmg, style_to_method
from .networking.base import network
from .states.skills import attempt_raise_skill
from .ui.main import ui

# PUBLIC
def progress_mh_combat_timer(char):
    """Increment combat timer by dt. If past max, attempt a melee hit."""
    # Add time.dt to combat timer, if flows over max, attempt hit and subtract max
    char.mh_combat_timer += time.dt * get_haste_modifier(char.haste)
    wep = char.equipment['mh']
    delay = get_wpn_delay(char, wep)
    if char.mh_combat_timer > delay:
        char.mh_combat_timer -= delay
        if get_target_hittable(char, wep):
            if network.is_main_client():
                attempt_melee_hit(char, char.target, "mh")
            else:
                # Host-authoritative, so we need to ask the host to compute the hit
                network.peer.remote_attempt_melee_hit(
                    network.peer.get_connections()[0],
                    char.uuid, char.target.uuid, "mh")

def progress_oh_combat_timer(char):
    """Increment combat timer by dt. If past max, attempt a melee hit."""
    # Add time.dt to combat timer, if flows over max, attempt hit and subtract max
    # * dw_skill / rec_level if slot == oh else 1
    char.oh_combat_timer += time.dt * get_haste_modifier(char.haste)  / 1.5
    wep = char.equipment['oh']
    delay = get_wpn_delay(char, wep)
    if char.oh_combat_timer > delay:
        char.oh_combat_timer -= delay
        if get_target_hittable(char, wep):
            if network.is_main_client():
                attempt_melee_hit(char, char.target, "oh")
            else:
                # Host-authoritative, so we need to ask the host to compute the hit
                network.peer.remote_attempt_melee_hit(
                    network.peer.get_connections()[0],
                    char.uuid, char.target.uuid, "oh")


# PRIVATE
def attempt_melee_hit(src, tgt, slot):
    """Main driver method for melee combat called by progress_mh/oh_melee_timer.
    Only main client (ie host or offline client) should call this. If not main client,
    call remote version."""
    # Do a bunch of fancy evasion and accuracy calculations to determine if hit goes through
    if random.random() < sigmoid((src.dex - tgt.ref) / 10):
        # It's a miss
        hitstring = get_melee_hit_string(src, tgt, miss=True)
    else:
        # If hit goes through, do some more fancy calculations to get damage
        wep = src.equipment[slot]
        if wep is not None and "info" not in wep:
            ui.gamewindow.add_message(f"Try hitting {target.cname} with something else.")
            return
        base_dmg = get_wpn_dmg(src, wep)
        style = get_wpn_style(src, wep)

        base_dmg *= 2 * sigmoid(src.str - tgt.armor)
        min_hit = max(0, ceil(base_dmg * 0.5))
        max_hit = max(0, ceil(base_dmg * 1.5))
        dmg = random.randint(min_hit, max_hit)
        hitstring = get_melee_hit_string(src, tgt, style=style, dmg=dmg)
        reduce_health(tgt, dmg)
        attempt_raise_skill(src, style, prob=0.5)
    ui.gamewindow.add_message(hitstring)
    # Broadcast the hit info to all peers, if host
    network.broadcast(network.peer.remote_print, hitstring)

@rpc(network.peer)
def remote_attempt_melee_hit(connection, time_received, src_uuid: int, tgt_uuid: int, slot: str):
    """Wrapper for calling attempt_melee_hit remotely"""
    src = network.uuid_to_char.get(src_uuid)
    tgt = network.uuid_to_char.get(tgt_uuid)
    if src and tgt:
        attempt_melee_hit(src, tgt, slot)

# HELPER FUNCTIONS
def increase_health(char, amt):
    """Function to be used whenever increasing character's health"""
    char.health = min(char.maxhealth, char.health + amt)

def reduce_health(char, amt):
    """Function to be used whenever decreasing character's health"""
    char.health -= amt

def get_melee_hit_string(src, tgt, style="fists", dmg=0, miss=False):
    """Produce a string with information about the melee hit."""
    if miss:
        return f"{src.cname} attempts to hit {tgt.cname}, but misses!"
    method = style_to_method[style]
    return f"{src.cname} {method} {tgt.cname} for {dmg} damage!"

def get_haste_modifier(haste):
    """Convert haste to a multiplicative time modifier"""
    return max(0, 1 + haste / 100)

def get_target_hittable(char, wpn):
    """Returns whether char.target is able to be hit, ie in LoS and within attack range"""
    if not char.get_tgt_los(char.target):
        ui.gamewindow.add_message(f"You can't see {char.target.cname}.")
        return False
    atk_range = get_attack_range(char, wpn)
    # use center rather than center of feet
    pos_src = char.position + Vec3(0, char.scale_y / 2, 0)
    pos_tgt = char.target.position + Vec3(0, char.target.scale_y / 2, 0)
    ray_dir = pos_tgt - pos_src
    ray_dist = distance(pos_tgt, pos_src)
    # Draw a line between the two
    line1 = raycast(pos_src, direction=ray_dir, distance=ray_dist,
                   traverse_target=char)
    line2 = raycast(pos_tgt, direction=-ray_dir, distance=ray_dist,
                    traverse_target=char.target)
    if not line1.hit or not line2.hit:
        return True
    point1 = line1.world_point
    point2 = line2.world_point

    inner_distance = distance(point1, point2)
    in_range = inner_distance <= atk_range
    if in_range:
        return True
    else:
        ui.gamewindow.add_message(f"{char.target.cname} is out of range!")
        return False

def get_wpn_dmg(char, wpn):
    if wpn is None:
        return 1
    info = wpn.get('info', {})
    return info.get('dmg', 1)

def get_wpn_style(char, wpn):
    if wpn is None:
        return 'fists'
    info = wpn.get('info', {})
    return info.get('style', 'fists')

def get_attack_range(char, wpn):
    """Equivalent to wpn['info']['range'] with some precautions"""
    if wpn is None:
        return 1
    info = wpn.get('info', {})
    return info.get('range', 1)

def get_wpn_delay(char, wpn):
    """Equivalent to wpn['info']['delay'] with some precautions"""
    if wpn is None:
        return 1
    info = wpn.get('info', {})
    return info.get('delay', 1)

@rpc(network.peer)
def remote_death(connection, time_received, char_uuid: int):
    """Tell other peers that a character died. Only to be called by host."""
    char = network.uuid_to_char.get(char_uuid)
    if char:
        char.die()
