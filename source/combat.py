from ursina import time
from ursina.networking import rpc
import random

from .base import sigmoid, sqdist
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
                attempt_melee_hit(char, char.target)
            else:
                # Host-authoritative, so we need to ask the host to compute the hit
                network.peer.remote_attempt_melee_hit(
                    network.peer.get_connections()[0],
                    char.uuid, char.target.uuid)

def progress_oh_combat_timer(char):
    """Increment combat timer by dt. If past max, attempt a melee hit."""
    # Add time.dt to combat timer, if flows over max, attempt hit and subtract max
    char.oh_combat_timer += time.dt * get_haste_modifier(char.haste) # * dw_skill / rec_level if slot == oh else 1
    if char.oh_combat_timer > char.max_oh_combat_timer:
        char.oh_combat_timer -= char.max_oh_combat_timer
        if get_target_hittable(char):
            if network.is_main_client():
                attempt_melee_hit(char, char.target)
            else:
                # Host-authoritative, so we need to ask the host to compute the hit
                network.peer.remote_attempt_melee_hit(
                    network.peer.get_connections()[0],
                    char.uuid, char.target.uuid)


def increase_health(char, amt):
    """Function to be used whenever increasing character's health"""
    char.health = min(char.maxhealth, char.health + amt)

def reduce_health(char, amt):
    """Function to be used whenever decreasing character's health"""
    char.health -= amt

# PRIVATE
def attempt_melee_hit(src, tgt):
    """Main driver method for melee combat.
    Melee combat in other files should only import this method and remote version.
    Only main client (ie host or offline client) should call this. If not main client,
    call remote version."""
    # Do a bunch of fancy evasion and accuracy calculations to determine if hit goes through
    if random.random() < sigmoid((src.dex - tgt.ref) / 10):
        # It's a miss
        hitstring = get_melee_hit_string(src, tgt, miss=True)
    else:
        # If hit goes through, do some more fancy calculations to get damage
        dmg = get_dmg(src, tgt)
        hitstring = get_melee_hit_string(src, tgt, dmg=dmg)
        reduce_health(tgt, dmg)
    ui.gamewindow.add_message(hitstring)
    # Broadcast the hit info to all peers, if host
    network.broadcast(network.peer.remote_print, hitstring)


@rpc(network.peer)
def remote_attempt_melee_hit(connection, time_received, src_uuid: int, tgt_uuid: int):
    """Calls attempt_melee_hit remotely"""
    src = network.uuid_to_char.get(src_uuid)
    tgt = network.uuid_to_char.get(tgt_uuid)
    if src and tgt:
        attempt_melee_hit(src, tgt)


def get_haste_modifier(haste):
    """Convert haste to a multiplicative time modifier"""
    return max(0, 1 + haste / 100)

def get_dmg(src, tgt):
    """Get damage from reading source and target's stats"""
    # Damage is uniform from min to max
    min_hit = 5 + src.str
    max_hit = 15 + src.str
    dmg = random.randint(min_hit, max_hit)
    return dmg

def get_melee_hit_string(src, tgt, dmg=0, miss=False):
    """Produce a string with information about the melee hit."""
    style = "pummel"
    if miss:
        return f"{src.cname} attempted to {style} {tgt.cname}, but missed!"
    return f"{src.cname} {style}s {tgt.cname} for {dmg} damage!"

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