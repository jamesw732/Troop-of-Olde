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
from .gamestate import gs
from .states import *

class Character(Entity):
    def __init__(self, uuid=None, pstate=PhysicalState(), cbstate=BaseCombatState(), skills=SkillsState()):
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

        self.controller = None
        self.namelabel = None

        # First, initialize Entity
        super().__init__()

        # Initialize default values for everything
        self._init_phys_attrs()
        self._init_powers()
        self._init_cb_attrs()
        # Populate all attrs
        pstate.apply(self)
        cbstate.apply(self)

        # self.skills = {skill: skills.get(skill, 1) for skill in all_skills}
        self.skills = {skill: skills[i] for i, skill in enumerate(all_skills)}

    def _init_phys_attrs(self):
        """Initialize base physical attributes. These are likely to change."""
        self.model_child = Actor()
        self.model_child.setColor(color.orange)
        self._model_name = ""
        for attr, val in default_phys_attrs.items():
            setattr(self, attr, copy(val))
        self.ignore_traverse = [self]

    def _init_cb_attrs(self):
        """Initialize base default combat attributes."""
        for attr, val in default_cb_attrs.items():
            setattr(self, attr, val)

    def _init_powers(self):
        self.num_powers = default_num_powers
        self.powers = [None] * self.num_powers

    def update_max_ratings(self):
        """Adjust max ratings, for example after receiving a stat update."""
        self.maxhealth = self.statichealth
        self.maxenergy = self.staticenergy
        self.health = min(self.maxhealth, self.health)
        self.energy = min(self.maxenergy, self.energy)

    def on_destroy(self):
        """Upon being destroyed, remove all references to objects
        attached to this character. This is currently not perfect,
        need to remove every single reference and some are missing.
        Todo: Remove EVERY reference so char cna be garbage collected."""
        if self.uuid is not None:
            del gs.network.uuid_to_char[self.uuid]
        try:
            gs.chars.remove(self)
        except:
            pass
        if self.controller:
            destroy(self.controller)
            del self.controller
        del self.ignore_traverse

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

    def get_target_hittable(self, wpn):
        """Returns whether self.target is able to be hit, ie in LoS and within attack range"""
        if not self.get_tgt_los(self.target):
            conn = gs.network.uuid_to_connection[self.uuid]
            gs.network.peer.remote_print(conn, f"You can't see {self.target.cname}.")
            return False
        atk_range = get_wpn_range(wpn)
        # use center rather than center of feet
        pos_src = self.position + Vec3(0, self.scale_y / 2, 0)
        pos_tgt = self.target.position + Vec3(0, self.target.scale_y / 2, 0)
        ray_dir = pos_tgt - pos_src
        ray_dist = distance(pos_tgt, pos_src)
        # Draw a line between the two
        line1 = raycast(pos_src, direction=ray_dir, distance=ray_dist,
                       traverse_target=self)
        line2 = raycast(pos_tgt, direction=-ray_dir, distance=ray_dist,
                        traverse_target=self.target)
        # ie one char is inside the other
        if not line1.hit or not line2.hit:
            return True
        point1 = line1.world_point
        point2 = line2.world_point
        # don't compute the distance between their centers,
        # compute the distance between their bodies
        inner_distance = distance(point1, point2)
        in_range = inner_distance <= atk_range
        if in_range:
            return True
        else:
            conn = gs.network.uuid_to_connection[self.uuid]
            gs.network.peer.remote_print(conn, f"{self.target.cname} is out of range!")
            return False

    def tick_gcd(self):
        """Ticks up the global cooldown for powers"""
        self.gcd_timer = min(self.gcd_timer + time.dt, self.gcd)

    def get_on_gcd(self):
        """Returns whether the character is currently on the global cooldown for powers"""
        return self.gcd_timer < self.gcd