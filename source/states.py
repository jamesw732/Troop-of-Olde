"""Contains API for States, including functions for building states."""
import os
import json
import types
import typing

from ursina import *
from ursina import Vec3, Vec4, color, load_model, Entity, destroy
from ursina.mesh_importer import imported_meshes

from .base import *
        

class State(list):
    """Base class for all State types. Never meant to be initialized directly,
    always inherited by other State types.

    In general, States are used to aggregate a large number of parameters meant to
    be sent over the network, or abstract frequently used parameters sent over the
    network. They can read either generic objects such as Characters (by pulling attrs)
    or dicts (by pulling keys). The latter is important for transferring login data
    from the client to the server before the client makes the player character, but
    the former is the more typical use case. States should not have any knowledge
    about the types they pull data from, any complexity should be delegated to
    a class's getter methods (@property methods). In other words, if you find yourself
    trying to redefine State._get_val_from_src, it's probably better to just invent
    a new property for the class you're working with.
    """
    statedef = {}
    defaults = {}
    type_to_default = {
        int: 0,
        float: 0.0,
        Vec3: Vec3(0, 0, 0),
        Vec4: Vec4(0, 0, 0, 0),
        str: ""
    }

    def __init__(self, src={}):
        """Populates self as a flat list, with defaults if missing.
        Will never have gaps.

        src: dict or Character object"""
        self.key_to_idx = {key: i for i, key in enumerate(self.statedef)}
        for attr in self.statedef:
            self.append(self._get_val_from_src(attr, src))

    def apply(self, dst):
        """Apply attrs to a destination object by overwriting the attrs
        
        dst: Character or container object, this may expand"""
        for k, v in zip(self.statedef, self):
            self._apply_attr(dst, k, v)
    
    def apply_diff(self, dst, remove=False):
        """Apply attrs to a destination object by adding/subtracting the attrs
        
        dst: Character"""
        for attr, val in zip(self.statedef, self):
            original_val = self._get_val_from_src(attr, dst)
            if remove:
                self._apply_attr(dst, attr, original_val - val)
            else:
                self._apply_attr(dst, attr, original_val + val)
        dst.update_max_ratings()

    def _get_val_from_src(self, attr, src):
        """General wrapper for getting attr from src. Since States are expected to have all fields
        in their state definition, this does its best to infer data if it's missing from src."""
        val = None
        # src is a keyed data structure like a dict and contains attr
        if isinstance(src, dict) and attr in src:
            val = src[attr]
        # src is a typical data structure and contains attr
        elif hasattr(src, attr):
            val = getattr(src, attr)
        # couldn't find attr in src, look in defaults
        if val is None:
            # If not in class's defaults, infer based on type of attr
            if attr not in self.defaults:
                return self.type_to_default[self.statedef[attr]]
            val = self.defaults[attr]
        elif type(val) != self.statedef[attr]:
            try:
                val = self.statedef[attr](val)
            except TypeError:
                try:
                    val = self.statedef[attr](*val)
                except TypeError:
                    if attr not in self.defaults:
                        return self.type_to_default[self.statedef[attr]]
                    val = self.defaults[attr]
        return val

    def _apply_attr(self, dst, attr, val):
        """Generic wrapper for setting attr of dst"""
        setattr(dst, attr, val)

    @classmethod
    def serialize(cls, writer, state):
        for i, k in enumerate(cls.statedef):
            v = state[i]
            writer.write(v)

    @classmethod
    def deserialize(cls, reader):
        state = cls()
        for i, (k, t) in enumerate(cls.statedef.items()):
            v = reader.read(t)
            state[i] = v
        return state

    def __getitem__(self, key):
        if isinstance(key, str):
            key = self.key_to_idx[key]
        val = super().__getitem__(key)
        return val

    def __setitem__(self, key, val):
        if isinstance(key, str):
            key = self.key_to_idx[key]
        super().__setitem__(key, val)


