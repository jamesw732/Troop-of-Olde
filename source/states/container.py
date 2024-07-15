class InitContainer(dict):
    """Use this class to initialize containers upon login

    Structure may be misleading, use the JSON for types - keys are always
    strings and values are always ints."""
    def __init__(self, container={}):
        for slot, itemid in container.items():
            self[slot] = itemid


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
