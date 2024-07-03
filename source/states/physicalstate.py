"""DO NOT import attrs"""

from ursina import *

attrs = {
    "model": str,
    "scale": Vec3,
    "position": Vec3,
    "rotation": Vec3,
    "color": str,

    "cname": str,
    "type": str,
    "target": int,
    "in_combat": bool,
}

class PhysicalState:
    """Physical character attributes. Client-authoritative."""
    def __init__(self, char=None, **kwargs):
        """Possible kwargs given by phys_state_attrs.

        Explanations of nontrivial kwargs:
        color: string representing the color, ie "red" or "orange". See ursina.color.colors for possible keys
        target: uuid of character's target"""
        # If a character was passed, take its attributes
        if char is not None:
            for attr in attrs:
                if hasattr(char, attr):
                    val = getattr(char, attr)
                    # Only include attrs intentionally set
                    if val is not None:
                        if attr in ["collider", "color", "model"]:
                            # Ursina objects exist in PhysicalState as string names
                            val = val.name
                        setattr(self, attr, val)
        # Otherwise, read the attributes straight off
        else:
            for attr in kwargs:
                if attr in attrs:
                    setattr(self, attr, kwargs[attr])

    def __str__(self):
        return str({attr: getattr(self, attr)
                for attr in attrs if hasattr(self, attr)})


def serialize_physical_state(writer, state):
    for attr in attrs:
        if hasattr(state, attr):
            val = getattr(state, attr)
            if val is not None:
                if attr == "target":
                    # Don't write the character, write its uuid
                    val = val.uuid
                writer.write(attr)
                writer.write(val)
    writer.write("end")

def deserialize_physical_state(reader):
    state = PhysicalState()
    while reader.iter.getRemainingSize() > 0:
        attr = reader.read(str)
        if attr == "end":
            return state
        val = reader.read(attrs[attr])
        setattr(state, attr, val)