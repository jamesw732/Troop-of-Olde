"""Represents the physical player/npc entities in game as understood by the server.
Clients will never initialize a Character object, only the server will."""
from ursina import *

from . import sqdist, default_cb_attrs, default_phys_attrs, default_equipment, default_inventory, all_skills
from .combat import *
from .physics import handle_movement
from .gamestate import gs
from .item import Item, equip_many_items
from .power import Power
from .skills import *
from .states.container import IdContainer
from .states.state import *

class Character(Entity):
    def __init__(self, cname="Player", uuid=None, 
                 pstate=None, base_state=None,
                 equipment={}, inventory={}, skills={}, lexicon={}):
        """Initializes a character on the server. Characters corresponding to player characters
        will have the states sent to the server (the server doesn't store player data), while
        NPC's have their states read from a file or generated.

        cname: name of character, str
        uuid: unique id. Used to encode which player you're talking about online.
        pstate: State; defines physical attrs, these are updated client-authoritatively
        base_state: State; used to build the character's stats from the ground up
        equipment: dict of Items keyed by slot, or IdContainer of item id's keyed by slot
        inventory: dict of Items keyed by index within inventory, 0-23, or IdContainer of item id's keyed by slot
        skills: State dict mapping str skill names to int skill levels
        lexicon: IdContainer mapping slot to power id
        """
        assert gs.network.peer.is_hosting()
        # Character-specific attrs
        self.controller = None
        self.cname = cname
        self.uuid = uuid
        # Update timer for attrs that don't get overwritten by
        # state updates, but still should be affected by state updates
        self.sec_update_rate = 1
        self.sec_update_timer = 0

        # Physical attrs
        # First, initialize Entity
        super().__init__()
        # Initialize base physical attributes
        self._init_phys_attrs()
        # Apply phys state, overwriting some of the initialized attrs
        if pstate:
            pstate.apply(self)

        self._init_equipment()
        self._init_inventory()

        self._init_powers()
        # Combat attrs
        self._init_cb_attrs()
        if inventory:
            for slot, item in inventory.items():
                if isinstance(item, (int, str)):
                    # handle it as an id
                    self.inventory[slot] = Item(str(item))
                else:
                    self.inventory[slot] = item
        if lexicon:
            for i, power_id in lexicon.items():
                self.lexicon[i] = Power(power_id)

        # Full creation of character from the ground up
        if base_state:
            base_state.apply(self)
        if equipment:
            if isinstance(equipment, IdContainer):
                equipment = {slot: Item(itemid) for slot, itemid in equipment.items()}
            equip_many_items(self, equipment)
        # ... apply effects
        self.update_max_ratings()
        for attr in ["health", "energy", "armor"]:
            maxval = getattr(self, "max" + attr)
            setattr(self, attr, maxval)

        self.skills = {skill: skills.get(skill, 1) for skill in all_skills}

    def update(self):
        """Character updates which happen every frame"""
        # Movement Handling

        handle_movement(self)
        # Combat Handling
        if self.target and not self.target.alive:
            self.target = None
            self.combat_timer = 0
        if self.target and self.target.alive and self.in_combat:
            if progress_mh_combat_timer(self) and self.get_target_hittable(self.equipment["mh"]):
                hit, msg = attempt_melee_hit(self, self.target, "mh")
                mh_skill = get_wpn_style(self.equipment["mh"])
                if hit and check_raise_skill(self, mh_skill):
                    raise_skill(self, mh_skill)
                conn = gs.network.uuid_to_connection.get(self.uuid, None)
                if conn is not None:
                    gs.network.peer.remote_print(conn, msg)
                    # Should add some sort of check to make sure this isn't happening too often
                    gs.network.broadcast_cbstate_update(self.target)
            # See if we should progress offhand timer too
            # (if has skill dw):
            mh_is_1h = self.equipment["mh"] is None \
                or self.equipment["mh"]["info"]["style"][:2] == "1h"
            offhand = self.equipment["oh"]
            # basically just check if not wearing a shield
            dual_wielding =  mh_is_1h and (offhand is None or offhand.get("type") == "weapon")
            if dual_wielding and progress_oh_combat_timer(self)\
            and self.get_target_hittable(self.equipment["oh"]):
                hit, msg = attempt_melee_hit(self, self.target, "oh")
                oh_skill = get_wpn_style(self.equipment["oh"])
                if hit and check_raise_skill(self, oh_skill):
                    raise_skill(self, oh_skill)
                conn = gs.network.uuid_to_connection.get(self.uuid, None)
                if conn is not None:
                    gs.network.peer.remote_print(conn, msg)
                    gs.network.broadcast_cbstate_update(self.target)
        else:
            self.mh_combat_timer = 0
            self.oh_combat_timer = 0

        # Death Handling
        if self.health <= 0:
            # Wait for server to tell character to die
            self.die()

    def _init_phys_attrs(self):
        """Initialize base physical attributes. These are likely to change."""
        for attr, val in default_phys_attrs.items():
            setattr(self, attr, copy(val))
        self.ignore_traverse = [self]

    def _init_cb_attrs(self):
        """Initialize base default combat attributes."""
        for attr, val in default_cb_attrs.items():
            setattr(self, attr, val)

    def _init_equipment(self):
        """Initialize equipment dict"""
        self.equipment = copy(default_equipment)

    def _init_inventory(self):
        self.inventory = copy(default_inventory)

    def _init_powers(self):
        self.lexicon = {}

    def _update_jump_attrs(self):
        """Adjust secondary physical attributes to state changes.
        These attrs are not adjusted directly by state changes,
        but still deserve to be updated when state changes occur."""
        self.height = self.scale_y
        self.max_jump_height = self.height * 1.5
        self.max_jump_time = 0.3
        if not self.jumping:
            self.rem_jump_height = self.max_jump_height
            self.rem_jump_time = self.max_jump_time

    def update_max_ratings(self):
        """Adjust max ratings, for example after receiving a staet update."""
        self.maxhealth = self.statichealth
        self.maxenergy = self.staticenergy
        self.health = min(self.maxhealth, self.health)
        self.energy = min(self.maxenergy, self.energy)

    def start_jump(self):
        """Set self.jumping to be true if not grounded"""
        if self.grounded:
            self.jumping = True

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
                                ignore=[entity for entity in scene.entities if type(entity) is Character])
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

        # don't compute the distance between their centers, compute the distance between
        # their bodies
        inner_distance = distance(point1, point2)
        in_range = inner_distance <= atk_range
        if in_range:
            return True
        else:
            conn = gs.network.uuid_to_connection[self.uuid]
            gs.network.peer.remote_print(conn, f"{self.target.cname} is out of range!")
            return False

    def on_destroy(self):
        """Upon being destroyed, remove all references to objects attached to this character. This
        is likely not perfect, and I imagine that characters will continue to live after being 
        destroyed."""
        if self.uuid is not None:
            del gs.network.uuid_to_char[self.uuid]
        try:
            gs.chars.remove(self)
        except:
            pass
        if self.controller:
            destroy(self.controller)
            del self.controller.character
            del self.controller
        del self.ignore_traverse

    def die(self):
        """Essentially just destroy self and make sure the rest of the network knows if host."""
        gs.network.broadcast(gs.network.peer.remote_death, self.uuid)
        self.alive = False
        destroy(self)

    def increase_health(self, amt):
        """Function to be used whenever increasing character's health"""
        self.health = min(self.maxhealth, self.health + amt)

    def reduce_health(self, amt):
        """Function to be used whenever decreasing character's health"""
        self.health -= amt
