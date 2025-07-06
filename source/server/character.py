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
    def __init__(self, uuid=None, pstate=PhysicalState(), cbstate=BaseCombatState(),
                 equipment=[], inventory=[], skills=SkillsState(), powers=[]):
        """Initialize a Character for the server.
        Args obtained from states.get_character_states_from_json.

        cname: name of character, str
        uuid: unique id. Used to encode which player you're talking about online.
        pstate: State; defines physical attrs, these are updated client-authoritatively
        base_state: State; used to build the character's stats from the ground up
        equipment: list of Items or item ids or tuples of item ids and inst item ids
        inventory: list of Items or item ids or tuples of item ids and inst item ids
        skills: State dict mapping str skill names to int skill levels
        powers: list of Powers or power Ids
        """
        super().__init__(uuid=uuid, pstate=pstate, cbstate=cbstate, skills=skills)
        self.inventory = ServerContainer("inventory", default_inventory)
        self.equipment = ServerContainer("equipment", default_equipment)
        for slot, item_id in enumerate(inventory):
            if item_id < 0:
                continue
            item = ServerItem(item_id)
            self.inventory[slot] = item
            item.auto_set_leftclick(self.inventory)
        for slot, item_id in enumerate(equipment):
            if item_id < 0:
                continue
            item = ServerItem(item_id)
            self.equipment[slot] = item
            item.handle_stats(self, self.equipment)
            item.auto_set_leftclick(self.equipment)
        for i, power_id in enumerate(powers):
            if power_id < 0:
                continue
            self.powers[i] = ServerPower(self, power_id)

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

    def die(self):
        """Essentially just destroy self and make sure the rest of the network knows if host."""
        network.broadcast(network.peer.remote_death, self.uuid)
        self.alive = False
        destroy(self)