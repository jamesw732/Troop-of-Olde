from .base import network
from ..states.cbstate_complete import CompleteCombatState, serialize_complete_cb_state, \
        deserialize_complete_cb_state
from ..states.cbstate_base import BaseCombatState, serialize_base_cb_state, deserialize_base_cb_state
from ..states.cbstate_mini import MiniCombatState, serialize_mini_state, deserialize_mini_state
from ..states.container import InitContainer, serialize_init_container, deserialize_init_container
from ..states.physicalstate import PhysicalState, serialize_physical_state, deserialize_physical_state
from ..states.stat_change import StatChange, serialize_stat_change, deserialize_stat_change
from ..states.skills import SkillState, serialize_skill_state, deserialize_skill_state

network.peer.register_type(PhysicalState, serialize_physical_state,
                           deserialize_physical_state)
network.peer.register_type(CompleteCombatState, serialize_complete_cb_state,
                           deserialize_complete_cb_state)
network.peer.register_type(BaseCombatState, serialize_base_cb_state,
                           deserialize_base_cb_state)
network.peer.register_type(InitContainer, serialize_init_container, deserialize_init_container)
network.peer.register_type(MiniCombatState, serialize_mini_state,
                           deserialize_mini_state)
network.peer.register_type(StatChange, serialize_stat_change, deserialize_stat_change)
network.peer.register_type(SkillState, serialize_skill_state, deserialize_skill_state)
