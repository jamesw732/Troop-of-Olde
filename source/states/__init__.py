import os
import json

from ursina import *

from .container import IdContainer
from .cbstate_base import BaseCombatState
from .cbstate_complete import CompleteCombatState
from .cbstate_mini import MiniCombatState
from .skills import SkillState
from .physicalstate import PhysicalState

def get_character_states_from_json(pname):
    """Does all the work needed to get inputs to Character from a player name in players.json
    Should this be in the states directory?"""
    players_path = os.path.join(os.path.dirname(__file__), "..", "..", "data", "players.json")
    with open(players_path) as players:
        d = json.load(players)[pname]
    pstate_raw = d.get("pstate", {})
    for k, v in pstate_raw.items():
        if hasattr(v, "__iter__"):
            pstate_raw[k] = Vec3(*v)
    basestate_raw = d.get("basestate", {})
    equipment_raw = d.get("equipment", {})
    inventory_raw = d.get("inventory", {})
    skills_raw = d.get("skills", {})
    page1_raw = d.get("page1", [])
    page2_raw = d.get("page2", [])

    pstate = PhysicalState(**pstate_raw)
    pstate["cname"] = pname
    basestate = BaseCombatState(**basestate_raw)
    equipment = IdContainer(equipment_raw)
    inventory = IdContainer(inventory_raw)
    skills = SkillState(skills_raw)
    page1 = IdContainer({str(i): power_id for i, power_id in enumerate(page1_raw)})
    page2 = IdContainer({str(i): power_id for i, power_id in enumerate(page2_raw)})

    lexicon = {"page1": page1, "page2": page2}
    return pstate, basestate, equipment, inventory, skills, lexicon
