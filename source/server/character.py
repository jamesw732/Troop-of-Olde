"""Represents the physical player/npc entities in game, unified for both
the server and client.
The functionality of Characters on the client and server is very different,
(and also player characters vs NPCs), but these distinctions are delegated
to the respective controllers in controllers.py.
"""
import os

from ursina import *
from ursina.mesh_importer import imported_meshes
from direct.actor.Actor import Actor
from panda3d.core import NodePath

from .item import ServerItem, ServerContainer
from .power import ServerPower
from .. import *

class ServerCharacter(Character):
    def __init__(self, uuid, pstate=PhysicalState(), cbstate=BaseCombatState(),
                 equipment=[], inventory=[], skills=SkillsState(), powers=[],
                 on_destroy=lambda: None):
        """Initialize a Character for the server.

        uuid: unique id. Used to refer to Characters over network.
        pstate: PhysicalState; defines physical attrs
        cbstate: BaseCombatState; defines base combat stats, not accounting for
        external sources like items or effects
        equipment: list of Items
        inventory: list of Items
        skills: SkillsState
        powers: list of Powers
        """
        super().__init__(uuid, pstate=pstate, equipment=equipment,
                         inventory=inventory, skills=skills)
        cbstate.apply(self)
        self.on_destroy = on_destroy
        for item in self.equipment:
            if item is None:
                continue
            item.handle_stats(self, self.equipment)
        for i, power_id in enumerate(powers):
            if power_id < 0:
                continue
            self.powers[i] = ServerPower(power_id)

        self.update_max_ratings()

    @property
    def model_name(self):
        """Get model name."""
        return self._model_name

    @model_name.setter
    def model_name(self, new_model):
        """Update model. Unlike ClientCharacter, does not update anything else
        since server only needs the name of the model.
        If this changes, just move corresponding ClientCharacter functions to Character
        new_model: name of model file (no other path information)"""
        self._model_name = new_model