class LoginState(State):
    """State sent by client to request to enter the world.
    src should be a dict obtained from players.json"""
    custom_defaults = {
        "cname": "Demo Player",
        "equipment": [-1] * num_equipment_slots,
        "inventory": [-1] * num_inventory_slots,
        "powers": [-1] * default_num_powers,
    }
    defaults = default_char_attrs | custom_defaults
    statedef = {
        "cname": str,
        "model_name": str,
        "model_color": Vec4,
        "scale": Vec3,
        "position": Vec3,
        "rotation": Vec3,
        "health": int,
        "energy": int,
        "statichealth": int,
        "staticenergy": int,
        "armor": int,
        "str": int,
        "dex": int,
        "ref": int,
        "haste": int,
        "speed": int,
        "equipment": list[int],
        "inventory": list[int],
        "powers": list[int],
        "skills": list[int],
    }


class PCSpawnState(State):
    """State sent by server to confirm spawning into the world.
    src should be a ServerCharacter"""
    custom_defaults = {
        "cname": "Demo Player",
        "equipment_id": -1,
        "equipment_inst_ids": [-1] * num_equipment_slots,
        "inventory_id": -1,
        "inventory_inst_ids": [-1] * num_inventory_slots,
        "powers_inst_ids": [-1] * default_num_powers,
    }
    defaults = default_char_attrs | custom_defaults
    statedef = {
        "uuid": int,
        "cname": str,
        "model_name": str,
        "model_color": Vec4,
        "scale": Vec3,
        "position": Vec3,
        "rotation": Vec3,
        "health": int,
        "energy": int,
        "statichealth": int,
        "staticenergy": int,
        "maxhealth": int,
        "maxenergy": int,
        "armor": int,
        "str": int,
        "dex": int,
        "ref": int,
        "haste": int,
        "speed": int,
        "equipment_id": int,
        "equipment_inst_ids": list[int],
        "inventory_id": int,
        "inventory_inst_ids": list[int],
        "powers_inst_ids": list[int],
        "skills": list[int],
    }

class NPCSpawnState(State):
    """State sent by server to spawn an NPC into the world."""
    custom_defaults = {
        "cname": "NPC",
    }
    defaults = default_char_attrs | custom_defaults
    statedef = {
        "uuid": int,
        "cname": str,
        "model_name": str,
        "model_color": Vec4,
        "scale": Vec3,
        "position": Vec3,
        "rotation": Vec3,
        "health": int,
        "energy": int,
        "maxhealth": int,
        "maxenergy": int,
    }


class BaseCombatState(State):
    statedef = {
        "health": int,
        "energy": int,
        "statichealth": int,
        "staticenergy": int,
        "armor": int,
        "str": int,
        "dex": int,
        "ref": int,
        "haste": int,
        "speed": int,
    }
    defaults = default_char_attrs


class PlayerCombatState(State):
    statedef = {
        "health": int,
        "maxhealth": int,
        "statichealth": int,
        "energy": int,
        "maxenergy": int,
        "staticenergy": int,
        "armor": int,
        "str": int,
        "dex": int,
        "ref": int,
        "haste": int,
        "speed": int,
    }
    defaults = default_char_attrs


class NPCCombatState(State):
    statedef = {
        "health": int,
        "maxhealth": int,
    }
    defaults = default_char_attrs


class Stats(State):
    statedef = {
        "statichealth": int,
        "staticenergy": int,
        "armor": int,
        "str": int,
        "dex": int,
        "ref": int,
        "haste": int,
        "speed": int
    }
    defaults = {stat: 0 for stat in statedef}


class PhysicalState(State):
    """Encodes the physical, engine-based attributes used for Character creation.

    Not to be used for generic Character updates, only for creation."""
    statedef = {
        "model_name": str,
        "model_color": Vec4,
        "scale": Vec3,
        "position": Vec3,
        "rotation": Vec3,
        "cname": str
    }
    defaults = default_char_attrs


def get_player_states_from_data(pc_data, player_name):
    """Returns the states necessary to request a Player Character
    be loaded from server.
    pc_data: npc data loaded from json and keyed by name
    player_name: the name of the character
    returns a list of states to use as arguments to request_enter_world"""
    pstate_raw = pc_data.get("pstate", {})
    pstate_raw["cname"] = player_name
    basestate_raw = pc_data.get("basestate", {})
    skills_raw = pc_data.get("skills", [])
    equipment = pc_data.get("equipment", [])
    inventory = pc_data.get("inventory", [])
    powers = pc_data.get("powers", [])

    pstate = PhysicalState(pstate_raw)
    basestate = BaseCombatState(basestate_raw)
    skills = skills_raw + [1] * (len(all_skills) - len(skills_raw))

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


