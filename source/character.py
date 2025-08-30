"""Represents the physical player/npc entities in game, unified for both
the server and client.
The functionality of Characters on the client and server is very different,
(and also player characters vs NPCs), but these distinctions are delegated
to the respective controllers in controllers.py.
"""
import os

from ursina import *
from ursina.mesh_importer import imported_meshes
from panda3d.core import NodePath

from .base import *
from .states import *

class Character(Entity):
    def __init__(self):
        """Base Character class representing the intersection of server and client-side Characters.

        Populates default values for everything.
        """
        super().__init__()
        for attr, val in default_char_attrs.items():
            setattr(self, attr, copy(val))
        for attr, val in init_char_attrs.items():
            setattr(self, attr, copy(val))

    def set_target(self, target):
        if self.target is not target:
            target.targeted_by.append(self)
        self.target = target

    def get_tgt_los(self, target):
        """Returns whether the target is in line of sight"""
        sdist = sqdist(self.position, self.target.position)
        src_pos = self.position + Vec3(0, 0.8 * self.scale_y, 0)
        tgt_pos = target.position + Vec3(0, 0.8 * target.scale_y, 0)
        dir = tgt_pos - src_pos
        line_of_sight = raycast(src_pos, direction=dir, distance=inf,
                                ignore=[entity for entity in scene.entities if isinstance(entity, Character)])
        if line_of_sight.hit:
            entity = line_of_sight.entity
            if sqdist(entity.position, self.position) < sdist:
                return False
        return True

    def start_gcd(self, gcd):
        self.gcd = gcd
        self.gcd_timer = 0

    def tick_gcd(self, dt):
        """Ticks up the global cooldown for powers"""
        self.gcd_timer = min(self.gcd_timer + dt, self.gcd)

    def get_on_gcd(self):
        """Returns whether the character is currently on the global cooldown for powers"""
        return self.gcd_timer < self.gcd

    @property
    def model_name(self):
        """Getter for model_name property, used for interoperability with
        the Panda3D Actor ClientCharacter.model_child"""
        return self._model_name

    @model_name.setter
    def model_name(self, new_model):
        """Setter for model_name property, used for interoperability
        with the Panda3D Actor ClientCharacter.model_child

        new_model: name of model file (no other path information)"""
        self._model_name = new_model

    @property
    def model_color(self):
        """Getter for model_color property, used for interoperability
        with the Panda3D Actor ClientCharacter.model_child"""
        return self._model_color

    @model_color.setter
    def model_color(self, new_color):
        """Setter for model_color property, used for interoperability
        with the Panda3D Actor ClientCharacter.model_child

        new_color: name of model file (no other path information)"""
        if isinstance(new_color, str):
            new_color = color.colors[new_color]
        self._model_color = new_color

    @property
    def equipment_id(self):
        if not self.equipment:
            return -1
        return self.equipment.inst_id

    @property
    def equipment_inst_ids(self):
        if not self.equipment:
            return [-1] * num_equipment_slots
        return [item.inst_id if item else -1 for item in self.equipment]

    @property
    def inventory_id(self):
        if not self.inventory:
            return -1
        return self.inventory.inst_id

    @property
    def inventory_inst_ids(self):
        if not self.inventory:
            return [-1] * num_inventory_slots
        return [item.inst_id if item else -1 for item in self.inventory]

    @property
    def powers_inst_ids(self):
        if not self.powers:
            return [-1] * default_num_powers
        return [power.inst_id if power else -1 for power in self.powers]