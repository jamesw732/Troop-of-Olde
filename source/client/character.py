import os

from ursina import *
from ursina.mesh_importer import imported_meshes
from direct.actor.Actor import Actor
from panda3d.core import NodePath

from .power import ClientPower
from .. import *


class ClientCharacter(Character):
    def __init__(self, uuid, pstate=PhysicalState(), cbstate=PlayerCombatState(),
                 equipment=[], inventory=[], skills=SkillsState(), powers=[],
                 on_destroy=lambda: None):
        """Initialize a Character for the Client.

        uuid: unique id. Used to encode which player you're talking about online.
        pstate: PhysicalState; defines physical attrs
        cbstate: PlayerCombatState; overwrites all combat stats
        equipment: list of Items
        inventory: list of Items
        skills: SkillsState
        powers: list of Powers
        """
        super().__init__(uuid, pstate=pstate, equipment=equipment,
                         inventory=inventory, skills=skills)
        cbstate.apply(self)
        for idx, item in enumerate(self.equipment):
            if item is None:
                continue
            item.auto_set_leftclick(self.equipment)
        for idx, item in enumerate(self.inventory):
            if item is None:
                continue
            item.auto_set_leftclick(self.inventory)
        for i, power_ids in enumerate(powers):
            if power_ids[0] < 0 or power_ids[1] < 0:
                continue
            self.powers[i] = ClientPower(self, *power_ids)
        self.on_destroy = on_destroy

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