"""DO NOT import attrs"""

attrs = {
    "health": int,
    "mana": int,
    "stamina": int,
    "armor": int,
    "spellshield": int,
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

class StatChange(dict):
    def __init__(self, **kwargs):
        """This class represents the stats of an auxilliary object, whether it be an Item or a 
        persistent Effect. Meant to be applied to Characters additively. It's just a dict."""
        super().__init__(**kwargs)

    def __str__(self):
        return str({attr: getattr(self, attr)
                for attr in attrs if hasattr(self, attr)})

def serialize_stat_change(writer, state):
    for k, v in state.items():
        writer.write(k)
        writer.write(v)
    writer.write("end")

def deserialize_stat_change(reader):
    state = StatChange()
    while reader.iter.getRemainingSize() > 0:
        k = reader.read(str)
        if k == "end":
            return state
        v = reader.read(attrs[k])
        state[k] = v

def apply_stat_change(char, stats):
    for attr, val in stats.items():
        original_val = getattr(char, attr)
        setattr(char, attr, original_val + val)

def remove_stat_change(char, stats):
    for attr, val in stats.items():
        original_val = getattr(char, attr)
        setattr(char, attr, original_val - val)