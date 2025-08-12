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

from .. import *

class ServerCharacter(Character):
    def __init__(self, **kwargs):
        """Initialize a Character for the server.

        Generally shouldn't be called directly, instead Characters should be
        created by World.make_char. This is mainly because updating the uuid maps
        is done in World, and World contains helpful functions for interfacing with
        the network.
        kwargs is obtained from World.make_char_init_dict, it is just
        a dict of attrs to loop through and set.
        """
        super().__init__()
        for key, val in kwargs.items():
            setattr(self, key, val)

        for item in self.equipment:
            if item is None:
                continue
            item.stats.apply_diff(self)
        self.update_max_ratings()
        self.effects = []
