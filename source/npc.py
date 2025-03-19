"""Represents the physical npc entities in game according to the client.
Only to be initialized by the client."""
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

class NPC(Entity):
    def __init__(self, cname="NPC", uuid=None,
                 pstate=None, cb_state=None,
                 equipment={}, inventory={}, skills={}):
        """Initializes an NPC given some states. Functionally a pretty bare-bones class, NPC's
        are basically zombies that are capable of LERPing and animations, but that's about it.

        cname: name of character, str
        uuid: unique id, only relevant if on network. Used to encode which player you're talking about online.
        type: "player" or "npc"
        pstate: State; defines client-authoritative attrs
        cb_state: State; Only initializes the most minimal attrs that the player needs to see
        from NPC's.
        equipment: dict of Items keyed by slot, or IdContainer of item id's keyed by slot
        inventory: dict of Items keyed by index within inventory, 0-23, or IdContainer of item id's keyed by slot
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
            apply_physical_state(self, pstate)
        # Make namelabel
        self.namelabel = NameLabel(self)
        # Finally, prep lerp
        self._init_lerp_attrs()

        self._init_equipment()
        self._init_inventory()

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

        # Host created a character that isn't mine
        if cb_state:
            apply_state(self, cb_state)

        self.skills = {skill: skills.get(skill, 1) for skill in all_skills}

    def update(self):
        """Character updates which happen every frame"""
        # Movement Handling
        if self.lerping and self.prev_state:
            self.lerp_timer += time.dt
            # If timer finished, just apply the new state
            if self.lerp_timer >= self.lerp_rate:
                self.lerping = False
                apply_physical_state(self, self.new_state)
            # Otherwise, LERP normally
            else:
                self.position = lerp(self.prev_state.get("position", self.position),
                                     self.new_state.get("position", self.position),
                                     self.lerp_timer / self.lerp_rate)
                self.rotation = lerp(self.prev_state.get("rotation", self.rotation),
                                     self.new_state.get("rotation", self.rotation),
                                     self.lerp_timer / self.lerp_rate)
        # Namelabel Handling
        self.namelabel.fix_position()
        self.namelabel.fix_rotation()
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

    def _init_lerp_attrs(self):
        """Initialize lerp logic"""
        self.prev_state = None
        self.new_state = State("physical", self)
        self.prev_lerp_recv = 0
        self.lerping = False
        self.lerp_rate = 0
        self.lerp_timer = 0.2

    def _init_equipment(self):
        """Initialize equipment dict"""
        self.equipment = copy(default_equipment)

    def _init_inventory(self):
        self.inventory = copy(default_inventory)

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

    def update_lerp_state(self, state, time):
        """Essentially just increments the lerp setup.
        Slide prev and new state, set self.lerping = True, and apply old state"""
        self.prev_state = self.new_state
        self.new_state = state
        if self.prev_state:
            self.lerping = True
            self.lerp_rate = time - self.prev_lerp_recv
            self.prev_lerp_recv = time
            self.lerp_timer = 0
            # Apply old state to ensure synchronization and update non-lerp attrs
            apply_physical_state(self, self.prev_state)

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
