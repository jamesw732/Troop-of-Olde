"""DO NOT import attrs"""

attrs = {
    "health": int,
    "mana": int,
    "stamina": int,
    "armor": int,
    "spellshield": int
}

class RatingsState(dict):
    """This state is currently unused, but will eventually be used to overwrite
    ratings upon login"""
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
    """Apply base state to Character. Assume it's the first
    thing to affect its combat state."""
    for k, v in state.items():
        setattr(char, k, v)
