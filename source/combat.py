from ursina import *
import random

from .networking.base import *

# PUBLIC
def attempt_melee_hit(src, tgt):
    """Main driver method for melee combat.
    Melee combat in other files should only import this method and remote version.
    Only main client (ie host or offline client) should call this. If not main client,
    call remote version."""
    # Do a bunch of fancy evasion and accuracy calculations to determine if hit goes through
    if random.random() < 0.2:
        # It's a miss
        hitstring = get_melee_hit_string(src, tgt, miss=True)
    else:
        # If hit goes through, do some more fancy calculations to get damage
        dmg = get_dmg(src, tgt)
        hitstring = get_melee_hit_string(src, tgt, dmg=dmg)
        tgt.reduce_health(dmg)
    print(hitstring)
    # Broadcast the hit info to all peers, if host
    broadcast(network.peer.remote_print, hitstring)


@rpc(network.peer)
def remote_attempt_melee_hit(connection, time_received, src_uuid: int, tgt_uuid: int):
    """Calls attempt_melee_hit remotely"""
    src = network.uuid_to_char.get(src_uuid)
    tgt = network.uuid_to_char.get(tgt_uuid)
    if src and tgt:
        attempt_melee_hit(src, tgt)


# PRIVATE
def get_dmg(src, tgt):
    """Get damage from reading source and target's stats"""
    # Damage is uniform from min to max
    min_hit = 5
    max_hit = 15
    dmg = random.randint(min_hit, max_hit)
    return dmg

def get_melee_hit_string(src, tgt, dmg=0, miss=False):
    """Produce a string with information about the melee hit."""
    style = "pummel"
    if miss:
        return f"{src.name} attempted to {style} {tgt.name}, but missed!"
    return f"{src.name} {style}s {tgt.name} for {dmg} damage!"

@rpc(network.peer)
def remote_death(connection, time_received, char_uuid: int):
    """Tell other peers that a character died. Only to be called by host."""
    char = network.uuid_to_char.get(char_uuid)
    if char:
        char.die()