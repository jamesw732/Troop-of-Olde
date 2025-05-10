"""This file contains generic RPC functions that are only called by the client.

Perhaps counterintuitively, all the function definitions will be executed on the host's
machine, not the client. They are *called* client side, though.
These are essentially networking wrappers for procedures done by the server. If a client
needs something done by the server, they call a function from here."""
from ursina.networking import rpc

from .network import network
from .world_responses import *
from ..character import Character
from ..controllers import *
from ..item import *
from ..gamestate import gs
from ..power import Power
from ..states.state import State

# LOGIN
@rpc(network.peer)
def request_enter_world(connection, time_received, pstate: State,
                        base_state: State, equipment: IdContainer,
                        inventory: IdContainer, skills: State,
                        lexicon: IdContainer):
    if network.peer.is_hosting():
        new_pc = Character(pstate=pstate, cbstate=base_state,
                         equipment=equipment, inventory=inventory, skills=skills,
                         lexicon=lexicon)
        new_pc.controller = MobController(new_pc)
        # Could we handle this uuid business in on_connect?
        new_pc.uuid = network.uuid_counter
        network.uuid_counter += 1
        network.uuid_to_char[new_pc.uuid] = new_pc
        network.uuid_to_connection[new_pc.uuid] = connection
        gs.chars.append(new_pc)
        network.connection_to_char[connection] = new_pc
        network.peer.remote_generate_world(connection, "demo.json")
        # The new pc will be an npc for everybody else
        new_pc_cbstate = State("npc_combat", new_pc)
        for conn in network.peer.get_connections():
            if conn == connection:
                for ch in gs.chars:
                    if ch is new_pc:
                        pc_cbstate = State("pc_combat", new_pc)
                        network.peer.spawn_pc(connection, new_pc.uuid, pstate, equipment,
                                              inventory, skills, lexicon, pc_cbstate)
                    else:
                        npc_pstate = State("physical", ch)
                        npc_cbstate = State("npc_combat", ch)
                        network.peer.spawn_npc(conn, ch.uuid, npc_pstate, npc_cbstate)
            # Existing users just need new character
            else:
                network.peer.spawn_npc(conn, new_pc.uuid, pstate, new_pc_cbstate)
        network.peer.make_ui(connection)
        # Send over instantiated item id's
        inst_inventory = IdContainer({k: item.iiid for k, item
                          in new_pc.inventory.items() if item is not None})
        inst_equipment = IdContainer({k: item.iiid for k, item
                          in new_pc.equipment.items() if item is not None})
        network.peer.bind_pc_items(connection, inst_inventory, inst_equipment)
        network.broadcast_cbstate_update(new_pc)


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
def request_use_power(connection, time_received, power_id: int):
    char = network.connection_to_char[connection]
    power = Power(power_id)
    if power is not None:
        msg = power.apply_effect(char, char.target)
        if msg:
            network.broadcast(network.peer.remote_print, msg)

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
        network.broadcast_cbstate_update(char)

@rpc(network.peer)
def request_auto_equip(connection, time_received, itemid: int, old_slot: str, old_container: str):
    """Request host to automatically equip a given item."""
    char = network.connection_to_char[connection]
    iauto_equip(char, old_container, old_slot)
    for name in set([old_container, "equipment"]):
        container = container_to_ids(getattr(char, name))
        network.peer.remote_update_container(connection, name, container)
        network.broadcast_cbstate_update(char)

@rpc(network.peer)
def request_auto_unequip(connection, time_received, itemid: int, old_slot: str):
    """Request host to automatically unequip a given item."""
    char = network.connection_to_char[connection]
    iauto_unequip(char, old_slot)
    for name in ["equipment", "inventory"]:
        container = container_to_ids(getattr(char, name))
        network.peer.remote_update_container(connection, name, container)
        network.broadcast_cbstate_update(char)

# State Updates
@rpc(network.peer)
def request_update_pstate(connection, time_received, uuid: int,
                       phys_state: State):
    """Client-authoritatively apply physical state updates.
    Don't apply new state directly, instead add it as the new LERP state.
    Host will broadcast the new state to all other peers.
    """
    char = network.uuid_to_char.get(uuid, None)
    if char is None:
        return
    phys_state.apply(char)
    if network.peer.is_hosting():
        for conn in network.peer.get_connections():
            if conn is not connection:
                network.peer.update_lerp_pstate(conn, uuid, phys_state)


