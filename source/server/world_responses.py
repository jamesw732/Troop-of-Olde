"""These are generic RPC functions that are only called by the host.

These will typically only be called by functions in world_requests as part
of a response to a request. Otherwise, they may be called by host_continuous."""
from ursina.networking import rpc

from .. import *

# LOGIN
@rpc(network.peer)
def remote_generate_world(connection, time_received, zone:str):
    """Remotely generate the world"""
    pass

def spawn_pc(connection, time_received, uuid: int, pstate: PhysicalState, equipment: list[int],
             inventory: list[int], skills: SkillsState, powers: list[int], cbstate: PlayerCombatState):
    """Does all the necessary steps to put the player character in the world, and makes the UI
    
    uuid: unique id of new Character, used to refer to it across the network
    pstate: physical state of the new Character
    equipment: list with structure [container_id, *database_ids, *instance_ids] for equipment
    inventory: list with structure [container_id, *database_ids, *instance_ids] for inventory
    skills: essentially a list containing all skill levels
    powers: list with structure [*database_ids, *instance_ids] for powers
    cbstate: combat state of the new Character
    """
    pass

def spawn_npc(connection, time_received, uuid: int,
              phys_state: PhysicalState, cbstate: NPCCombatState):
    """Remotely spawn a character that isn't the client's player character (could also be other players)"""
    pass

def toggle_combat(connection, time_received, toggle: bool):
    pass

def remote_death(connection, time_received, char_uuid: int):
    """Tell clients that a character died. Only to be called by host."""
    pass

def remote_set_target(connection, time_received, uuid: int):
    """Update player character's target"""
    pass

def update_pc_cbstate(connection, time_received, uuid: int, cbstate: PlayerCombatState):
    pass

def update_npc_cbstate(connection, time_received, uuid: int, cbstate: NPCCombatState):
    pass

def remote_update_skill(connection, time_received, skill: str, val: int):
    pass

def remote_update_container(connection, time_received, container_id: int, container: list[int]):
    """Update internal containers and visual containers

    Mimic most of the process in ItemIcon.swap_locs for hosts, but
    this will only be done by non-hosts"""
    pass

def update_npc_lerp_attrs(connection, time_received, uuid: int, pos: Vec3, rot: float):
    """Called by server to update physical state for an NPC"""
    pass

def update_pc_lerp_attrs(connection, time_received, sequence_number: int, pos: Vec3, rot: float):
    """Called by server to update physical state for a player character"""
    pass

def update_pos_rot(connection, time_received, uuid: int, pos: Vec3, rot: Vec3):
    pass

def update_rotation(connection, time_received, uuid: int, rot: Vec3):
    pass

def remote_print(connection, time_received, msg: str):
    """Remotely print a message for another player"""
    pass
