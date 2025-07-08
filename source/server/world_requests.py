"""This file contains generic RPC functions that are only called by the client.

Perhaps counterintuitively, all the function definitions will be executed on the host's
machine, not the client. They are *called* client side, though.
These are essentially networking wrappers for procedures done by the server. If a client
needs something done by the server, they call a function from here."""
from ursina.networking import rpc

from .character import ServerCharacter
from .controllers import MobController
from .world import world
from .world_responses import *
from .. import *


# LOGIN
@rpc(network.peer)
def request_enter_world(connection, time_received, pstate: PhysicalState,
                        base_state: BaseCombatState, equipment: list[int],
                        inventory: list[int], skills: SkillsState,
                        powers: list[int]):
    new_pc = world.make_char(pstate=pstate, cbstate=base_state, equipment=equipment,
                             inventory=inventory, skills=skills, powers=powers)
    new_ctrl = world.make_ctrl(new_pc.uuid)
    network.uuid_to_connection[new_pc.uuid] = connection
    network.connection_to_char[connection] = new_pc
    network.peer.remote_load_world(connection, "demo.json")
    # extend instance id-based objects to include database id and instance id
    inventory_ids = network.container_to_ids(new_pc.inventory, ("item_id", "inst_id"))
    inventory_ids = [new_pc.inventory.container_id] + inventory_ids
    equipment_ids = network.container_to_ids(new_pc.equipment, ("item_id", "inst_id"))
    equipment_ids = [new_pc.equipment.container_id] + equipment_ids
    power_ids = network.container_to_ids(new_pc.powers, ("power_id", "inst_id"))
    # The new pc will be an npc for everybody else
    new_char_cbstate = NPCCombatState(new_pc)
    for conn in network.peer.get_connections():
        if conn == connection:
            for uuid, ch in network.uuid_to_char.items():
                if ch is new_pc:
                    pc_cbstate = PlayerCombatState(new_pc)
                    network.peer.spawn_pc(connection, uuid, pstate, equipment_ids,
                                          inventory_ids, skills, power_ids, pc_cbstate)
                else:
                    npc_pstate = PhysicalState(ch)
                    npc_cbstate = NPCCombatState(ch)
                    network.peer.spawn_npc(conn, uuid, npc_pstate, npc_cbstate)
        # Existing users just need new character
        else:
            network.peer.spawn_npc(conn, new_pc.uuid, pstate, new_char_cbstate)

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
    controller = network.uuid_to_ctrl[char.uuid]
    if sequence_number > controller.sequence_number:
        controller.sequence_number = sequence_number

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
def request_swap_items(connection, time_received, to_id: int, to_slot: int,
                       from_id: int, from_slot: int):
    """Request host to swap items internally, host will send back updated container states"""
    if not network.peer.is_hosting():
        return
    char = network.connection_to_char[connection]
    to_container = network.inst_id_to_container[to_id]
    from_container = network.inst_id_to_container[from_id]
    full_item_move(char, to_container, to_slot, from_container, from_slot)
    unique_containers = {to_id: to_container, from_id: from_container}
    for container_id, container in unique_containers.items():
        container = network.container_to_ids(container)
        network.peer.remote_update_container(connection, container_id, container)
        network.broadcast_cbstate_update(char)

@rpc(network.peer)
def request_auto_equip(connection, time_received, itemid: int, slot: int, container_id: int):
    """Request host to automatically equip an item."""
    char = network.connection_to_char[connection]
    container = network.inst_id_to_container[container_id]
    internal_autoequip(char, container, slot)
    for container in [container, char.equipment]:
        container_id = container.container_id
        container = network.container_to_ids(container)
        network.peer.remote_update_container(connection, container_id, container)
        network.broadcast_cbstate_update(char)

@rpc(network.peer)
def request_auto_unequip(connection, time_received, itemid: int, slot: int):
    """Request host to automatically unequip an item."""
    char = network.connection_to_char[connection]
    internal_autounequip(char, slot)
    for container in [char.equipment, char.inventory]:
        container_id = container.container_id
        container = network.container_to_ids(container)
        network.peer.remote_update_container(connection, container_id, container)
        network.broadcast_cbstate_update(char)

