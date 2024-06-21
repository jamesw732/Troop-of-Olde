from ursina import *
import random

from .networking.base import *

# PUBLIC
# Update this to expand CombatState
combat_state_attrs = {
    "health": int,
}

class CombatState:
    """This class is intentionally opaque to save from writing the same code
    in multiple places and needing to update several functions every time I want
    to expand this class. The entire purpose of this class is to abbreviate Character
    combat data, and make them sendable over the network. See combat_state_attrs at
    the top of this file for relevant data."""
    def __init__(self, char=None, **kwargs):
        # If a character was passed, take its attributes
        if char is not None:
            for attr in combat_state_attrs:
                if hasattr(char, attr):
                    val = getattr(char, attr)
                    # Only include attrs intentionally set
                    if val is not None:
                        setattr(self, attr, val)
        # Otherwise, read the attributes straight off
        else:
            for attr in combat_state_attrs:
                if attr in kwargs:
                    setattr(self, attr, kwargs[attr])

    def __str__(self):
        return str({attr: getattr(self, attr)
                for attr in combat_state_attrs if hasattr(self, attr)})


def attempt_melee_hit(src, tgt):
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
    style = "pummel"
    if miss:
        return f"{src.name} attempted to {style} {tgt.name}, but missed!"
    return f"{src.name} {style}s {tgt.name} for {dmg} damage!"

@rpc(network.peer)
def remote_death(connection, time_received, char_uuid: int):
    char = network.uuid_to_char.get(char_uuid)
    if char:
        char.die()