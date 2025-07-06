"""This file contains the interface for all networking requests. These are functions called
by the client, executed by the server. We don't need the implementation client-side, so we
don't include it."""
from ursina.networking import rpc

from ..networking.network import network
from ..states import *

# LOGIN
@rpc(network.peer)
def request_enter_world(connection, time_received, pstate: PhysicalState,
                        base_state: BaseCombatState, equipment: list[int],
                        inventory: list[int], skills: SkillsState,
                        powers: list[int]):
    pass

# PHYSICS
@rpc(network.peer)
def request_move(connection, time_received, sequence_number: int, kb_direction: Vec2,
                 kb_y_rotation: int, mouse_y_rotation: float):
    """Request server to process keyboard inputs for movement and rotation"""
    pass

@rpc(network.peer)
def request_jump(connection, time_received):
    pass

def request_toggle_combat(connection, time_received):
    pass

def request_set_target(connection, time_received, uuid: int):
    pass

def request_use_power(connection, time_received, inst_id: int):
    """Function called to use or queue a power.

    This function is called when a player clicks a power button while their character is not on GCD.
    If the character is on GCD, then it's better to not call this function, and instead let the client
    handle it in case there's another input, until the GCD is over. This function is called upon GCD end.

    Will eventually want to make the above more sophisticated with client-side prediction, but this is
    good enough for now.
    """
    pass

def request_swap_items(connection, time_received, to_id: int, to_slot: int,
                       from_id: int, from_slot: int):
    """Request host to swap items internally, host will send back updated container states"""
    pass

def request_auto_equip(connection, time_received, itemid: int, slot: int, container_id: int):
    """Request host to automatically equip an item."""
    pass

def request_auto_unequip(connection, time_received, itemid: int, slot: int):
    """Request host to automatically unequip an item."""
    pass


