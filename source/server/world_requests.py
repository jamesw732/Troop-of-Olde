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
def request_enter_world(connection, time_received, login_state: LoginState):
    """Add a new player character to the world and update all clients.
    Expected inputs are the outputs of get_pc_data_from_json"""
    init_dict = world.make_char_init_dict(login_state)
    new_pc = world.make_char(init_dict)
    new_ctrl = world.make_ctrl(new_pc.uuid)
    network.uuid_to_connection[new_pc.uuid] = connection
    network.connection_to_uuid[connection] = new_pc.uuid
    network.peer.remote_load_world(connection, "demo.json")
    # State for new character sent to this client
    new_pc_spawn_state = PCSpawnState(new_pc)
    # State for new character sent to other clients
    new_npc_spawn_state = NPCSpawnState(new_pc)
    # Need to update all clients
    for conn in network.peer.get_connections():
        if conn == connection:
            # Send over PC and all NPC's
            for uuid, ch in world.uuid_to_char.items():
                if uuid == new_pc.uuid:
                    network.peer.spawn_pc(connection, new_pc_spawn_state)
                else:
                    npc_spawn_state = NPCSpawnState(ch)
                    network.peer.spawn_npc(conn, npc_spawn_state)
        else:
            # Existing users just need new character
            network.peer.spawn_npc(conn, new_npc_spawn_state)

# PHYSICS
@rpc(network.peer)
def request_move(connection, time_received, sequence_number: int, kb_direction: Vec2,
                 kb_y_rotation: int, mouse_y_rotation: float):
    """Request server to process keyboard inputs for movement and rotation"""
    uuid = network.connection_to_uuid[connection]
    controller = world.uuid_to_ctrl[uuid]
    controller.handle_movement_inputs(sequence_number, kb_direction, kb_y_rotation, mouse_y_rotation)

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
def request_swap_items(connection, time_received, to_container_id: int, to_slot: int,
                       from_container_id: int, from_slot: int):
    """Request host to swap items internally, host will send back updated container states"""
    if not network.peer.is_hosting():
        return
    uuid = network.connection_to_uuid[connection]
    char = world.uuid_to_char[uuid]
    to_container = world.inst_id_to_container[to_container_id]
    from_container = world.inst_id_to_container[from_container_id]
    char.container_swap_locs(to_container, to_slot, from_container, from_slot)
    unique_containers = {to_container_id: to_container, from_container_id: from_container}
    for container_id, container in unique_containers.items():
        container = world.container_to_ids(container) # add method to serialize
        network.peer.remote_update_container(connection, container_id, container)
    network.broadcast_cbstate_update(char)
