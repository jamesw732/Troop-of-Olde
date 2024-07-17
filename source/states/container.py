from ..networking.base import network
from ..base import default_equipment

class InitContainer(dict):
    """Use this class to initialize containers upon login

    Structure may be misleading, use the JSON for types - keys are always
    strings and values are always ints."""
    def __init__(self, container={}):
        """Initialize InitContainer.

        container: dict, map STR keys to INT itemids, even if container is a list"""
        super().__init__(container)

    def __str__(self):
        return super().__str__()

def serialize_init_container(writer, state):
    for k, v in state.items():
        writer.write(k)
        writer.write(v)
    writer.write("end")

def deserialize_init_container(reader):
    state = InitContainer()
    while reader.iter.getRemainingSize() > 0:
        k = reader.read(str)
        if k == "end":
            return state
        v = reader.read(int)
        state[k] = v
    return state

def container_to_init(container):
    """Convert a container (Character attribute) to one sendable over the network"""
    return InitContainer({slot: item.uiid for slot, item in container.items()
                          if item is not None})

def init_to_container(init_container):
    """Convert an InitContainer (dict mapping slots to uiids) to a dict of Items"""
    return {slot: network.uiid_to_item[itemid] for slot, itemid in init_container.items()}
