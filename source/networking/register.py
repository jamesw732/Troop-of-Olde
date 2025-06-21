from .network import network
from ..states import *

network.peer.register_type(BaseCombatState, BaseCombatState.serialize, BaseCombatState.deserialize)
network.peer.register_type(SkillsState, SkillsState.serialize, SkillsState.deserialize)
network.peer.register_type(PlayerCombatState, PlayerCombatState.serialize, PlayerCombatState.deserialize)
network.peer.register_type(NPCCombatState, NPCCombatState.serialize, NPCCombatState.deserialize)
network.peer.register_type(PhysicalState, PhysicalState.serialize, PhysicalState.deserialize)
network.peer.register_type(ItemStats, ItemStats.serialize, ItemStats.deserialize)
