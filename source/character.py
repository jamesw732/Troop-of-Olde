"""Represents the physical player/npc entities in game. Engine-relevant character
logic."""
from ursina import *
import numpy

from .mob import *

# Update this to expand CharacterState
char_state_attrs = {
    "uuid": int,
    "name": str,
    "position": Vec3,
    "rotation": Vec3,
    "scale": Vec3,
    "speed": float,
    "type": str
}

# kwargs that aren't necessary to specify at all, can exist as Nones
optional_char_kwargs = ["uuid", "controller", "type", "namelabel"]

class Character(Entity):
    def __init__(self, *args, name="Player", speed=10, mob=None, state=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.name = name
        if mob:
            self.mob = mob
        else:
            self.mob = Mob(character=self)

        self.height = self.scale_y

        self.speed = speed
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

        for kwarg in optional_char_kwargs:
            if kwarg in kwargs:
                setattr(self, kwarg, kwargs[kwarg])
            else:
                setattr(self, kwarg, None)
        if state:
            self.apply_state(state)

    def update(self):
        self.handle_movement()

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
    
    def get_state(self):
        return CharacterState(char=self)
    
    def apply_state(self, state):
        self.uuid = state.uuid
        self.name = state.name
        self.position = state.position
        self.rotation = state.rotation
        self.scale = state.scale
        self.speed = state.speed


class CharacterState:
    def __init__(self, **kwargs):
        if "char" in kwargs:
            char = kwargs["char"]
            for attr in char_state_attrs:
                if hasattr(char, attr):
                    val = getattr(char, attr)
                    setattr(self, attr, val)
        else:
            for attr in char_state_attrs:
                if attr in kwargs:
                    setattr(self, attr, kwargs[attr])


def serialize(writer, state):
    for attr in char_state_attrs:
        writer.write(attr)
        writer.write(getattr(state, attr))

def deserialize(reader):
    state = CharacterState()
    while reader.iter.getRemainingSize() > 0:
        attr = reader.read(str)
        val = reader.read(char_state_attrs[attr])
        setattr(state, attr, val)
    return state