import os

from ursina import *
from ursina.mesh_importer import imported_meshes
from direct.actor.Actor import Actor
from panda3d.core import NodePath, TransparencyAttrib

from .. import *


class ClientCharacter(Character):
    def __init__(self, **kwargs):
        """Initialize a Character for the Client.

        Generally shouldn't be called directly, instead Characters should be
        created by World.make_pc or World.make_npc. This is mainly because
        updating the uuid maps is done in World, and World contains helpful
        functions for interfacing with the network.
        kwargs is obtained from World.make_pc_init_dict or World.make_npc_init_dict,
        it is just a dict of attrs to loop through and set.
        """
        self.model_child = Actor()
        super().__init__()
        for key, val in kwargs.items():
            setattr(self, key, val)
        if self.equipment is not None:
            for idx, item in enumerate(self.equipment):
                if item is None:
                    continue
                item.auto_set_leftclick(self.equipment)
        if self.equipment is not None:
            for idx, item in enumerate(self.inventory):
                if item is None:
                    continue
                item.auto_set_leftclick(self.inventory)

        self.clickbox = ClickBox(self)
        self.namelabel = None

    @Character.model_name.setter
    def model_name(self, new_model):
        """When setting model, update actor and name

        new_model: name of model file (no other path information)"""
        self.model_child.detachNode()
        path = os.path.join(models_path, new_model)
        self.model_child = Actor(path)
        self.model_child.reparent_to(self)
        # Rotate 180 degrees
        self.model_child.setH(180)
        self.model_child.setColor(self.color)
        # Enable transparency
        # self.model_child.set_transparency(TransparencyAttrib.M_alpha)
        self._model_name = new_model

    @Character.model_color.setter
    def model_color(self, new_color):
        if isinstance(new_color, str):
            new_color = color.colors[new_color]
        self.model_child.setColor(new_color)
        self._model_color = new_color

    def __repr__(self):
        return self.cname

class ClickBox(Entity):
    def __init__(self, parent, scale=Vec3(1, 1, 1)):
        super().__init__(parent=parent, scale=scale, origin=Vec3(0, -0.5, 0),
                       model="cube", collider="box", visible=False)