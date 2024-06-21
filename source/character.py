"""Represents the physical player/npc entities in game. Engine-relevant character
logic."""
from ursina import *
import numpy

from .combat import attempt_melee_hit
from .networking.base import *
from .physics import handle_movement, PhysicalState, phys_state_attrs
from .gamestate import *


class Character(Entity):
    def __init__(self, *args, name="Player", speed=10.0,  uuid=None,
                 type="player", state=None, **kwargs):
        # Engine-relevant vars
        super().__init__(*args, **kwargs)
        if state:
            self.apply_physical_state(state)
        else:
            self.uuid = uuid
            self.type = type
            self.name = name
            self.speed = speed

        self.height = self.scale_y
        self.namelabel = NameLabel(self)

        self.velocity_components = {}

        self.jumping = False
        self.grounded = False
        self.grav = 0

        self.max_jump_height = self.height * 1.5
        self.rem_jump_height = self.max_jump_height
        self.max_jump_time = 0.3
        self.rem_jump_time = self.max_jump_time

        self.traverse_target = scene
        self.ignore_traverse = [self]

        self.controller = None

        # Non-engine-relevant vars
        self.maxhealth = 100
        self.health = self.maxhealth
        self.in_combat = False
        self.target = None
        self.max_combat_timer = 0.1
        self.combat_timer = 0
        self.attackrange = 10
        self.alive = True

        # LERP vars
        self.prev_state = None
        self.new_state = self.get_physical_state()
        self.prev_lerp_recv = 0
        self.lerping = False
        self.lerp_rate = 0
        self.lerp_timer = 0.2

    def update(self):
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
        """Set self.jumping"""
        if self.grounded:
            self.jumping = True

    def cancel_jump(self):
        """Reset self.jumping, remaining jump height"""
        self.jumping = False
        self.rem_jump_height = self.max_jump_height

    def get_tgt_los(self, target):
        """Returns whether the target is in line of sight"""
        dist = distance(self, target)
        src_pos = self.position + Vec3(0, 0.8 * self.scale_y, 0)
        tgt_pos = target.position + Vec3(0, 0.8 * target.scale_y, 0)
        dir = tgt_pos - src_pos
        line_of_sight = raycast(src_pos, direction=dir, distance=dist,
                                ignore=[entity for entity in scene.entities if type(entity) is Character])
        return len(line_of_sight.entities) == 0

    def progress_combat_timer(self):
        # Add time.dt to combat timer, if flows over max, attempt hit and subtract max
        self.combat_timer += time.dt
        if self.combat_timer > self.max_combat_timer:
            self.combat_timer -= self.max_combat_timer
            if self.get_target_hittable():
                if is_main_client():
                    attempt_melee_hit(self, self.target)
                else:
                    network.peer.remote_attempt_melee_hit(
                        network.peer.get_connections()[0],
                        self.uuid, self.target.uuid)

    def get_target_hittable(self):
        in_range = distance(self, self.target) < self.attackrange
        return in_range and self.get_tgt_los(self.target)

    def increase_health(self, amt):
        self.health += amt

    def reduce_health(self, amt):
        self.health -= amt

    def on_destroy(self):
        """Remove all references to objects attached to this character"""
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
        print(f"{self.name} perishes.")
        self.alive = False
        if network.peer.is_hosting():
            broadcast(network.peer.remote_death, self.uuid)
        destroy(self)
    
    def get_physical_state(self):
        return PhysicalState(char=self)
    
    def apply_physical_state(self, state):
        for attr in phys_state_attrs:
            if hasattr(state, attr):
                val = getattr(state, attr)
                # Ursina is smart about assigning model/collider, but not color
                if attr == "color":
                    val = color.colors[val]
                setattr(self, attr, val)

    def update_lerp_state(self, state, time):
        self.prev_state = self.new_state
        self.new_state = state
        if self.prev_state:
            self.lerping = True
            self.lerp_rate = time - self.prev_lerp_recv
            self.prev_lerp_recv = time
            self.lerp_timer = 0
            # Apply old state to ensure synchronization and update non-lerp attrs
            self.apply_physical_state(self.prev_state)


class NameLabel(Text):
    def __init__(self, char):
        super().__init__(char.name, parent=scene, scale=10, origin=(0, 0, 0),
                         position=char.position + Vec3(0, char.height + 1, 0))
        self.char = char

    def fix_rotation(self):
        if gs.pc:
            direction = gs.pc.character.position - camera.world_position
            self.look_at(direction + self.world_position)
            self.rotation_z = 0

    def fix_position(self):
        self.position = self.char.position + Vec3(0, self.char.height + 1, 0)


