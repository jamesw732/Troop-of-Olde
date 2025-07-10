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

from .base import default_cb_attrs, default_phys_attrs, all_skills, sqdist, default_num_powers
from .combat import get_wpn_range
from .states import *

class Character(Entity):
    def __init__(self, uuid, pstate=PhysicalState(), inventory=[], equipment=[],
                 skills=SkillsState(), powers=[]):
        """Base Character class representing the intersection of server and client-side Characters.

        Functionality from here should liberally be pulled into ClientCharacter and ServerCharacter
        when necessary.
        cname: name of character, str
        uuid: unique id. Used to encode which player you're talking about online.
        pstate: PhysicalState; defines physical attrs, these are updated client-authoritatively
        base_state: BaseCombatState; used to build the character's stats from the ground up
        skills: SkillsState dict mapping str skill names to int skill levels
        """
        self.uuid = uuid

        self.namelabel = None

        self.model_child = Actor()
        self._model_name = ""
        super().__init__()

        # Initialize default values for everything
        # Physical attrs
        for attr, val in default_phys_attrs.items():
            setattr(self, attr, copy(val))
        self.ignore_traverse = [self]
        # Combat attrs
        for attr, val in default_cb_attrs.items():
            setattr(self, attr, val)
        self.targeted_by = []
        # Populate all attrs
        pstate.apply(self)
        self.equipment = equipment
        self.inventory = inventory
        self.num_powers = default_num_powers
        self.powers = powers

        # self.skills = {skill: skills.get(skill, 1) for skill in all_skills}
        self.skills = {skill: skills[i] for i, skill in enumerate(all_skills)}

    def update_max_ratings(self):
        """Adjust max ratings, for example after receiving a stat update."""
        self.maxhealth = self.statichealth
        self.maxenergy = self.staticenergy
        self.health = min(self.maxhealth, self.health)
        self.energy = min(self.maxenergy, self.energy)

    def increase_health(self, amt):
        """Function to be used whenever increasing character's health"""
        self.health = min(self.maxhealth, self.health + amt)

    def reduce_health(self, amt):
        """Function to be used whenever decreasing character's health"""
        self.health -= amt

    def start_jump(self):
        """Do the things required to make the character jump"""
        if self.grounded:
            self.jumping = True
            self.grounded = False

    def cancel_jump(self):
        """Reset self.jumping, remaining jump height"""
        self.jumping = False
        self.rem_jump_height = self.max_jump_height

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

    def tick_gcd(self):
        """Ticks up the global cooldown for powers"""
        self.gcd_timer = min(self.gcd_timer + time.dt, self.gcd)

    def get_on_gcd(self):
        """Returns whether the character is currently on the global cooldown for powers"""
        return self.gcd_timer < self.gcd