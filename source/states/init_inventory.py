class InitInventoryState(dict):
    """Class used for sending inventory over network upon login.

    Inherits dict so that empty spaces in inventory are allowed"""
    def __init__(self, inventory={}):
        for slot, itemid in inventory.items():
            self[slot] = str(itemid)

    def __str__(self):
        super().__str__()


def serialize_init_equip_state(writer, state):
    for k, v in state.items():
        writer.write(k)
        writer.write(v)
    writer.write("end")

def deserialize_init_invent_state(reader):
    state = InitInventoryState()
    while reader.iter.getRemainingSize() > 0:
        k = reader.read(int)
        if k == "end":
            return state
        v = reader.read(str)
        state[k] = v
    return state
