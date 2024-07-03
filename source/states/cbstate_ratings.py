from ursina import *

attrs = {
    "health": int,
    "maxhealth": int,
    # "mana": int,
    # "maxmana": int,
    # "stamina": int,
    # "maxstamina": int,
    # "spellshield": int,
    # "maxspellshield": int,
    # "armor": int,
    # "maxarmor": int,
}

class RatingsState:
    def __init__(self, char=None, **kwargs):
        """This state is meant for host-authoritative overwrites of non-player-characters. Minimal possible information is sent."""
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


def serialize_ratings_state(writer, state):
    for attr in attrs:
        if hasattr(state, attr):
            val = getattr(state, attr)
            if val is not None:
                writer.write(attr)
                writer.write(val)
    writer.write("end")

def deserialize_ratings_state(reader):
    state = RatingsState()
    while reader.iter.getRemainingSize() > 0:
        attr = reader.read(str)
        if attr == "end":
            return state
        val = reader.read(attrs[attr])
        setattr(state, attr, val)