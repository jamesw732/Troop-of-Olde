import os
import json

from ursina import *

from ..base import data_path
from ..gamestate import gs
from .state import *

def get_character_states_from_json(pname):
    """Does all the work needed to get inputs to Character from a player name in players.json.  """
    players_path = os.path.join(data_path, "players.json")
    with open(players_path) as players:
        d = json.load(players)[pname]
    pstate_raw = d.get("pstate", {})
    pstate_raw["cname"] = pname
    basestate_raw = d.get("basestate", {})
    skills_raw = d.get("skills", {})
    equipment = d.get("equipment", [])
    inventory = d.get("inventory", [])
    powers = d.get("powers", [])

    pstate = PhysicalState(pstate_raw)
    basestate = BaseCombatState(basestate_raw)
    skills = SkillsState(skills_raw)

    return pstate, basestate, equipment, inventory, skills, powers

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
