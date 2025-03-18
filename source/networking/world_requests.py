"""This file contains generic RPC functions that are only called by the client.

Perhaps counterintuitively, all the function definitions will be executed on the host's
machine, not the client. They are *called* client side, though.
These are essentially networking wrappers for procedures done by the server. If a client
needs something done by the server, they call a function from here."""
from ursina.networking import rpc

from . import network
from .world_responses import *
from ..item import *
from ..states.physicalstate import PhysicalState, apply_physical_state

# COMBAT
@rpc(network.peer)
def request_toggle_combat(connection, time_received):
    char = network.connection_to_char[connection]
    char.in_combat = not char.in_combat
    network.peer.toggle_combat(connection, char.in_combat)
    # Could respond, or could just wait for next continuous update

@rpc(network.peer)
def request_set_target(connection, time_received, uuid: int):
    src = network.connection_to_char[connection]
    tgt = network.uuid_to_char[uuid]
    src.target = tgt
    network.peer.remote_set_target(connection, uuid)

# POWERS
@rpc(network.peer)
def request_use_power(connection, time_received, uuid: int, page: str, slot: str):
    char = network.uuid_to_char[uuid]
    power = getattr(char, page).get(slot, None)
    if power is not None:
        power.apply_effect()

# ITEMS
@rpc(network.peer)
def request_swap_items(connection, time_received, container1: str, slot1: str, container2: str, slot2: str):
    """Request host to swap items internally, host will send back updated container states"""
    if not network.peer.is_hosting():
        return
    char = network.connection_to_char[connection]
    internal_swap(char, container1, slot1, container2, slot2)
    for name in set([container1, container2]):
        container = container_to_ids(getattr(char, name))
        network.peer.remote_update_container(connection, name, container)

@rpc(network.peer)
def request_auto_equip(connection, time_received, itemid: int, old_slot: str, old_container: str):
    """Request host to automatically equip a given item."""
    char = network.connection_to_char[connection]
    iauto_equip(char, old_container, old_slot)
    for name in set([old_container, "equipment"]):
        container = container_to_ids(getattr(char, name))
        network.peer.remote_update_container(connection, name, container)

@rpc(network.peer)
def request_auto_unequip(connection, time_received, itemid: int, old_slot: str):
    """Request host to automatically unequip a given item."""
    char = network.connection_to_char[connection]
    iauto_unequip(char, old_slot)
    for name in ["equipment", "inventory"]:
        container = container_to_ids(getattr(char, name))
        network.peer.remote_update_container(connection, name, container)

# State Updates
@rpc(network.peer)
def request_update_pstate(connection, time_received, uuid: int,
                       phys_state: PhysicalState):
    """Client-authoritatively apply physical state updates.
    Don't apply new state directly, instead add it as the new LERP state.
    Host will broadcast the new state to all other peers.
    """
    char = network.uuid_to_char.get(uuid, None)
    if char is None:
        return
    apply_physical_state(char, phys_state)
    if network.peer.is_hosting():
        for conn in network.peer.get_connections():
            if conn is not connection:
                network.peer.update_lerp_pstate(conn, uuid, phys_state)
