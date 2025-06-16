"""A State is just a container used to represent a portion of a character. States may not
be complete, in which case the undefined portion is ignored."""
from ursina import Vec3, color, Entity

from .state_defs import state_defs, statetype_to_defaults, type_to_default
from ..gamestate import gs


class State(dict):
    def __init__(self, state_type, src=None):
        """States are containers that store Character attrs.

        They are essentially dicts with the power to extract data from/apply data to
        Characters. Possible states are defined in state_defs.
        src is prioritized over kwargs, all kwargs are ignored if src is specified.
        state_type: one of the keys to state_defs
        src: object to grab data from, usually a Character or dict. State not tied to src.
        """
        self.state_type = state_type
        self.attrs = state_defs[self.state_type]
        # If a character was passed, take its attributes
        if src is not None:
            for attr in self.attrs:
                val = self._get_val_from_src(attr, src)
                self[attr] = val

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
        defaults = statetype_to_defaults.get(self.state_type, {})
        val = None
        # src is a keyed data structure like a dict and contains attr
        if isinstance(src, dict) and attr in src:
            val = src[attr]
        # src is a typical data structure and contains attr
        elif hasattr(src, attr):
            val = getattr(src, attr)
        # couldn't find attr in src, look in defaults
        if val is None:
            # If not in state_type's defaults, just take the default based on the type of the variable
            if attr not in defaults:
                statedef = state_defs[self.state_type]
                t = statedef[attr]
                return type_to_default[t]
            val = defaults[attr]
        # these need to be strings, not the respective Ursina objects
        if attr in ["collider", "color", "model"] and not isinstance(val, str):
            val = val.name
        return val

    def _apply_attr(self, dst, attr, val):
        """Generic wrapper for setting attr of dst"""
        if self.state_type == "skills":
            dst[attr] = val
            return
        elif self.state_type == "physical":
            # Colors can't be strings, need to be color objects
            if attr == "color" and isinstance(val, str):
                val = color.colors[val]
        setattr(dst, attr, val)
        if attr == "model":
            # When updating a model, origin gets reset, so we fix
            # This should probably be intrinsic to the Character, not done here
            dst.origin = Vec3(0, -0.5, 0)


def serialize_state(writer, state):
    writer.write(state.state_type)
    state_def = state_defs[state.state_type]
    for k in state_def:
        v = state[k]
        writer.write(v)

def deserialize_state(reader):
    state_type = reader.read(str)
    state_def = state_defs[state_type]
    state = State(state_type=state_type)
    for k, t in state_def.items():
        v = reader.read(t)
        state[k] = v
    return state