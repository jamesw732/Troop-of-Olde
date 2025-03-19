from . import network
from ..states.state import State, serialize_state, deserialize_state
from ..states.container import IdContainer, serialize_init_container, deserialize_init_container

network.peer.register_type(IdContainer, serialize_init_container, deserialize_init_container)
network.peer.register_type(State, serialize_state, deserialize_state)
