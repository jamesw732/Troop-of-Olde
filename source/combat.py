from ursina import time, ceil
from ursina.networking import rpc
import random

from .base import sigmoid, sqdist, fists_base_dmg, style_to_method
from .networking.base import network
from .ui.main import ui

# PUBLIC
def progress_mh_combat_timer(char):
    """Increment combat timer by dt. If past max, attempt a melee hit."""
    # Add time.dt to combat timer, if flows over max, attempt hit and subtract max
    char.mh_combat_timer += time.dt * get_haste_modifier(char.haste)
    if char.mh_combat_timer > char.max_mh_combat_timer:
        char.mh_combat_timer -= char.max_mh_combat_timer
        if get_target_hittable(char):
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
    if char.oh_combat_timer > char.max_oh_combat_timer:
        char.oh_combat_timer -= char.max_oh_combat_timer
        if get_target_hittable(char):
            if network.is_main_client():
                attempt_melee_hit(char, char.target, "oh")
            else:
                # Host-authoritative, so we need to ask the host to compute the hit
                network.peer.remote_attempt_melee_hit(
                    network.peer.get_connections()[0],
                    char.uuid, char.target.uuid, "oh")


def increase_health(char, amt):
    """Function to be used whenever increasing character's health"""
    char.health = min(char.maxhealth, char.health + amt)

def reduce_health(char, amt):
    """Function to be used whenever decreasing character's health"""
    char.health -= amt

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
        if wep is None:
            # Use fists
            base_dmg = fists_base_dmg
            style = "fists"
        else:
            if "info" not in wep:
                ui.gamewindow.add_message(f"Try hitting {target.cname} with something else.")
                return
            # Assume from now on that the weapon has everything needed
            base_dmg = wep["info"]["dmg"]
            style = wep["info"]["style"]
        base_dmg *= 2 * sigmoid(src.str - tgt.armor)
        min_hit = ceil(base_dmg * 0.5)
        max_hit = ceil(base_dmg * 1.5)
        dmg = random.randint(min_hit, max_hit)
        hitstring = get_melee_hit_string(src, tgt, style=style, dmg=dmg)
        reduce_health(tgt, dmg)
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

def get_haste_modifier(haste):
    """Convert haste to a multiplicative time modifier"""
    return max(0, 1 + haste / 100)

def get_melee_hit_string(src, tgt, style="fists", dmg=0, miss=False):
    """Produce a string with information about the melee hit."""
    if miss:
        return f"{src.cname} attempts to hit {tgt.cname}, but misses!"
    method = style_to_method[style]
    return f"{src.cname} {method} {tgt.cname} for {dmg} damage!"

@rpc(network.peer)
def remote_death(connection, time_received, char_uuid: int):
    """Tell other peers that a character died. Only to be called by host."""
    char = network.uuid_to_char.get(char_uuid)
    if char:
        char.die()

def get_target_hittable(char):
    """Returns whether char.target is able to be hit, ie in LoS and within attack range"""
    in_range = sqdist(char.position, char.target.position) < char.attackrange ** 2
    return in_range and char.get_tgt_los(char.target)