"""A State is just a container used to represent a portion of a character. States may not
be complete, in which case the undefined portion is ignored."""
from ursina import Vec3, color
from ..base import all_skills

labl_to_attrs = {
    # Used for ground-up Character creation, stored by client and sent to server
    "base_combat": { 
        "statichealth": int,
        "staticenergy": int,
        "staticarmor": int,

        "str": int,
        "dex": int,
        "ref": int,
        "hardy": int,

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
        "energy": int,
        "maxenergy": int,
        "staticenergy": int,
        "armor": int,
        "maxarmor": int,
        "staticarmor": int,

        "str": int,
        "dex": int,
        "ref": int,
        "hardy": int,

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
    def __init__(self, state_type, src=None, **kwargs):
        """States are temporary containers that can be sent over the network.

        They are essentially dicts with the power to extract data from/apply data to
        objects such as Characters. Developer is held responsible for knowing what type
        of state to create, the rest is handled automatically.
        If neither src nor kwargs is specified, will essentially create a blank dict.
        state_type: one of the keys to labl_to_attrs
        src: object to grab data from, optional
        **kwargs: alternative to grabbing attrs from character, optional
        """
        self.state_type = state_type
        self.attrs = labl_to_attrs[self.state_type]
        # If a character was passed, take its attributes
        if src is not None:
            for attr in self.attrs:
                val = self._get_val_from_src(attr, src)
                # Only include attrs intentionally set
                if val is None:
                    continue
                self[attr] = val
        # Otherwise, read the attributes straight off
        else:
            valid_kwargs = {k: v for k, v in kwargs.items() if k in self.attrs}
            super().__init__(**valid_kwargs)

    def apply(self, dst):
        """Apply attrs to a destination object by overwriting the attrs
        
        dst: Character or container object, this may expand"""
        for k, v in self.items():
            self._apply_attr(dst, k, v)
    
    def apply_diff(self, dst, remove=False):
        """Apply attrs to a destination object by adding/subtracting the attrs
        
        dst: Character or container object, this may expand"""
        for attr, val in self.items():
            original_val = self._get_val_from_src(attr, dst)
            if remove:
                self._apply_attr(dst, attr, original_val - val)
            else:
                self._apply_attr(dst, attr, original_val + val)

    def _get_val_from_src(self, attr, src):
        """Generic wrapper for getting attr from src
        
        Only nontrivial handling we need to do is for Dict objects, and also
        some state attrs we need to assign names rather than objects
        (because that's how Ursina works), rather than Entity/Mesh objects.
        Depends on self.state_type to infer what kind of thing src is."""
        if self.state_type == "skills":
            val = src.get(attr, 1)
        else:
            if not hasattr(src, attr):
                return None
            val = getattr(src, attr)
        if val is None:
            return val
        if self.state_type == "physical" and attr in ["collider", "color", "model"]:
            val = val.name
        return val

    def _apply_attr(self, dst, attr, val):
        """Generic wrapper for setting attr of dst"""
        if self.state_type == "skills":
            dst[attr] = val
            return
        elif self.state_type == "physical":
            # Colors can't be strings, need to be color objects
            if attr == "color" and isinstance(val, str):
                val = color.colors[val]
        setattr(dst, attr, val)
        if attr == "model":
            # When updating a model, origin gets reset, so we fix
            # This should probably be intrinsic to the Character, not done here
            dst.origin = Vec3(0, -0.5, 0)


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