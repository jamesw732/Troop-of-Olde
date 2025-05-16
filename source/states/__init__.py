import os
import json

from ursina import *

from ..gamestate import gs
from .state import State

def get_character_states_from_json(pname):
    """Does all the work needed to get inputs to Character from a player name in players.json.  """
    players_path = os.path.join(os.path.dirname(__file__), "..", "..", "data", "players.json")
    with open(players_path) as players:
        d = json.load(players)[pname]
    pstate_raw = d.get("pstate", {})
    for k, v in pstate_raw.items():
        if hasattr(v, "__iter__"):
            pstate_raw[k] = Vec3(*v)
    basestate_raw = d.get("basestate", {})
    skills_raw = d.get("skills", {})
    equipment = d.get("equipment", [])
    inventory = d.get("inventory", [])
    lexicon = d.get("lexicon", [])

    pstate = State("physical", **pstate_raw)
    pstate["cname"] = pname
    basestate = State("base_combat", **basestate_raw)
    skills = State("skills", **skills_raw)

    return pstate, basestate, equipment, inventory, skills, lexicon

# These should eventually be expanded to take more than just items, should be pretty easy
def container_to_ids(container):
    """Convert a container (Character attribute) to one sendable over the network"""
    return [item.iiid if item else -1 for item in container]

def ids_to_container(id_container):
    """Convert container of ids to a list of objects"""
    return [gs.network.iiid_to_item.get(itemid, None) for itemid in id_container]
