"""These are generic RPC functions that are only called by the host.

These will typically only be called by functions in world_requests as part
of a response to a request. Otherwise, they may be called by host_continuous."""
from ursina.networking import rpc

from .world import world
from .ui import ui
from .. import *

# Login/Character Creation
@rpc(network.peer)
def remote_load_world(connection, time_received, zone:str):
    """Remotely generate the world"""
    world.load_zone(zone)

@rpc(network.peer)
def spawn_pc(connection, time_received, uuid: int, pstate: PhysicalState, equipment: list[int],
             inventory: list[int], skills: list[int], powers: list[int], cbstate: PlayerCombatState):
    """Does all the necessary steps to put the player character in the world, and makes the UI
    
    uuid: unique id of new Character, used to refer to it across the network
    pstate: physical state of the new Character
    equipment: list with structure [container_id, *database_ids, *instance_ids] for equipment
    inventory: list with structure [container_id, *database_ids, *instance_ids] for inventory
    skills: essentially a list containing all skill levels
    powers: list with structure [*database_ids, *instance_ids] for powers
    cbstate: combat state of the new Character
    """
    inv_id = inventory[0]
    inventory = inventory[1:]
    inv_l = len(inventory)
    inventory = [inv_id] + list(zip(inventory[:inv_l//2], inventory[inv_l//2:]))
    equip_id = equipment[0]
    equipment = equipment[1:]
    equip_l = len(equipment)
    equipment = [equip_id] + list(zip(equipment[:equip_l//2], equipment[equip_l//2:]))
    powers_l = len(powers)
    powers = list(zip(powers[:powers_l//2], powers[powers_l//2:]))
    world.make_pc(uuid, pstate=pstate, equipment=equipment, inventory=inventory,
                  skills=skills, powers=powers, cbstate=cbstate)
    world.make_pc_ctrl()
    network.server_connection = connection

    ui.make_all_ui()

@rpc(network.peer)
def spawn_npc(connection, time_received, uuid: int,
              pstate: PhysicalState, cbstate: NPCCombatState):
    """Remotely spawn a character that isn't the client's player character (could also be other players)"""
    if uuid not in world.uuid_to_char:
        world.make_npc(uuid, pstate, cbstate)
        world.make_npc_ctrl(uuid)

# Combat
@rpc(network.peer)
def toggle_combat(connection, time_received, uuid: int, toggle: bool):
    char = world.uuid_to_char[uuid]
    ctrl = world.uuid_to_ctrl[uuid]
    char.in_combat = toggle
    if toggle:
        ctrl.animator.enter_combat()
    else:
        ctrl.animator.exit_combat()
    if ui.gamewindow:
        msg = "Now entering combat" if toggle else "Now leaving combat"
        ui.gamewindow.add_message(msg)

@rpc(network.peer)
def remote_kill(connection, time_received, uuid: int):
    if uuid not in world.uuid_to_ctrl:
        return
    ctrl = world.uuid_to_ctrl[uuid]
    char = ctrl.character
    if ui.gamewindow:
        msg = f"{char.cname} perishes"
        ui.gamewindow.add_message(msg)
    ctrl.kill()

@rpc(network.peer)
def remote_set_target(connection, time_received, uuid: int):
    """Update player character's target"""
    tgt = world.uuid_to_char[uuid]
    world.pc.target = tgt
    if ui.gamewindow:
        msg = f"Now targeting: {tgt.cname}"
        ui.gamewindow.add_message(msg)

@rpc(network.peer)
def update_pc_cbstate(connection, time_received, uuid: int, cbstate: PlayerCombatState):
    if world.pc is None:
        return
    cbstate.apply(world.pc)
    if ui.bars:
        ui.bars.update_display()
    if ui.playerwindow:
        ui.playerwindow.stats.update_labels()

@rpc(network.peer)
def update_npc_cbstate(connection, time_received, uuid: int, cbstate: NPCCombatState):
    char = world.uuid_to_char.get(uuid)
    if char is None:
        return
    cbstate.apply(char)

# Skills
@rpc(network.peer)
def remote_update_skill(connection, time_received, skill: str, val: int):
    char = world.pc
    char.skills[skill] = val
    if ui.playerwindow:
        ui.playerwindow.skills.set_label_text(skill)

@rpc(network.peer)
def remote_update_skills(connection, time_received, skills: list[int]):
    char = world.pc
    for i, skill in enumerate(all_skills):
        char.skills[i] = skills[i]
        if ui.playerwindow:
            ui.playerwindow.skills.set_label_text(skill)

# Items
@rpc(network.peer)
def remote_update_container(connection, time_received, container_id: int, container: list[int]):
    """Update internal containers and visual containers

    Mimic most of the process in ItemIcon.swap_locs for hosts, but
    this will only be done by non-hosts"""
    new_container = world.ids_to_container(container)
    old_container = world.inst_id_to_container[container_id]
    old_container.overwrite_items(new_container)

    item_frame = ui.item_frames.get(container_id)
    if item_frame:
        item_frame.update_ui_icons()

# UI Updates
@rpc(network.peer)
def remote_print(connection, time_received, msg: str):
    """Remotely print a message for another player"""
    if ui.gamewindow:
        ui.gamewindow.add_message(msg)

# Physical
@rpc(network.peer)
def update_npc_lerp_attrs(connection, time_received, uuid: int, pos: Vec3, rot: float):
    """Called by server to update physical state for an NPC"""
    controller = world.uuid_to_ctrl.get(uuid)
    if controller is None:
        return
    controller.update_lerp_attrs(time_received, pos, rot)

@rpc(network.peer)
def update_pc_lerp_attrs(connection, time_received, sequence_number: int, pos: Vec3, rot: float):
    """Called by server to update physical state for a player character"""
    if world.pc is None:
        return
    # To check synchronization, uncomment these:
    # print(rot % 360)
    # print(world.pc.rotation_y)
    # print(pos)
    # print(world.pc.position)
    controller = world.pc_ctrl
    controller.update_lerp_attrs(sequence_number, pos, rot)

@rpc(network.peer)
def update_pos_rot(connection, time_received, uuid: int, pos: Vec3, rot: Vec3):
    char = world.uuid_to_char.get(uuid)
    if char is None:
        return
    char.position = pos
    char.rotation = rot
             
@rpc(network.peer)
def update_rotation(connection, time_received, uuid: int, rot: Vec3):
    char = world.uuid_to_char.get(uuid)
    if char is None:
        return
    char.rotation = rot

# Animation
@rpc(network.peer)
def remote_start_run_anim(connection, time_received, uuid: int):
    ctrl = world.uuid_to_ctrl.get(uuid)
    if ctrl is None:
        return
    ctrl.animator.start_run_cycle()

@rpc(network.peer)
def remote_end_run_anim(connection, time_received, uuid: int):
    ctrl = world.uuid_to_ctrl.get(uuid)
    if ctrl is None:
        return
    ctrl.animator.end_run_cycle()

@rpc(network.peer)
def remote_do_attack_anim(connection, time_received, uuid: int, slot: str):
    ctrl = world.uuid_to_ctrl.get(uuid)
    if ctrl is None:
        return
    ctrl.animator.do_attack(slot)
