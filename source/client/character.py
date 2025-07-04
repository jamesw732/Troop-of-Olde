import os

from ursina import *
from ursina.mesh_importer import imported_meshes
from direct.actor.Actor import Actor
from panda3d.core import NodePath

from ..character import Character
from ..item import Item, Container
from .power import ClientPower
from ..states import *


class ClientCharacter(Character):
    def __init__(self, uuid=None, pstate=PhysicalState(), cbstate=BaseCombatState(),
                 equipment=[], inventory=[], skills=SkillsState(), powers=[]):
        """Initialize a Character for the Client.
        Args obtained from states.get_character_states_from_data.

        cname: name of character, str
        uuid: unique id. Used to encode which player you're talking about online.
        pstate: State; defines physical attrs, these are updated client-authoritatively
        base_state: State; used to build the character's stats from the ground up
        equipment: list of Items or item ids or tuples of item ids and inst item ids
        inventory: list of Items or item ids or tuples of item ids and inst item ids
        skills: State dict mapping str skill names to int skill levels
        powers: list of Powers or power Ids
        """
        if equipment:
            equipment_id = equipment[0]
            equipment = equipment[1:]
            self.equipment = Container(equipment_id, "equipment", equipment)
            for slot, item_ids in enumerate(equipment):
                if item_ids[0] < 0 or item_ids[1] < 0:
                    self.equipment[slot] = None
                    continue
                item = Item(*item_ids)
                self.equipment[slot] = item
                item.auto_set_leftclick(self.equipment)
        if inventory:
            inventory_id = inventory[0]
            inventory = inventory[1:]
            self.inventory = Container(inventory_id, "inventory", inventory)
            for slot, item_ids in enumerate(inventory):
                if item_ids[0] < 0 or item_ids[1] < 0:
                    self.inventory[slot] = None
                    continue
                item = Item(*item_ids)
                self.inventory[slot] = item
                item.auto_set_leftclick(self.inventory)
        super().__init__(uuid=uuid, pstate=pstate, cbstate=cbstate, skills=skills)
        for i, power_ids in enumerate(powers):
            if power_ids[0] < 0 or power_ids[1] < 0:
                continue
            self.powers[i] = ClientPower(self, *power_ids)

    @property
    def model_name(self):
        """When accessing model, return the name of the model"""
        return self._model_name

    @model_name.setter
    def model_name(self, new_model):
        """When setting model, update actor and name

        new_model: name of model file (no other path information)"""
        self.model_child.detachNode()
        path = os.path.join(models_path, new_model)
        self.model_child = Actor(path)
        self.model_child.reparent_to(self)
        self.model_child.setH(180)
        self.model_child.setColor(self.color)
        self.model_child.loop("Idle")
        self._model_name = new_model

    @property
    def color(self):
        return Vec4(self.model_child.getColor())

    @color.setter
    def color(self, new_color):
        if isinstance(new_color, str):
            new_color = color.colors[new_color]
        self.model_child.setColor(new_color)

    def die(self):
        """Essentially just destroy self and make sure the rest of the network knows if host."""
        self.alive = False
        destroy(self)