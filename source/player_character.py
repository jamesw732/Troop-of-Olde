"""Represents the physical player entity in game according to the client.
Only to be initialized by a client, and only for the player character.
"""
from ursina import *
import json

from . import sqdist, default_cb_attrs, default_phys_attrs, default_equipment, default_inventory, all_skills
from .networking import network
from .networking.world_responses import remote_death
from .physics import handle_movement
from .gamestate import gs
from .item import Item, equip_many_items
from .power import Power
from .states.container import IdContainer
from .states.state import *
from .ui.main import ui

class PlayerCharacter(Entity):
    def __init__(self, cname="Player", uuid=None, 
                 pstate=None, cb_state=None, 
                 equipment={}, inventory={}, skills={}, lexicon={}):
        """Initializes the player character. Should only be called once per client.

        cname: name of character, str
        uuid: unique id, only relevant if on network. Used to encode which player you're talking about online.
        type: "player" or "npc"
        pstate: State; defines client-authoritative attrs
        cb_state: State; Skip any ground-up computation and just overwrite the combat attrs
        equipment: dict of Items keyed by slot, or IdContainer of item id's keyed by slot
        inventory: dict of Items keyed by index within inventory, 0-23, or IdContainer of item id's keyed by slot
        skills: State dict mapping str skill names to int skill levels
        lexicon: IdContainer mapping slot to power id
        """
        assert not network.peer.is_hosting()
        # Character-specific attrs
        self.cname = cname
        self.uuid = uuid
        self.controller = None

        # Physical attrs
        # First, initialize Entity
        super().__init__()
        # Initialize base physical attributes
        self._init_phys_attrs()
        # Apply phys state, overwriting some of the initialized attrs
        if pstate:
            apply_state(self, pstate)
        # Make namelabel
        self.namelabel = NameLabel(self)

        self._init_equipment()
        self._init_inventory()

        self._init_powers()
        # Combat attrs
        self._init_cb_attrs()

        if equipment:
            if isinstance(equipment, IdContainer):
                equipment = {slot: Item(itemid) for slot, itemid in equipment.items()}
            equip_many_items(self, equipment, handle_stats=False)

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

        # Host created my character
        if cb_state:
            apply_state(self, cb_state)

        self.skills = {skill: skills.get(skill, 1) for skill in all_skills}

    def update(self):
        """Character updates which happen every frame"""
        # Movement Handling
        handle_movement(self)
        # Namelabel Handling
        self.namelabel.fix_position()
        self.namelabel.fix_rotation()
        # Combat Handling
        if self.target and not self.target.alive:
            self.target = None
        # Death Handling

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
        destroy(self.namelabel)
        del self.namelabel
        del self.ignore_traverse

    def die(self):
        """Essentially just destroy self and make sure the rest of the network knows if host."""
        msg = f"{self.cname} perishes."
        ui.gamewindow.add_message(msg)
        self.alive = False
        destroy(self)

    def on_click(self):
        gs.playercontroller.set_target(self)


class NameLabel(Text):
    def __init__(self, char):
        """Creates a namelabel above a character"""
        super().__init__(char.cname, parent=scene, scale=10, origin=(0, 0, 0),
                         position=char.position + Vec3(0, char.height + 1, 0))
        self.char = char

    def fix_rotation(self):
        """Aim the namelabel at the player with the right direction"""
        if gs.pc:
            direction = gs.pc.position - camera.world_position
            self.look_at(direction + self.world_position)
            self.rotation_z = 0

    def fix_position(self):
        """Position the namelabel above the character"""
        self.position = self.char.position + Vec3(0, self.char.height + 1, 0)

