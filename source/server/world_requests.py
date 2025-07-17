"""This file contains generic RPC functions that are only called by the client.

Perhaps counterintuitively, all the function definitions will be executed on the host's
machine, not the client. They are *called* client side, though.
These are essentially networking wrappers for procedures done by the server. If a client
needs something done by the server, they call a function from here."""
from ursina.networking import rpc

from .character import ServerCharacter
from .controllers import MobController
from .world import world
from .. import *


# LOGIN
@rpc(network.peer)
def request_enter_world(connection, time_received, pstate: PhysicalState,
                        base_state: BaseCombatState, equipment: list[int],
                        inventory: list[int], skills: SkillsState,
                        powers: list[int]):
    """Add a new player character to the world and update all clients.
    Expected inputs are the outputs of get_pc_data_from_json"""
    new_pc = world.make_char(pstate=pstate, cbstate=base_state, equipment=equipment,
                             inventory=inventory, skills=skills, powers=powers)
    new_ctrl = world.make_ctrl(new_pc.uuid)
    network.uuid_to_connection[new_pc.uuid] = connection
    network.connection_to_uuid[connection] = new_pc.uuid
    network.peer.remote_load_world(connection, "demo.json")
    # extend instance id-based objects to include database id and instance id
    inventory_ids = world.container_to_ids(new_pc.inventory, ("item_id", "inst_id"))
    inventory_ids = [new_pc.inventory.container_id] + inventory_ids
    equipment_ids = world.container_to_ids(new_pc.equipment, ("item_id", "inst_id"))
    equipment_ids = [new_pc.equipment.container_id] + equipment_ids
    power_ids = world.container_to_ids(new_pc.powers, ("power_id", "inst_id"))
    # The new pc will be an npc for everybody else
    new_char_cbstate = NPCCombatState(new_pc)
    for conn in network.peer.get_connections():
        if conn == connection:
            for uuid, ch in world.uuid_to_char.items():
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
    uuid = network.connection_to_uuid[connection]
    char = world.uuid_to_char[uuid]
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
    controller = world.uuid_to_ctrl[char.uuid]
    if sequence_number > controller.sequence_number:
        controller.sequence_number = sequence_number
    if kb_direction != Vec2(0, 0) and controller.moving == False:
        controller.moving = True
        for conn, uuid in network.connection_to_uuid.items():
            if char.uuid != uuid:
                network.peer.remote_start_run_anim(conn, char.uuid)
    elif kb_direction == Vec2(0, 0) and controller.moving == True:
        controller.moving = False
        for conn, uuid in network.connection_to_uuid.items():
            if char.uuid != uuid:
                network.peer.remote_start_idle_anim(conn, char.uuid)

@rpc(network.peer)
def request_jump(connection, time_received):
    uuid = network.connection_to_uuid[connection]
    char = world.uuid_to_char[uuid]
    char.start_jump()

# COMBAT
@rpc(network.peer)
def request_toggle_combat(connection, time_received):
    uuid = network.connection_to_uuid[connection]
    char = world.uuid_to_char[uuid]
    char.in_combat = not char.in_combat
    network.peer.toggle_combat(connection, char.uuid, char.in_combat)
    # Could respond, or could just wait for next continuous update

@rpc(network.peer)
def request_set_target(connection, time_received, uuid: int):
    src_uuid = network.connection_to_uuid[connection]
    src = world.uuid_to_char[src_uuid]
    tgt = world.uuid_to_char[uuid]
    src.set_target(tgt)
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
    uuid = network.connection_to_uuid[connection]
    char = world.uuid_to_char[uuid]
    ctrl = world.uuid_to_ctrl[char.uuid]
    power = world.inst_id_to_power[inst_id]
    ctrl.use_power(power)


# ITEMS
@rpc(network.peer)
def request_swap_items(connection, time_received, to_id: int, to_slot: int,
                       from_id: int, from_slot: int):
    """Request host to swap items internally, host will send back updated container states"""
    if not network.peer.is_hosting():
        return
    uuid = network.connection_to_uuid[connection]
    char = world.uuid_to_char[uuid]
    to_container = world.inst_id_to_container[to_id]
    from_container = world.inst_id_to_container[from_id]
    full_item_move(char, to_container, to_slot, from_container, from_slot)
    unique_containers = {to_id: to_container, from_id: from_container}
    for container_id, container in unique_containers.items():
        container = world.container_to_ids(container)
        network.peer.remote_update_container(connection, container_id, container)
        network.broadcast_cbstate_update(char)

@rpc(network.peer)
def request_auto_equip(connection, time_received, itemid: int, slot: int, container_id: int):
    """Request host to automatically equip an item."""
    uuid = network.connection_to_uuid[connection]
    char = world.uuid_to_char[uuid]
    from_container = world.inst_id_to_container[container_id]
    internal_autoequip(char, from_container, slot)
    for container in [from_container, char.equipment]:
        container_id = container.container_id
        container = world.container_to_ids(container)
        network.peer.remote_update_container(connection, container_id, container)
        network.broadcast_cbstate_update(char)

@rpc(network.peer)
def request_auto_unequip(connection, time_received, itemid: int, slot: int):
    """Request host to automatically unequip an item."""
    uuid = network.connection_to_uuid[connection]
    char = world.uuid_to_char[uuid]
    internal_autounequip(char, slot)
    for container in [char.equipment, char.inventory]:
        container_id = container.container_id
        container = world.container_to_ids(container)
        network.peer.remote_update_container(connection, container_id, container)
        network.broadcast_cbstate_update(char)

