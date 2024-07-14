class InitEquipmentState(dict):
    """Class used for sending equipment over network upon login.

    Somewhat incomplete, eventually will need to also allow for armor damage
    """
    def __init__(self, equipment={}):
        """equipment: dict of items loaded from """
        for slot, itemid in equipment.items():
            self[slot] = str(itemid)

    def __str__(self):
        super().__str__()


def serialize_init_equip_state(writer, state):
    for k, v in state.items():
        writer.write(k)
        writer.write(v)
    writer.write("end")

def deserialize_init_equip_state(reader):
    state = InitEquipmentState()
    while reader.iter.getRemainingSize() > 0:
        k = reader.read(str)
        if k == "end":
            return state
        v = reader.read(str)
        state[k] = v
    return state
