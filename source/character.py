"""Represents the physical player/npc entities in game. Engine-relevant character
logic."""
from ursina import *
import json

from .base import sqdist, default_cb_attrs, default_phys_attrs, default_equipment, default_inventory
from .combat import progress_mh_combat_timer, progress_oh_combat_timer
from .networking.base import network
from .physics import handle_movement
from .gamestate import gs
from .item import Item, equip_many_items
from .states.cbstate_complete import apply_complete_cb_state
from .states.cbstate_base import BaseCombatState, apply_base_state
from .states.cbstate_mini import apply_mini_state
from .states.container import InitContainer
from .states.physicalstate import PhysicalState, apply_physical_state
from .states.skills import SkillState
from .ui.main import ui

class Character(Entity):
    def __init__(self, cname="Player", uuid=None, type="player",
                 pstate=None, base_state=None,
                 complete_cb_state=None, mini_state=None,
                 equipment={}, inventory={}, skills={}):
        """Initializes a character using a PhysicalState and one type of combat state.
        These options are explained below.

        cname: name of character, str
        uuid: unique id, only relevant if on network. Used to encode which player you're talking about online.
        type: "player" or "npc"
        pstate: PhysicalState; defines client-authoritative attrs
        base_state: BaseCombatState; Use for common initialization if the main client
            to build the character's stats from the ground up
        complete_cb_state: CompleteCombatState; If specified, skip any ground-up
            computation and just overwrite the combat attrs
        mini_state: MiniCombatState; If specified, only initializes the most minimal
            attrs that the player needs to see from other characters.
        equipment: dict of Items keyed by slot, or InitContainer of item id's keyed by slot
        inventory: dict of Items keyed by index within inventory, 0-23, or InitContainer of item id's keyed by slot
        """
        # Character-specific attrs
        self.type = type
        self.cname = cname
        self.uuid = uuid
        self.controller = None
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
        # Make namelabel
        self.namelabel = NameLabel(self)
        # Finally, prep lerp
        self._init_lerp_attrs()

        self._init_equipment()
        if type == 'player':
            self._init_inventory()
        # Combat attrs
        self._init_cb_attrs()
        if inventory and self.type == "player":
            for slot, item in inventory.items():
                if isinstance(item, (int, str)):
                    # handle it as an id
                    self.inventory[slot] = Item(str(item))
                else:
                    self.inventory[slot] = item
        # Full creation of character from the ground up
        if base_state:
            apply_base_state(self, base_state)
            if equipment:
                if isinstance(equipment, InitContainer):
                    equipment = {slot: Item(itemid) for slot, itemid in equipment.items()}
                equip_many_items(self, equipment)
            # ... apply effects
            self.update_max_ratings()
            for attr in ["health", "mana", "stamina", "armor", "spellshield"]:
                # if not hasattr(base_state, attr):
                maxval = getattr(self, "max" + attr)
                setattr(self, attr, maxval)
        # Host created my character
        elif complete_cb_state:
            apply_complete_cb_state(self, complete_cb_state)
        # Host created a character that isn't mine
        elif mini_state:
            apply_mini_state(self, mini_state)

        self.skills = skills

    def update(self):
        """Character updates which happen every frame"""
        # Movement Handling
        if not self.lerping:
            handle_movement(self)
        elif self.lerping and self.prev_state:
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
        # Combat Handling
        if self.target and not self.target.alive:
            self.target = None
            self.combat_timer = 0
        else:
            if self.target and self.target.alive and self.in_combat:
                progress_mh_combat_timer(self)
                # See if we should progress offhand timer too
                # (if has skill dw):
                mh_is_1h = self.equipment["mh"] is None \
                    or self.equipment["mh"]["info"]["style"][:2] == "1h"
                offhand = self.equipment["oh"]
                # basically just check if not wearing a shield
                dual_wielding =  mh_is_1h and (offhand is None or offhand.get("type") == "weapon")
                if dual_wielding:
                    progress_oh_combat_timer(self)
            else:
                self.mh_combat_timer = 0
                self.oh_combat_timer = 0
        # self._update_incremental_vals() # It might be nice to just do this exactly when needed, not incrementally...
        # Death Handling
        if self.health <= 0:
            # Wait for server to tell character to die
            if network.is_main_client():
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

    def _init_lerp_attrs(self):
        """Initialize lerp logic"""
        self.prev_state = None
        self.new_state = PhysicalState(self)
        self.prev_lerp_recv = 0
        self.lerping = False
        self.lerp_rate = 0
        self.lerp_timer = 0.2

    def _init_equipment(self):
        """Initialize equipment dict"""
        self.equipment = copy(default_equipment)

    def _init_inventory(self):
        self.inventory = copy(default_inventory)

    def _update_sec_phys_attrs(self):
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
        self.maxhealth = self.statichealth + self.bdy * 10
        self.maxmana = self.staticmana + self.int * 10
        self.maxstamina = self.staticstamina + self.bdy * 5 + self.str * 5
        self.health = min(self.maxhealth, self.health)
        self.mana = min(self.maxmana, self.mana)
        self.stamina = min(self.maxstamina, self.stamina)

    # def _update_incremental_vals(self):
    #     """Increment timer for and update values that need continuous update, but
    #     don't want to do this every frame"""
    #     self.sec_update_timer += time.dt
    #     if self.sec_update_timer >= self.sec_update_rate:
    #         self.sec_update_timer -= self.sec_update_rate
    #         # self._update_sec_phys_attrs() # For now, this is unnecessary
    #         self.update_max_ratings()

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
        if network.peer.is_running() and self.uuid is not None:
            network.uuid_to_char.pop(self.uuid)
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
        if network.peer.is_hosting():
            network.broadcast(network.peer.remote_death, self.uuid)
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


def get_character_states_from_json(pname):
    """Does all the work needed to get inputs to Character from a player in players.json"""
    players_path = os.path.join(os.path.dirname(__file__), "..", "data", "players.json")
    with open(players_path) as players:
        d = json.load(players)[pname]
    pstate_raw = d.get("pstate", {})
    for k, v in pstate_raw.items():
        if hasattr(v, "__iter__"):
            pstate_raw[k] = Vec3(*v)
    basestate_raw = d.get("basestate", {})
    equipment_raw = d.get("equipment", {})
    inventory_raw = d.get("inventory", {})
    skills_raw = d.get("skills", {})
    pstate = PhysicalState(**pstate_raw)
    pstate["cname"] = pname
    basestate = BaseCombatState(**basestate_raw)
    equipment = InitContainer(equipment_raw)
    inventory = InitContainer(inventory_raw)
    skills = SkillState(skills_raw)
    return pstate, basestate, equipment, inventory, skills

def load_character_from_json(pname):
    pstate, basestate, equipment, inventory, skills = get_character_states_from_json(pname)
    return Character(cname=pname, pstate=pstate, base_state=basestate,
                        equipment=equipment, inventory=inventory, skills=skills)