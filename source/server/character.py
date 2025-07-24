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

from .power import ServerPower
from .. import *

class ServerCharacter(Character):
    def __init__(self, uuid, pstate=None, cbstate=None,
                 equipment=None, inventory=None, skills=None, powers=None,
                 on_destroy=lambda: None):
        """Initialize a Character for the server.

        In general, defaults should only be used for ease of testing, when parts of the
        character are not necessary to define.
        uuid: unique id. Used to refer to Characters over network.
        pstate: PhysicalState
        cbstate: BaseCombatState, used as first step to build up combat attrs
        inventory: Container of num_inventory_slots Items
        equipment: Container of num_equipment_slots Items
        skills: list[int] containing skill levels
        powers: list of num_powers Powers
        """
        super().__init__(uuid, pstate=pstate, equipment=equipment,
                         inventory=inventory, skills=skills, powers=powers)
        if cbstate is not None:
            cbstate.apply(self)
        self.on_destroy = on_destroy
        for item in self.equipment:
            if item is None:
                continue
            item.handle_stats(self, self.equipment)
        self.update_max_ratings()
        self.effects = []
