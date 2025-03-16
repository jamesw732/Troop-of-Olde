"""Represents the physical player/npc entities in game as understood by the server.
Clients will never initialize a Character object, only the server will."""
from ursina import *

from . import sqdist, default_cb_attrs, default_phys_attrs, default_equipment, default_inventory
from .combat import progress_mh_combat_timer, progress_oh_combat_timer, attempt_melee_hit, get_target_hittable
from .networking import network
from .networking.world_responses import remote_death
from .physics import handle_movement
from .gamestate import gs
from .item import Item, equip_many_items
from .power import Power
from .states.cbstate_base import BaseCombatState, apply_base_state
from .states.container import IdContainer
from .states.physicalstate import PhysicalState, apply_physical_state
from .states.skills import SkillState
from .ui.main import ui

class Character(Entity):
    def __init__(self, cname="Player", uuid=None, 
                 pstate=None, base_state=None,
                 equipment={}, inventory={}, skills={}, lexicon={}):
        """Initializes a character on the server. Characters corresponding to player characters
        will have the states sent to the server (the server doesn't store player data), while
        NPC's have their states read from a file or generated.

        cname: name of character, str
        uuid: unique id. Used to encode which player you're talking about online.
        pstate: PhysicalState; defines physical attrs, these are updated client-authoritatively
        base_state: BaseCombatState; used to build the character's stats from the ground up
        equipment: dict of Items keyed by slot, or IdContainer of item id's keyed by slot
        inventory: dict of Items keyed by index within inventory, 0-23, or IdContainer of item id's keyed by slot
        skills: SkillState dict mapping str skill names to int skill levels
        lexicon: IdContainer mapping slot to power id
        """
        assert network.peer.is_hosting()
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
            apply_physical_state(self, pstate)

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
            for i, power_id in lexicon["page1"].items():
                self.page1[i] = Power(power_id, self)
            for i, power_id in lexicon["page2"].items():
                self.page2[i] = Power(power_id, self)

        # Full creation of character from the ground up
        if base_state:
            apply_base_state(self, base_state)
        if equipment:
            if isinstance(equipment, IdContainer):
                equipment = {slot: Item(itemid) for slot, itemid in equipment.items()}
            equip_many_items(self, equipment)
        # ... apply effects
        self.update_max_ratings()
        for attr in ["health", "energy", "armor"]:
            # if not hasattr(base_state, attr):
            maxval = getattr(self, "max" + attr)
            setattr(self, attr, maxval)

        self.skills = skills

    def update(self):
        """Character updates which happen every frame"""
        # Movement Handling

        handle_movement(self)
        # Combat Handling
        if self.target and not self.target.alive:
            self.target = None
            self.combat_timer = 0
        if self.target and self.target.alive and self.in_combat:
            if progress_mh_combat_timer(self) and get_target_hittable(self, self.equipment["mh"]):
                msg = attempt_melee_hit(self, self.target, "mh")
                conn = network.uuid_to_connection.get(self.uuid, None)
                if conn is not None:
                    network.peer.remote_print(conn, msg)
            # See if we should progress offhand timer too
            # (if has skill dw):
            mh_is_1h = self.equipment["mh"] is None \
                or self.equipment["mh"]["info"]["style"][:2] == "1h"
            offhand = self.equipment["oh"]
            # basically just check if not wearing a shield
            dual_wielding =  mh_is_1h and (offhand is None or offhand.get("type") == "weapon")
            if dual_wielding and progress_oh_combat_timer(self)\
            and get_target_hittable(self, self.equipment["oh"]):
                msg = attempt_melee_hit(self, self.target, "oh")
                conn = network.uuid_to_connection.get(self.uuid, None)
                if conn is not None:
                    network.peer.remote_print(conn, msg)
        else:
            self.mh_combat_timer = 0
            self.oh_combat_timer = 0

        # Death Handling
        if self.health <= 0:
            # Wait for server to tell character to die
            self.die()
                # for conn in network.peer.get_connections():
                #     network.peer.remote_death(conn, self.uuid)

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
        self.page1 = {}
        self.page2 = {}

    def _update_jump_attrs(self):
        """Adjust secondary physical attributes to state changes.
        These attrs are not adjusted directly by state changes,
        but still deserve to be updated by them."""
        self.height = self.scale_y
        self.max_jump_height = self.height * 1.5
        self.max_jump_time = 0.3
        if not self.jumping:
            self.rem_jump_height = self.max_jump_height
            self.rem_jump_time = self.max_jump_time

    def update_max_ratings(self):
        """Adjust secondary combat attributes to state changes.
        These attrs are not adjusted directly by state changes,
        but still deserve to be updated by them."""
        self.maxhealth = self.statichealth
        self.maxenergy = self.staticenergy
        self.health = min(self.maxhealth, self.health)
        self.energy = min(self.energy, self.energy)

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

    def on_destroy(self):
        """Upon being destroyed, remove all references to objects attached to this character"""
        if self.uuid is not None:
            del network.uuid_to_char[self.uuid]
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
        network.broadcast(network.peer.remote_death, self.uuid)
        self.alive = False
        destroy(self)