from .network import network
from ..states.state import State, serialize_state, deserialize_state

network.peer.register_type(State, serialize_state, deserialize_state)
