from ..networking.base import network
from ..base import default_equipment

class IdContainer(dict):
    """This class represents any container whose positions/slots are encoded by strings,
    and whose values are encoded by integers.

    The meaning of the values is ambiguous - they are always ints, but can reference
    stored item ids (from items.json) or instantiated item ids (Item.uiid). Conversion
    of global ids to Items is left up to the programmer, but ids_to_container and
    container_to_ids are intended for use with uiid's (renaming might be appropriate)
    Every container is assumed to be a dict or a list of 2-typles keyed by strings and
    valued by ints."""
    def __init__(self, container={}):
        """Initialize IdContainer.

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
    state = IdContainer()
    while reader.iter.getRemainingSize() > 0:
        k = reader.read(str)
        if k == "end":
            return state
        v = reader.read(int)
        state[k] = v
    return state

def container_to_ids(container):
    """Convert a container (Character attribute) to one sendable over the network"""
    return IdContainer({slot: item.uiid if item is not None else -1
                          for slot, item in container.items()})

def ids_to_container(init_container):
    """Convert an IdContainer (dict mapping slots to uiids) to a dict of Items"""
    return {slot: network.uiid_to_item.get(itemid, None) for slot, itemid in init_container.items()}
