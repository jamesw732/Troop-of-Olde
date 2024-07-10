"""DO NOT import attrs"""


attrs = {
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

class CompleteCombatState(dict):
    """This state is meant for host-authoritative overwrites of a player's own state.
    Only use is to get complete state of character A, and send to client whose player
    character is character A. Rather than backend client-side updates, the player
    character's state will just be overwritten by this."""
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


def serialize_complete_cb_state(writer, state):
    for k, v in state.items():
        writer.write(k)
        writer.write(v)
    writer.write("end")

def deserialize_complete_cb_state(reader):
    state = CompleteCombatState()
    while reader.iter.getRemainingSize() > 0:
        k = reader.read(str)
        if k == "end":
            return state
        v = reader.read(attrs[k])
        state[k] = v


def apply_complete_cb_state(char, state):
    for k, v in state.items():
        setattr(char, k, v)
