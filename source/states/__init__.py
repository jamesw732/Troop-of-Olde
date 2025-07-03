import os
import json

from ursina import *

from ..base import data_path
from ..gamestate import gs
from .state import *

def get_player_states_from_data(pc_data, player_name):
    """Returns the states necessary to request a Player Character
    be loaded from server.
    pc_data: npc data loaded from json and keyed by name
    player_name: the name of the character
    returns a list of states to use as arguments to request_enter_world"""
    pstate_raw = pc_data.get("pstate", {})
    pstate_raw["cname"] = player_name
    basestate_raw = pc_data.get("basestate", {})
    skills_raw = pc_data.get("skills", {})
    equipment = pc_data.get("equipment", [])
    inventory = pc_data.get("inventory", [])
    powers = pc_data.get("powers", [])

    pstate = PhysicalState(pstate_raw)
    basestate = BaseCombatState(basestate_raw)
    skills = SkillsState(skills_raw)

    return pstate, basestate, equipment, inventory, skills, powers

def get_npc_states_from_data(npc_data, npc_name):
    """Return the states necessary to load an NPC from JSON data.
    npc_data: npc data loaded from json and keyed by name
    npc_name: the name of the character
    returns a dict mapping ServerCharacter argument name to state"""
    pstate_raw = npc_data.get("physical", {})
    pstate_raw["cname"] = npc_name
    basestate_raw = npc_data.get("basestate", {})

    pstate = PhysicalState(pstate_raw)
    basestate = BaseCombatState(basestate_raw)

    return {"pstate": pstate, "cbstate": basestate}

# These should eventually be expanded to take more than just items, should be pretty easy
def container_to_ids(container, id_type="inst_id"):
    """Convert a container (Character attribute) to one sendable over the network

    container: list containing Items
    id_type: the literal id attribute of the item, or tuple of id attributes
    In the latter case, returns a 1d list stacked in order of the id attributes"""
    if isinstance(id_type, tuple):
        return [getattr(item, id_subtype) if hasattr(item, id_subtype) else -1 for id_subtype in id_type
                for item in container]
    return [getattr(item, id_type) if hasattr(item, id_type) else -1 for item in container]

def ids_to_container(id_container):
    """Convert container of inst ids to a list of objects"""
    return [gs.network.inst_id_to_item.get(itemid, None) for itemid in id_container]
