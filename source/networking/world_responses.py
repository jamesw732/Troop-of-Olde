"""These are generic RPC functions that are only called by the host.

These will typically only be called by functions in world_requests as part
of a response to a request. Otherwise, they may be called by host_continuous."""
from ursina.networking import rpc

from .network import network
from ..base import sqnorm, PHYSICS_UPDATE_RATE
from ..character import Character
from ..controllers import *
from ..item import *
from ..gamestate import gs
from ..states import State
from ..ui import UI, make_all_ui
from ..world_gen import GenerateWorld

# LOGIN
@rpc(network.peer)
def remote_generate_world(connection, time_received, zone:str):
    """Remotely generate the world"""
    gs.world = GenerateWorld(zone)

@rpc(network.peer)
def spawn_pc(connection, time_received, uuid: int, pstate: State, equipment: list[int],
             inventory: list[int], skills: State, powers: list[int], cbstate: State):
    """Does all the necessary steps to put the player character in the world, and makes the UI
    
    Parameters are typical, except for equipment and inventory. We need both the global
    item id and instance id of each item, so the first half of the list is the global
    id, the second half is the instance id.
    """
    inv_l = len(inventory)
    inventory = zip(inventory[:inv_l//2], inventory[inv_l//2:])
    equip_l = len(equipment)
    equipment = zip(equipment[:equip_l//2], equipment[equip_l//2:])
    gs.pc = Character(pstate=pstate, equipment=equipment,
                      inventory=inventory, skills=skills,
                      powers=powers, cbstate=cbstate)

    gs.playercontroller = PlayerController(gs.pc)
    gs.pc.controller = gs.playercontroller

    gs.chars.append(gs.pc)
    gs.pc.ignore_traverse = gs.chars

    network.uuid_to_char[uuid] = gs.pc
    gs.pc.uuid = uuid
    network.my_uuid = uuid
    network.server_connection = connection

    gs.ui = UI()
    make_all_ui(gs.ui)

@rpc(network.peer)
def spawn_npc(connection, time_received, uuid: int,
              phys_state: State, cbstate: State):
    """Remotely spawn a character that isn't the client's player character (could also be other players)"""
    if network.peer.is_hosting():
        return
    if uuid not in network.uuid_to_char:
        char = Character(pstate=phys_state, cbstate=cbstate)
        char.controller = NPCController(char)
        gs.chars.append(char)
        network.uuid_to_char[uuid] = char
        char.uuid = uuid

# Combat
@rpc(network.peer)
def toggle_combat(connection, time_received, toggle: bool):
    my_char = network.uuid_to_char.get(network.my_uuid)
    my_char.in_combat = toggle
    if gs.ui.gamewindow:
        msg = "Now entering combat" if toggle else "Now leaving combat"
        gs.ui.gamewindow.add_message(msg)

@rpc(network.peer)
def remote_death(connection, time_received, char_uuid: int):
    """Tell clients that a character died. Only to be called by host."""
    char = network.uuid_to_char.get(char_uuid)
    if char:
        if gs.ui.gamewindow:
            msg = f"{char.cname} perishes"
            gs.ui.gamewindow.add_message(msg)
        char.die()

@rpc(network.peer)
def remote_set_target(connection, time_received, uuid: int):
    """Update player character's target"""
    tgt = network.uuid_to_char[uuid]
    gs.pc.target = tgt
    if gs.ui.gamewindow:
        msg = f"Now targeting: {tgt.cname}"
        gs.ui.gamewindow.add_message(msg)

@rpc(network.peer)
def update_cbstate(connection, time_received, uuid: int, cbstate: State):
    char = network.uuid_to_char.get(uuid)
    if char is None:
        return
    cbstate.apply(char)
    if uuid is network.my_uuid:
        if gs.ui.bars:
            gs.ui.bars.update_display()
        if gs.ui.playerwindow:
            gs.ui.playerwindow.stats.update_labels()

# Skills
@rpc(network.peer)
def remote_update_skill(connection, time_received, skill: str, val: int):
    char = gs.pc
    char.skills[skill] = val
    if gs.ui.playerwindow:
        gs.ui.playerwindow.skills.set_label_text(skill)

# Items
@rpc(network.peer)
def remote_update_container(connection, time_received, container_name: str, container: list[int]):
    """Update internal containers and visual containers

    Mimic most of the process in ItemIcon.swap_locs for hosts, but
    this will only be done by non-hosts"""
    if network.peer.is_hosting():
        return
    new_container = ids_to_container(container)

    for slot, item in enumerate(new_container):
        internal_move_item(gs.pc, item, container_name, slot, "nowhere", handle_stats=False)

    item_frame = gs.ui.item_frames.get(container_name)
    if item_frame:
        item_frame.update_ui_icons()

# Physical
@rpc(network.peer)
def update_lerp_pstate(connection, time_received, uuid: int, phys_state: State):
    """Called by server to update physical state for an NPC"""
    npc = network.uuid_to_char.get(uuid)
    if npc is None:
        return
    npc.controller.update_lerp_state(phys_state, time_received)

@rpc(network.peer)
def update_target_attrs(connection, time_received, sequence_number: int, pos: Vec3, rot: float):
    """Called by server to update physical state for a player character"""
    if gs.pc is None:
        return
    # To check synchronization, uncomment these:
    # print(rot % 360)
    # print(gs.pc.rotation_y)
    # print(pos)
    # print(gs.pc.position)
    controller = gs.pc.controller
    if sequence_number > controller.recv_sequence_number:
        controller.recv_sequence_number = sequence_number
        for num in controller.sn_to_pos.copy():
            if num < sequence_number:
                controller.sn_to_pos.pop(num)
                controller.sn_to_rot.pop(num)
    else:
        # Always take the most recent sequence number
        # Alternatively, reject completely if it's old
        sequence_number = controller.recv_sequence_number
    # controller.shadow.position = pos
    # controller.shadow.rotation_y = rot
    # Compute the offset amt for position
    # sn_to_pos is missing sequence_number on startup
    predicted_pos = controller.sn_to_pos.get(sequence_number, pos)
    pos_offset = pos - predicted_pos
    controller.character.displacement_components["server_offset"] = pos_offset
    # Compute the offset amt for rotation
    rot = rot % 360
    predicted_rot = controller.sn_to_rot.get(sequence_number, rot)
    rot_offset = rot - predicted_rot
    controller.rot_offset = rot_offset

@rpc(network.peer)
def update_pos_rot(connection, time_received, uuid: int, pos: Vec3, rot: Vec3):
    char = network.uuid_to_char.get(uuid)
    if char is None:
        return
    char.position = pos
    char.rotation = rot
             
@rpc(network.peer)
def update_rotation(connection, time_received, uuid: int, rot: Vec3):
    char = network.uuid_to_char.get(uuid)
    if char is None:
        return
    char.rotation = rot

# Generic
@rpc(network.peer)
def remote_print(connection, time_received, msg: str):
    """Remotely print a message for another player"""
    if gs.ui and gs.ui.gamewindow:
        gs.ui.gamewindow.add_message(msg)
