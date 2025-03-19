"""A State is just a container used to represent a portion of a character. States may not
be complete, in which case the undefined portion is ignored."""
from ursina import Vec3, color
from .. import all_skills

labl_to_attrs = {
    # Used for ground-up Character creation, stored by client and sent to server
    "base_combat": { 
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
    },
    # Used to update Player Character's stats, sent by server
    "pc_combat": {
        "health": int,
        "maxhealth": int,
        "statichealth": int,
        "mana": int,
        "maxmana": int,
        "staticmana": int,
        "stamina": int,
        "maxstamina": int,
        "staticstamina": int,
        "spellshield": int,
        "maxspellshield": int,
        "armor": int,
        "maxarmor": int,

        "bdy": int,
        "str": int,
        "dex": int,
        "ref": int,
        "int": int,

        "amagic": int,
        "aphys": int,
        "afire": int,
        "acold": int,
        "aelec": int,
        "apois": int,
        "adis": int,

        "haste": int,
        "speed": int,
        "casthaste": int,
        "healmod": int
    },
    # Used to update NPC's stats, sent by server
    "npc_combat": {
        "health": int,
        "maxhealth": int,
    },
    # Used to update character's physical state, sent to/by server
    "physical": {
        "model": str,
        "scale": Vec3,
        "position": Vec3,
        "rotation": Vec3,
        "color": str,
        "cname": str,
    },
    "skills": {skill: int for skill in all_skills}
}

class State(dict):
    def __init__(self, state_type, char=None, **kwargs):
        """Constructs a State object which can be sent over a network.

        If neither char nor kwargs is specified, will essentially create a blank dict.
        state_type: one of the keys to labl_to_attrs
        char: Character to grab all attrs from, optional
        **kwargs: alternative to grabbing attrs from character, optional
        """
        self.state_type = state_type
        self.attrs = labl_to_attrs[self.state_type]
        # If a character was passed, take its attributes
        self.src = self.get_src(char)
        if self.src is not None:
            for attr in self.attrs:
                val = self.get_val_from_src(attr)
                # Only include attrs intentionally set
                if val is None:
                    continue
                self[attr] = val
        # Otherwise, read the attributes straight off
        else:
            valid_kwargs = {k: v for k, v in kwargs.items() if k in self.attrs}
            super().__init__(**valid_kwargs)

    def get_src(self, char):
        """Derive the object containing the state information for the given character."""
        if char is None:
            return None
        if self.state_type == "skills":
            return char.skills
        return char

    def get_val_from_src(self, attr):
        """Derive the value a given attr for our source"""
        if self.state_type == "skills":
            val = self.src.get(attr, 1)
        else:
            if not hasattr(self.src, attr):
                return None
            val = getattr(self.src, attr)
        if self.state_type == "physical" and attr in ["collider", "color", "model"]:
            val = val.name
        return val

    # def get_valid_kwargs(self, kwargs):
    #     if self.state_type == "skills":
    #         return {skill: kwargs.get(skill, 1) for skill in all_skills}
    #     return {k: v for k, v in kwargs.items() if k in self.attrs}


def serialize_state(writer, state):
    writer.write(state.state_type)
    for k, v in state.items():
        writer.write(k)
        writer.write(v)
    writer.write("end")

def deserialize_state(reader):
    state_type = reader.read(str)
    attrs = labl_to_attrs[state_type]
    state = State(state_type=state_type)
    while reader.iter.getRemainingSize() > 0:
        k = reader.read(str)
        if k == "end":
            return state
        v = reader.read(attrs[k])
        state[k] = v
    return state

def apply_state(char, state):
    """Apply attrs to char by overwriting the attrs"""
    state_src = state.get_src(char)
    for k, v in state.items():
        setattr(state_src, k, v)

def apply_state_diff(char, state):
    """Apply attrs to a character by adding all keys of stats to attributes of char
    char: Character
    stats: State"""
    state_src = state.get_src(char)
    for attr, val in state.items():
        original_val = getattr(state_src, attr)
        setattr(state_src, attr, original_val + val)

def remove_state_diff(char, state):
    """Apply attrs to a character by subtracting all keys of stats from attributes of char
    char: Character
    stats: State"""
    state_src = state.get_src(char)
    for attr, val in state.items():
        original_val = getattr(state_src, attr)
        setattr(state_src, attr, original_val - val)

def apply_physical_state(char, state):
    """Apply physical state by overwriting. Usage is the same as apply_state,
    but handles some special casing. Could this just be part of apply_state?"""
    for k, v in state.items():
        if k == "color" and isinstance(v, str):
            # color is supposed to be a string, so grab the color.color
            v = color.colors[v]
        setattr(char, k, v)
        # Overwriting model causes origin to break, fix it
        if "model" in state:
            char.origin = Vec3(0, -0.5, 0)

