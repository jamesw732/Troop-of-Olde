import os

from ursina import *
from ursina.mesh_importer import imported_meshes
from direct.actor.Actor import Actor
from panda3d.core import NodePath, TransparencyAttrib

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
        self.model_child = Actor()
        super().__init__(uuid, pstate=pstate, equipment=equipment,
                         inventory=inventory, skills=skills, powers=powers)
        cbstate.apply(self)
        for idx, item in enumerate(self.equipment):
            if item is None:
                continue
            item.auto_set_leftclick(self.equipment)
        for idx, item in enumerate(self.inventory):
            if item is None:
                continue
            item.auto_set_leftclick(self.inventory)
        self.on_destroy = on_destroy

    @Character.model_name.setter
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
        self.model_child.set_transparency(TransparencyAttrib.M_alpha)
        self._model_name = new_model

    @Character.model_color.setter
    def model_color(self, new_color):
        if isinstance(new_color, str):
            new_color = color.colors[new_color]
        self.model_child.setColor(new_color)
        self._model_color = new_color

    def __repr__(self):
        return self.cname