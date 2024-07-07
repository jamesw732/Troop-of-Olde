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

class BaseCombatState:
    """This state is meant to represent the fundamental stats of a character, as if nothing else was affecting them. Meant to be assigned to a character once and only once - when it's created."""
    def __init__(self, char=None, **kwargs):
        """Possible kwargs given by combat_state_attrs."""
        # If a character was passed, take its attributes
        if char is not None:
            for attr in attrs:
                if hasattr(char, attr):
                    val = getattr(char, attr)
                    # Only include attrs intentionally set
                    if val is not None:
                        setattr(self, attr, val)
        # Otherwise, read the attributes straight off
        else:
            for attr in kwargs:
                if attr in attrs:
                    setattr(self, attr, kwargs[attr])

    def __str__(self):
        return str({attr: getattr(self, attr)
                for attr in attrs if hasattr(self, attr)})

def serialize_base_cb_state(writer, state):
    for attr in attrs:
        if hasattr(state, attr):
            val = getattr(state, attr)
            if val is not None:
                writer.write(attr)
                writer.write(val)
    writer.write("end")

def deserialize_base_cb_state(reader):
    state = BaseCombatState()
    while reader.iter.getRemainingSize() > 0:
        attr = reader.read(str)
        if attr == "end":
            return state
        val = reader.read(attrs[attr])
        setattr(state, attr, val)

def apply_base_state(char, state):
    for attr in attrs:
        if hasattr(state, attr):
            val = getattr(state, attr)
            setattr(char, attr, val)