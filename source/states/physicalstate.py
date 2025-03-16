"""DO NOT import attrs"""

from ursina import *

from ..networking import network

attrs = {
    "model": str,
    "scale": Vec3,
    "position": Vec3,
    "rotation": Vec3,
    "color": str,

    "cname": str,
}

class PhysicalState(dict):
    """Physical character attributes. Client-authoritative."""
    def __init__(self, char=None, **kwargs):
        """Possible kwargs given by phys_state_attrs.

        Explanations of nontrivial kwargs:
        color: string representing the color, ie "red" or "orange". See ursina.color.colors for possible keys
        """
        # If a character was passed, take its attributes
        if char is not None:
            for attr in attrs:
                if hasattr(char, attr):
                    val = getattr(char, attr)
                    # Only include attrs intentionally set
                    if val is not None:
                        # Why do I check for collider if not in attrs?
                        if attr in ["collider", "color", "model"]:
                            # Ursina objects exist in PhysicalState as string names
                            val = val.name
                        self[attr] = val
        # Otherwise, read the attributes straight off
        else:
            super().__init__(**kwargs)

    def __str__(self):
        return super().__str__()
        # return str({key: val for key, val in self.items()})


def serialize_physical_state(writer, state):
    for k, v in state.items():
        if k == "target" and not isinstance(v, int):
            # it's a character; write its uuid
            v = v.uuid
        writer.write(k)
        writer.write(v)
    writer.write("end")

def deserialize_physical_state(reader):
    state = PhysicalState()
    while reader.iter.getRemainingSize() > 0:
        k = reader.read(str)
        if k == "end":
            return state
        v = reader.read(attrs[k])
        if k == "target":
            v = network.uuid_to_char.get(v, None)
        state[k] = v
    return state

def apply_physical_state(char, state):
    for k, v in state.items():
        if k == "color" and isinstance(v, str):
            # color is supposed to be a string, so grab the color.color
            v = color.colors[v]
        elif k == "target":
            # target is supposed to be a uuid, so grab the character
            if v in network.uuid_to_char:
                v = network.uuid_to_char[v]
        setattr(char, k, v)
        # Overwriting model causes origin to break, fix it
        if "model" in state:
            char.origin = Vec3(0, -0.5, 0)