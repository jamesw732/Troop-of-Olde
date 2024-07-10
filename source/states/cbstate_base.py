"""DO NOT import attrs"""

from ursina import *

attrs = {
    "statichealth": int,
    "staticmana": int,
    "staticstamina": int,
    "maxarmor": int,
    "maxspellshield": int,

    "bdy": int,
    "str": int,
    "dex": int,
    "ref": int,
    "int": int,

    "afire": int,
    "acold": int,
    "aelec": int,
    "apois": int,
    "adis": int,

    "haste": int,
    "speed": int,
    "casthaste": int,
    "healmod": int
}

class BaseCombatState(dict):
    """This state is meant to represent the fundamental stats of a character, as if nothing else was affecting them. Meant to be assigned to a character once and only once - when it's created."""
    def __init__(self, char=None, **kwargs):
        # If a character was passed, take its attributes
        if char is not None:
            for attr in attrs:
                if hasattr(char, attr):
                    val = getattr(char, attr)
                    # Only include attrs intentionally set
                    if val is not None:
                        self[attr] = val
        # Otherwise, read the attributes straight off
        else:
            super().__init__(**kwargs)

    def __str__(self):
        super().__str__()
        # return str({key: val for key, val in self.items()})

def serialize_base_cb_state(writer, state):
    for k, v in state.items():
        writer.write(k)
        writer.write(v)
    writer.write("end")

def deserialize_base_cb_state(reader):
    state = BaseCombatState()
    while reader.iter.getRemainingSize() > 0:
        k = reader.read(str)
        if k == "end":
            return state
        v = reader.read(attrs[k])
        state[k] = v

def apply_base_state(char, state):
    """Apply base state to Character. Assume it's the first
    thing to affect its combat state."""
    for k, v in state.items():
        setattr(char, k, v)