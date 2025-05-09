"""Represents the physical player/npc entities in game.

Currently incomplete, meant to be a unification of characters (both NPC and PC) for both the server
and client. Distinctions between these things will be delegated to the respective controllers.

Currently missing functionality that needs to be translated over to controllers:
Movement/jumping
Combat
"""

from ursina import *

from . import default_cb_attrs, default_phys_attrs, default_equipment, default_inventory, all_skills
from .gamestate import gs
from .item import Item, equip_many_items
from .physics import *
from .power import Power
from .skills import *
from .states.state import *
from .states.container import IdContainer


class Character(Entity):
    def __init__(self, cname="Player", uuid=None, 
                 pstate=None, cbstate=None,
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
        self.cname = cname
        self.uuid = uuid

        self.controller = None
        self.namelabel = None

        # Physical attrs
        # First, initialize Entity
        super().__init__()

        # Initialize default values for everything
        self._init_phys_attrs()
        self._init_equipment()
        self._init_inventory()
        self._init_powers()
        self._init_cb_attrs()
        # Populate all attrs
        if pstate:
            pstate.apply(self)
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
        if cbstate:
            cbstate.apply(self)
        if equipment:
            if isinstance(equipment, IdContainer):
                equipment = {slot: Item(itemid) for slot, itemid in equipment.items()}
            equip_many_items(self, equipment)

        self.update_max_ratings()
        for attr in ["health", "energy", "armor"]:
            maxval = getattr(self, "max" + attr)
            setattr(self, attr, maxval)

        self.skills = {skill: skills.get(skill, 1) for skill in all_skills}

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

    def update(self):
        # This will eventually be moved to MobController, on a fixed
        # update rate
        handle_movement(self)

    def update_max_ratings(self):
        """Adjust max ratings, for example after receiving a staet update."""
        self.maxhealth = self.statichealth
        self.maxenergy = self.staticenergy
        self.health = min(self.maxhealth, self.health)
        self.energy = min(self.maxenergy, self.energy)

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

    def start_jump(self):
        """Do the things required to make the character jump"""
        if self.grounded:
            self.jumping = True
            self.grounded = False

    def cancel_jump(self):
        """Reset self.jumping, remaining jump height"""
        self.jumping = False
        self.rem_jump_height = self.max_jump_height
