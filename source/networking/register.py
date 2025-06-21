from .network import network
from ..states.state import State, serialize_state, deserialize_state
from ..states.state2 import *

network.peer.register_type(State, serialize_state, deserialize_state)
network.peer.register_type(BaseCombatState, BaseCombatState.serialize, BaseCombatState.deserialize)
network.peer.register_type(SkillsState, SkillsState.serialize, SkillsState.deserialize)
network.peer.register_type(PlayerCombatState, PlayerCombatState.serialize, PlayerCombatState.deserialize)
network.peer.register_type(NPCCombatState, NPCCombatState.serialize, NPCCombatState.deserialize)
network.peer.register_type(PhysicalState, PhysicalState.serialize, PhysicalState.deserialize)
