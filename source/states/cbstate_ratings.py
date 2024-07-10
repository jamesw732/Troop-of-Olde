"""DO NOT import attrs"""


# These are very low priority, at least for now. They will probably be added eventually, though.
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

class RatingsState(dict):
    def __init__(self, char=None, **kwargs):
        """This state is meant for host-authoritative overwrites of non-player-characters. Minimal possible information is sent."""
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


def serialize_ratings_state(writer, state):
    for k, v in state.items():
        writer.write(k)
        writer.write(v)
    writer.write("end")

def deserialize_ratings_state(reader):
    state = RatingsState()
    while reader.iter.getRemainingSize() > 0:
        k = reader.read(str)
        if k == "end":
            return state
        v = reader.read(attrs[k])
        state[k] = v

def apply_ratings_state(char, state):
    for k, v in state.items():
        setattr(char, k, v)