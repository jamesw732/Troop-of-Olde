"""This file contains generic RPC functions that are only called by the client.

Perhaps counterintuitively, all the function definitions will be executed on the host's
machine, not the client. They are *called* client side, though.
These are essentially networking wrappers for procedures done by the server. If a client
needs something done by the server, they call a function from here."""
from ursina.networking import rpc

from .network import network
from .world_responses import *
from ..character import ServerCharacter
from ..controllers import *
from ..item import *
from ..gamestate import gs
from ..states import State, container_to_ids

# LOGIN
@rpc(network.peer)
def request_enter_world(connection, time_received, pstate: State,
                        base_state: State, equipment: list[int],
                        inventory: list[int], skills: State,
                        powers: list[int]):
    if network.peer.is_hosting():
        new_pc = ServerCharacter(pstate=pstate, cbstate=base_state,
                         equipment=equipment, inventory=inventory, skills=skills,
                         powers=powers)
        new_pc.controller = MobController(new_pc)
        # Could we handle this uuid business in on_connect?
        new_pc.uuid = network.uuid_counter
        network.uuid_counter += 1
        network.uuid_to_char[new_pc.uuid] = new_pc
        network.uuid_to_connection[new_pc.uuid] = connection
        gs.chars.append(new_pc)
        network.connection_to_char[connection] = new_pc
        network.peer.remote_generate_world(connection, "demo.json")
        # extend instance id-based objects to include database id and instance id
        inventory_ids = container_to_ids(new_pc.inventory, ("item_id", "inst_id"))
        inventory_ids = [new_pc.inventory.container_id] + inventory_ids
        equipment_ids = container_to_ids(new_pc.equipment, ("item_id", "inst_id"))
        equipment_ids = [new_pc.equipment.container_id] + equipment_ids
        power_ids = container_to_ids(new_pc.powers, ("power_id", "inst_id"))
        # The new pc will be an npc for everybody else
        new_pc_cbstate = State("npc_combat", new_pc)
        for conn in network.peer.get_connections():
            if conn == connection:
                for ch in gs.chars:
                    if ch is new_pc:
                        pc_cbstate = State("pc_combat", new_pc)
                        network.peer.spawn_pc(connection, new_pc.uuid, pstate, equipment_ids,
                                              inventory_ids, skills, power_ids, pc_cbstate)
                    else:
                        npc_pstate = State("physical", ch)
                        npc_cbstate = State("npc_combat", ch)
                        network.peer.spawn_npc(conn, ch.uuid, npc_pstate, npc_cbstate)
            # Existing users just need new character
            else:
                network.peer.spawn_npc(conn, new_pc.uuid, pstate, new_pc_cbstate)

# PHYSICS
@rpc(network.peer)
def request_move(connection, time_received, sequence_number: int, kb_direction: Vec2,
                 kb_y_rotation: int, mouse_y_rotation: float):
    """Request server to process keyboard inputs for movement and rotation"""
    char = network.connection_to_char[connection]
    char_speed = get_speed_modifier(char.speed)
    vel = (char.right * kb_direction[0] + char.forward * kb_direction[1]).normalized() * 10 * char_speed
    if "keyboard" not in char.velocity_components:
        char.velocity_components["keyboard"] = vel
    char.velocity_components["keyboard"] += vel
    # char_rotation = Vec3(0, kb_y_rotation[1] * 100 * math.cos(math.radians(self.focus.rotation_x)), 0)
    y_rotation = kb_y_rotation * 100 * PHYSICS_UPDATE_RATE + mouse_y_rotation
    char.rotation_y += y_rotation
    # Will send back the most recently received sequence number to match the predicted state.
    # If packets arrive out of order, we want to update based on last sequence number
    if sequence_number > char.controller.sequence_number:
        char.controller.sequence_number = sequence_number

@rpc(network.peer)
def request_jump(connection, time_received):
    char = network.connection_to_char[connection]
    char.start_jump()

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
def request_use_power(connection, time_received, inst_id: int):
    """Function called to use or queue a power.

    This function is called when a player clicks a power button while their character is not on GCD.
    If the character is on GCD, then it's better to not call this function, and instead let the client
    handle it in case there's another input, until the GCD is over. This function is called upon GCD end.

    Will eventually want to make the above more sophisticated with client-side prediction, but this is
    good enough for now.
    """
    char = network.connection_to_char[connection]
    power = network.inst_id_to_power[inst_id]
    if char.get_on_gcd():
        power.queue()
        return
    # Eventually, may incorporate auto-targetting with power.get_target.
    tgt = power.get_target()
    power.use(tgt)
    # Once auto-targetting is implemented, send back new target
    # May also need to send back some info to help with client-side prediction
    # Likewise in request_queue_power


# ITEMS
@rpc(network.peer)
def request_swap_items(connection, time_received, container1_id: int, slot1: int,
                       container2_id: int, slot2: int):
    """Request host to swap items internally, host will send back updated container states"""
    if not network.peer.is_hosting():
        return
    char = network.connection_to_char[connection]
    internal_swap(char, container1_id,  slot1, container2_id, slot2)
    unique_containers = {container_id: network.inst_id_to_container[container_id]
                         for container_id in [container1_id, container2_id]}
    for container_id, container in unique_containers.items():
        container = container_to_ids(container)
        network.peer.remote_update_container(connection, container_id, container)
        network.broadcast_cbstate_update(char)

@rpc(network.peer)
def request_auto_equip(connection, time_received, itemid: int, slot: int, container_id: int):
    """Request host to automatically equip an item."""
    char = network.connection_to_char[connection]
    container = network.inst_id_to_container[container_id]
    container_name = container.name
    iauto_equip(char, container_name, slot)
    for container in [container, char.equipment]:
        container_id = container.container_id
        container = container_to_ids(container)
        network.peer.remote_update_container(connection, container_id, container)
        network.broadcast_cbstate_update(char)

@rpc(network.peer)
def request_auto_unequip(connection, time_received, itemid: int, slot: int):
    """Request host to automatically unequip an item."""
    char = network.connection_to_char[connection]
    iauto_unequip(char, slot)
    for container in [char.equipment, char.inventory]:
        container_id = container.container_id
        container = container_to_ids(container)
        network.peer.remote_update_container(connection, container_id, container)
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


