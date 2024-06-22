"""Represents the physical player/npc entities in game. Engine-relevant character
logic."""
from ursina import *

from .combat import attempt_melee_hit
from .networking.base import *
from .physics import handle_movement
from .gamestate import *


class Character(Entity):
    def __init__(self, *args, name="Player",  uuid=None, type="player",
                 pstate=None, cbstate = None, **kwargs):
        """ *args and **kwargs are just passed directly into Entity().

        name: name of character, str
        uuid: unique id, only relevant if on network. Used to encode which player you're talking about online.
        type: "player" or "npc"
        pstate: PhysicalState; defines client-authoritative attrs
        cbstate: CombatState; defines host-authoritative attrs"""
        super().__init__(*args, **kwargs)
        self.type = type
        self.name = name
        self.uuid = uuid
        self.controller = None

        self.sec_update_rate = 1
        self.sec_update_timer = 0

        self._init_phys_attrs()
        self._init_cb_attrs()

        if pstate:
            self.apply_physical_state(pstate)
        if cbstate:
            self.apply_combat_state(cbstate)

        self._init_lerp_attrs()

    def _init_phys_attrs(self):
        """Initialize base physical attributes. These are likely to change."""
        self.model = "cube"
        self.scale = Vec3(1, 2, 1)
        self.origin = Vec3(0, -0.5, 0)
        self.collider="box"
        self.color = color.orange

        self.jumping = False
        self.grounded = False
        self.grav = 0
        self.velocity_components = {}

        self.height = self.scale_y
        self.max_jump_height = self.height * 1.5
        self.rem_jump_height = self.max_jump_height
        self.max_jump_time = 0.3
        self.rem_jump_time = self.max_jump_time

        self.traverse_target = scene
        self.ignore_traverse = [self]

        self.namelabel = NameLabel(self)

    def _init_cb_attrs(self):
        """Initialize base combat attributes. These will definitely change."""
        self.maxhealth = 100
        self.health = self.maxhealth
        self.maxmana = 100
        self.mana = self.maxmana
        self.maxstamina = 100
        self.stamina = self.maxstamina

        self.bdy = 0
        self.str = 0
        self.dex = 0
        self.ref = 0
        self.agi = 0
        self.int = 0

        self.haste = 0
        self.speed = 10

        # self.maxspellshield = 0
        # self.spellshield = self.maxspellshield
        # self.rmagic = 0
        # self.rphys = 0
        # self.rfire = 0
        # self.rcold = 0
        # self.relec = 0

        self.max_combat_timer = 0.1
        self.combat_timer = 0
        self.attackrange = 10
        self.alive = True
        self.in_combat = False
        self.target = None

    def _init_lerp_attrs(self):
        """Initialize lerp logic"""
        self.prev_state = None
        self.new_state = self.get_physical_state()
        self.prev_lerp_recv = 0
        self.lerping = False
        self.lerp_rate = 0
        self.lerp_timer = 0.2

    def _update_sec_phys_attrs(self):
        """Adjust secondary physical attributes to state changes"""
        self.height = self.scale_y
        self.max_jump_height = self.height * 1.5
        self.rem_jump_height = self.max_jump_height
        self.max_jump_time = 0.3
        self.rem_jump_time = self.max_jump_time

    def _update_sec_cb_attrs(self):
        """Adjust secondary combat attributes to state changes"""
        self.maxhealth = 100 + self.bdy * 10
        self.maxmana = 100 + self.int * 10
        self.maxstamina = 100 + self.bdy * 5 + self.str * 5

    def _update_secondary_vals(self):
        """Increment timer and update secondary values"""
        self.sec_update_timer += time.dt
        if self.sec_update_timer >= self.sec_update_rate:
            self.sec_update_timer -= self.sec_update_rate
            self._update_sec_phys_attrs()
            self._update_sec_cb_attrs()

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
                self.apply_physical_state(self.new_state)
            # Otherwise, LERP normally
            else:
                self.position = lerp(self.prev_state.position,
                                     self.new_state.position,
                                     self.lerp_timer / self.lerp_rate)
                self.rotation = lerp(self.prev_state.rotation,
                                     self.new_state.rotation,
                                     self.lerp_timer / self.lerp_rate)
        # Namelabel Handling
        self.namelabel.fix_position()
        self.namelabel.fix_rotation()
        # Combat Handling
        if self.target and self.target.alive and self.in_combat:
                self.progress_combat_timer()
        else:
            self.combat_timer = 0
            if self.target and not self.target.alive:
                self.target = None
        # Death Handling
        if self.health <= 0:
            # Wait for server to tell character to die
            if is_main_client():
                self.die()

    def start_jump(self):
        """Set self.jumping to be true if not grounded"""
        if self.grounded:
            self.jumping = True

    def cancel_jump(self):
        """Reset self.jumping, remaining jump height"""
        self.jumping = False
        self.rem_jump_height = self.max_jump_height

    def progress_combat_timer(self):
        """Increment combat timer by dt. If past max, attempt a melee hit."""
        # Add time.dt to combat timer, if flows over max, attempt hit and subtract max
        self.combat_timer += time.dt
        if self.combat_timer > self.max_combat_timer:
            self.combat_timer -= self.max_combat_timer
            if self.get_target_hittable():
                if is_main_client():
                    attempt_melee_hit(self, self.target)
                else:
                    # Host-authoritative, so we need to ask the host to compute the hit
                    network.peer.remote_attempt_melee_hit(
                        network.peer.get_connections()[0],
                        self.uuid, self.target.uuid)

    def get_target_hittable(self):
        """Returns whether self.target is able to be hit, ie in LoS and within attack range"""
        in_range = distance(self, self.target) < self.attackrange
        return in_range and self.get_tgt_los(self.target)

    def get_tgt_los(self, target):
        """Returns whether the target is in line of sight"""
        dist = distance(self, target)
        src_pos = self.position + Vec3(0, 0.8 * self.scale_y, 0)
        tgt_pos = target.position + Vec3(0, 0.8 * target.scale_y, 0)
        dir = tgt_pos - src_pos
        line_of_sight = raycast(src_pos, direction=dir, distance=dist,
                                ignore=[entity for entity in scene.entities if type(entity) is Character])
        return len(line_of_sight.entities) == 0

    def increase_health(self, amt):
        """Function to be used whenever increasing character's health"""
        self.health = min(self.maxhealth, self.health + amt)

    def reduce_health(self, amt):
        """Function to be used whenever decreasing character's health"""
        self.health -= amt

    def on_destroy(self):
        """Upon being destroyed, remove all references to objects attached to this character"""
        if network.peer.is_running():
            network.uuid_to_char.pop(self.uuid)
        gs.chars.remove(self)
        if self.controller:
            destroy(self.controller)
            del self.controller.character
            del self.controller
        destroy(self.namelabel)
        del self.namelabel
        del self.ignore_traverse

    def die(self):
        """Essentially just destroy self and make sure the rest of the network knows if host."""
        print(f"{self.name} perishes.")
        self.alive = False
        if network.peer.is_hosting():
            broadcast(network.peer.remote_death, self.uuid)
        destroy(self)
    
    def get_physical_state(self):
        """Computes the current state of Character's client-authoritative attributes"""
        return PhysicalState(char=self)
    
    def apply_physical_state(self, state):
        """Applies state of client-authoritative attributes.
        Should really only be called by update_lerp_state"""
        for attr in phys_state_attrs:
            if hasattr(state, attr):
                val = getattr(state, attr)
                # Ursina is smart about assigning model/collider, but not color
                if attr == "color":
                    val = color.colors[val]
                elif attr == "target":
                    # target is a uuid, not a char
                    if val in network.uuid_to_char:
                        val = network.uuid_to_char[val]
                    else:
                        continue
                setattr(self, attr, val)
        # Overwriting model causes origin to break, for some reason
        if hasattr(state, "model"):
            self.origin = Vec3(0, -0.5, 0)

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
            self.apply_physical_state(self.prev_state)

    def get_combat_state(self):
        """Computes the current state of Character's host-authoritative attributes"""
        return CombatState(char=self)

    def apply_combat_state(self, state):
        """Applies state of host-authoritative attributes"""
        for attr in combat_state_attrs:
            if hasattr(state, attr):
                val = getattr(state, attr)
                setattr(self, attr, val)


class NameLabel(Text):
    def __init__(self, char):
        """Creates a namelabel above a character"""
        super().__init__(char.name, parent=scene, scale=10, origin=(0, 0, 0),
                         position=char.position + Vec3(0, char.height + 1, 0))
        self.char = char

    def fix_rotation(self):
        """Aim the namelabel at the player with the right direction"""
        if gs.pc:
            direction = gs.pc.character.position - camera.world_position
            self.look_at(direction + self.world_position)
            self.rotation_z = 0

    def fix_position(self):
        """Position the namelabel above the character"""
        self.position = self.char.position + Vec3(0, self.char.height + 1, 0)


