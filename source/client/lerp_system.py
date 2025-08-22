from ursina import *

from ..physics import PHYSICS_UPDATE_RATE


class LerpSystem(Entity):
    def __init__(self, gamestate):
        super().__init__()
        self.uuid_to_lerp = gamestate.uuid_to_lerp

    def make_lerp_state(self, character):
        self.uuid_to_lerp[character.uuid] = LerpState(character)

    def update(self):
        for lerp_state in self.uuid_to_lerp.values():
            lerp_state.lerp(time.dt)


class LerpState:
    def __init__(self, character):
        self.character = character
        # Previous positions/rotations to lerp from
        self.prev_pos = self.character.position
        self.prev_rot = self.character.rotation_y
        # Current targets to lerp to
        self.target_pos = self.character.position
        self.target_rot = self.character.rotation_y
        self.lerp_timer = 0
        self.lerp_time = PHYSICS_UPDATE_RATE

    def lerp(self, dt):
        self.lerp_timer += dt
        pct = min(1, self.lerp_timer / self.lerp_time)
        self.character.position = lerp(self.prev_pos, self.target_pos, pct)
        self.character.rotation_y = lerp_angle(self.prev_rot, self.target_rot, pct)
        # Fix character rotation
        self.character.rotation_x = 0
        self.character.rotation_z = 0

    def update_targets(self, pos, rot, time=PHYSICS_UPDATE_RATE):
        """Updates target position/rotation and resets lerp timer"""
        self.character.position = self.prev_pos
        self.character.rotation_y = self.prev_rot
        self.prev_pos = self.target_pos
        self.target_pos = pos
        self.prev_rot = self.target_rot
        self.target_rot = rot
        self.lerp_timer = 0
        self.lerp_time = time
