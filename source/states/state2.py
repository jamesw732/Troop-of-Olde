from ursina import Vec3
from ..base import all_skills, default_equipment, default_phys_attrs, default_cb_attrs

class State2(dict):
    statedef = {}
    defaults = {}
    type_to_default = {
        int: 0,
        float: 0.0,
        Vec3: Vec3(0, 0, 0),
        str: ""
    }

    def __init__(self, src={}):
        """Generic parent class for State types"""
        for attr in self.statedef:
            self[attr] = self._get_val_from_src(attr, src)

    def apply(self, dst):
        """Apply attrs to a destination object by overwriting the attrs
        
        dst: Character or container object, this may expand"""
        for k, v in self.items():
            self._apply_attr(dst, k, v)
    
    def apply_diff(self, dst, remove=False):
        """Apply attrs to a destination object by adding/subtracting the attrs
        
        dst: Character or container object, this may expand"""
        for attr, val in self.items():
            original_val = self._get_val_from_src(attr, dst)
            if remove:
                self._apply_attr(dst, attr, original_val - val)
            else:
                self._apply_attr(dst, attr, original_val + val)

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
        return val

    def _apply_attr(self, dst, attr, val):
        """Generic wrapper for setting attr of dst"""
        setattr(dst, attr, val)

    def serialize(writer, state):
        statedef = State.state_def
        for k in statedef:
            v = state[k]
            writer.write(v)

    def deserialize(reader):
        statedef = State.statedef
        state = State()
        for k, t in statedef.items():
            v = reader.read(t)
            state[k] = v
        return state

class BaseCombatState(State2):
    statedef = { 
        "statichealth": int,
        "staticenergy": int,
        "staticarmor": int,

        "str": int,
        "dex": int,
        "ref": int,

        "haste": int,
        "speed": int,
    }
    defaults = default_cb_attrs

    def serialize(writer, state):
        statedef = BaseCombatState.statedef
        for k in statedef:
            v = state[k]
            writer.write(v)

    def deserialize(reader):
        statedef = BaseCombatState.statedef
        state = BaseCombatState()
        for k, t in statedef.items():
            v = reader.read(t)
            state[k] = v
        return state

class PlayerCombatState(State2):
    statedef = {
        "health": int,
        "maxhealth": int,
        "statichealth": int,
        "energy": int,
        "maxenergy": int,
        "staticenergy": int,
        "armor": int,
        "maxarmor": int,
        "staticarmor": int,

        "str": int,
        "dex": int,
        "ref": int,

        "haste": int,
        "speed": int,
    }
    defaults = default_cb_attrs

    def serialize(writer, state):
        statedef = PlayerCombatState.statedef
        for k in statedef:
            v = state[k]
            writer.write(v)

    def deserialize(reader):
        statedef = PlayerCombatState.statedef
        state = PlayerCombatState()
        for k, t in statedef.items():
            v = reader.read(t)
            state[k] = v
        return state

class NPCCombatState(State2):
    statedef = {
        "health": int,
        "maxhealth": int,
    }
    defaults = default_cb_attrs

    def serialize(writer, state):
        statedef = NPCCombatState.statedef
        for k in statedef:
            v = state[k]
            writer.write(v)

    def deserialize(reader):
        statedef = NPCCombatState.statedef
        state = NPCCombatState()
        for k, t in statedef.items():
            v = reader.read(t)
            state[k] = v
        return state

class ItemStats(State2):
    statedef = {
        "statichealth": int,
        "staticenergy": int,
        "staticarmor": int,
        "str": int,
        "dex": int,
        "ref": int,
        "haste": int,
        "speed": int
    }
    defaults = {stat: 0 for stat in statedef}

    def serialize(writer, state):
        statedef = ItemStats.statedef
        for k in statedef:
            v = state[k]
            writer.write(v)

    def deserialize(reader):
        statedef = ItemStats.statedef
        state = ItemStats()
        for k, t in statedef.items():
            v = reader.read(t)
            state[k] = v
        return state

class PhysicalState(State2):
    statedef = {
        "model": str,
        "scale": Vec3,
        "position": Vec3,
        "rotation": Vec3,
        "color": str,
        "cname": str
    }
    defaults = default_phys_attrs
    # Need to overwrite some things here

    def _apply_attr(self, dst, attr, val):
        """Essentially just setattr but with handling for color/model"""
        # Colors can't be strings, need to be color objects
        if attr == "color" and isinstance(val, str):
            val = color.colors[val]
        setattr(dst, attr, val)
        if attr == "model":
            # When updating a model, origin gets reset, so we fix
            dst.origin = Vec3(0, -0.5, 0)

    def serialize(writer, state):
        statedef = PhysicalState.statedef
        for k in statedef:
            v = state[k]
            writer.write(v)

    def deserialize(reader):
        statedef = PhysicalState.statedef
        state = PhysicalState()
        for k, t in statedef.items():
            v = reader.read(t)
            state[k] = v
        return state

class SkillsState(State2):
    statedef = {
        skill: int for skill in all_skills
    }
    defaults = {skill: 1 for skill in all_skills}

    def serialize(writer, state):
        statedef = SkillsState.statedef
        for k in statedef:
            v = state[k]
            writer.write(v)

    def deserialize(reader):
        statedef = SkillsState.statedef
        state = SkillsState()
        for k, t in statedef.items():
            v = reader.read(t)
            state[k] = v
        return state
