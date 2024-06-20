"""Represents the physical player/npc entities in game. Engine-relevant character
logic."""
from ursina import *
import numpy

from .combat import *
from .networking.base import *
from .world_defns import *

# Update this to expand CharacterState
char_state_attrs = {
    "uuid": int,
    "name": str,
    "type": str,
    "speed": float,
    "model": str,
    "scale": Vec3,
    "origin": Vec3,
    "collider": str,
    "position": Vec3,
    "rotation": Vec3,
    "color": str,
}


class Character(Entity):
    def __init__(self, *args, name="Player", speed=10.0,  uuid=None, type="player",
                state=None, **kwargs):
        # Engine-relevant vars
        super().__init__(*args, **kwargs)
        if state:
            self.apply_state(state)
        else:
            self.uuid = uuid
            self.type = type
            self.name = name
            self.speed = speed

        self.height = self.scale_y
        self.namelabel = self.make_namelabel()

        self.velocity = Vec3(0, 0, 0)
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

    def update(self):
        self.handle_movement()
        self.adjust_namelabel()

        if self.target and self.target.alive and self.in_combat:
            self.progress_combat_timer()
        else:
            self.combat_timer = 0
            if self.target and not self.target.alive:
                self.target = None

        if self.health <= 0:
            if is_main_client():
                self.die()

    def handle_movement(self):
        """Combines all movement inputs into one velocity vector, then handles collision and grounding and moves in just one call."""
        # Get the character-only velocity items
        self.set_gravity_vel()
        self.set_jump_vel()
        # Combine them all, there will likely be others besides gravity and jumping
        self.velocity = sum(list(self.velocity_components.values()))
        # If components was empty, we get an int, so convert to zero vector
        if type(self.velocity) is int:
            self.velocity = Vec3(0, 0, 0)

        self.handle_grounding()
        self.handle_collision()
        self.handle_upward_collision()

        self.position += self.velocity * time.dt

    def set_gravity_vel(self):
        """If not grounded and not jumping, subtract y (linear in time) from velocity vector"""
        if not self.grounded and not self.jumping:
            self.grav -= 1
        elif self.grounded:
            self.grav = 0
        self.velocity_components["gravity"] = Vec3(0, self.grav, 0)

    def set_jump_vel(self):
        """If jumping, add some y to velocity vector"""
        if self.jumping:
            speed = self.max_jump_height / self.max_jump_time
            if self.rem_jump_height - speed * time.dt <= 0:
                speed = self.rem_jump_height / self.max_jump_time
                self.cancel_jump()
            else:
                self.rem_jump_height -= speed * time.dt
            jump_vel = Vec3(0, speed, 0)
        else:
            jump_vel = Vec3(0, 0, 0)
        self.velocity_components["jump"] = jump_vel

    def handle_grounding(self):
        """Handles logic for whether the character is grounded or not.
        Doesn't move the character at all, just handles logic for whether or not the player is grounded"""
        if self.velocity[1] > 0:
            self.grounded = False
        elif self.velocity[1] == 0:
            ground = raycast(self.position, direction=(0, -1, 0), distance=0.01, ignore=self.ignore_traverse)
            self.grounded = ground.hit
        else:
            ground = raycast(self.position, direction=(0, -1, 0), distance=abs(self.velocity[1] * time.dt), ignore=self.ignore_traverse)
            if ground.hit:
                self.grounded = True

    def handle_collision(self):
        """Handles most of the collision logic."""
        dist = distance((0, 0, 0), self.velocity) * time.dt
        collision_check = raycast(self.position, direction=self.velocity, distance=dist, ignore=self.ignore_traverse)
        if collision_check.hit:
            normal = collision_check.world_normal
            if numpy.dot(normal, self.velocity) < 0:
                # Note this is different from character speed if multiple velocity components
                speed = distance(Vec3.zero, self.velocity)
                # Project velocity onto normal of colliding entity
                # This is not correct.
                self.velocity = self.velocity - (numpy.dot(normal, self.velocity)) * normal
                # Match old speed
                self.velocity = self.velocity.normalized() * speed
                # Make sure new velocity doesn't pass through any entities, ie concave case.
                # For now, we just don't move at all, but eventually can improve this.
                dist2 = distance((0, 0, 0), self.velocity) * time.dt
                ray = raycast(self.position, direction=self.velocity, distance=dist2, ignore=self.ignore_traverse)
                if ray.hit:
                    self.velocity = Vec3(0, 0, 0)

    def handle_upward_collision(self):
        """Blocks upward movement when jumping into a ceiling"""
        if self.velocity[1] < 0:
            return
        # Cast ray from top of model, rather than bottom like in handle_collision
        pos = self.position + Vec3(0, self.height, 0)
        ceiling = raycast(pos, direction=(0, 1, 0), distance=self.velocity[1] * time.dt, ignore=self.ignore_traverse)
        if ceiling.hit:
            self.velocity[1] = 0

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

    def make_namelabel(self):
        return Text(self.name, parent=scene, scale=10, origin=(0, 0, 0),
                    position=self.position + Vec3(0, self.height + 1, 0))

    def rotate_namelabel(self, direction):
        if self.namelabel:
            self.namelabel.look_at(direction + self.namelabel.world_position)
            self.namelabel.rotation_z = 0

    def adjust_namelabel(self):
        if self.namelabel:
            self.namelabel.position = self.position + Vec3(0, self.height + 1, 0)

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
        chars.remove(self)
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
    
    def get_state(self):
        return CharacterState(char=self)
    
    def apply_state(self, state):
        for attr in char_state_attrs:
            if hasattr(state, attr):
                val = getattr(state, attr)
                # Ursina is smart about assigning model/collider, but not color
                if attr == "color":
                    val = color.colors[val]
                setattr(self, attr, val)


class CharacterState:
    """This class is intentionally opaque to save from writing the same code
    in multiple places and needing to update several functions every time I want
    to expand this class. The entire purpose of this class is to abbreviate Characters,
    and make them sendable over the network. To see exactly how Characters are
    abbreviated, look at char_state_attrs at the top of this file."""
    def __init__(self, char=None, **kwargs):
        # If a character was passed, take its attributes
        if char is not None:
            for attr in char_state_attrs:
                if hasattr(char, attr):
                    val = getattr(char, attr)
                    # Only include attrs intentionally set
                    if val is not None:
                        if attr in ["collider", "color", "model"]:
                            # Ursina objects exist in CharacterState as string names
                            val = val.name
                        setattr(self, attr, val)
        # Otherwise, read the attributes straight off
        else:
            for attr in char_state_attrs:
                if attr in kwargs:
                    setattr(self, attr, kwargs[attr])

    def __str__(self):
        return str({attr: getattr(self, attr)
                for attr in char_state_attrs if hasattr(self, attr)})


def serialize_character_state(writer, state):
    for attr in char_state_attrs:
        if hasattr(state, attr):
            val = getattr(state, attr)
            if val is not None:
                writer.write(attr)
                writer.write(val)

def deserialize_character_state(reader):
    state = CharacterState()
    while reader.iter.getRemainingSize() > 0:
        attr = reader.read(str)
        val = reader.read(char_state_attrs[attr])
        setattr(state, attr, val)
    return state