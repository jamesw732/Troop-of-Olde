from ursina import *

from .. import *


class PlayerController(Entity):
    """Singleton class that processes movement inputs to update character position/rotation.

    Does not update these attributes directly, instead interfaces to lerp_system.LerpState
    to update target attributes and smoothly interpolate each frame. Movement uses client-side
    prediction with correction for server updates."""
    def __init__(self, character, lerp_state):
        super().__init__()
        self.character = character
        self.lerp_state = lerp_state
        # The sequence number of movement inputs
        self.sequence_number = 0
        # The most recent received sequence number
        self.recv_sequence_number = 0
        # Remember the position/rotation when we sent sequence numbers
        self.sn_to_pos = {}
        self.sn_to_rot = {}
        # Components to build target rotation
        self.keyboard_y_rotation = 0
        self.mouse_y_rotation = 0
        self.rot_offset = 0 # Predicted difference from server's rotation

    def update_keyboard_inputs(self, fwdback, strafe, rightleft_rot):
        """Update local keyboard velocity and target rotation, send
        request for server to do the same

        Performed at the end of the frame, and relies on handle_mouse_rotation
        to correctly update target_rot according to mouse rotation."""
        # Local updates
        char = self.character
        # Keyboard velocity
        char_speed = get_speed_modifier(char.speed)
        kb_vel = (char.right * strafe + char.forward * fwdback).normalized() * 10 * char_speed
        char.velocity_components["keyboard"] = kb_vel
        # Keyboard rotation
        self.keyboard_y_rotation = rightleft_rot
        # Server update
        conn = network.server_connection
        keyboard_direction = Vec2(strafe, fwdback)
        network.peer.request_move(conn, self.sequence_number, keyboard_direction,
                                     rightleft_rot, self.mouse_y_rotation)

    @every(PHYSICS_UPDATE_RATE)
    def tick_movement(self):
        """Update target position/rotation on a fixed interval"""
        char = self.character
        if char is None:
            return
        # Client-side prediction for movement/rotation
        set_gravity_vel(char)
        displacement = get_displacement(char)
        # Update target position, lag behind by one timestep
        target_pos = char.position + displacement
        input_rot = self.keyboard_y_rotation * 100 * PHYSICS_UPDATE_RATE + self.mouse_y_rotation
        target_rot = char.rotation_y + input_rot + self.rot_offset
        self.lerp_state.update_targets(target_pos, target_rot)
        # Just some necessary bookkeeping things
        char.displacement_components["server_offset"] = Vec3(0, 0, 0)
        self.rot_offset = 0
        self.mouse_y_rotation = 0
        self.sequence_number += 1

    def update_mouse_y_rotation(self, amt):
        """Updates self.mouse_y_rotation with rotation obtained from mouse movement

        Does not update the character's rotation directly, instead this
        quantity is stored cumulatively over one physics tick period, then
        used to determine the next target_rot."""
        self.mouse_y_rotation += amt

    def do_jump(self):
        if self.character is None:
            return
        char_start_jump(self.character)
        network.peer.request_jump(network.server_connection)

    def update_server_offsets(self, sequence_number, pos, rot):
        """Updates diff between server's pos/rot and client's pos/rot"""
        if sequence_number > self.recv_sequence_number:
            self.recv_sequence_number = sequence_number
            for num in self.sn_to_pos.copy():
                if num < sequence_number:
                    self.sn_to_pos.pop(num)
                    self.sn_to_rot.pop(num)
        else:
            # Always take the most recent sequence number
            # Alternatively, reject completely if it's old
            sequence_number = self.recv_sequence_number
        # Compute the offset amt for position
        # sn_to_pos is missing sequence_number on startup
        predicted_pos = self.sn_to_pos.get(sequence_number, pos)
        pos_offset = pos - predicted_pos
        self.character.displacement_components["server_offset"] = pos_offset
        # Compute the offset amt for rotation
        rot = rot % 360
        predicted_rot = self.sn_to_rot.get(sequence_number, rot)
        rot_offset = rot - predicted_rot
        self.rot_offset = rot_offset


class NPCController:
    """Provides an interface for updating NPC position and rotation.

    Does not update these attributes directly, instead interfaces to lerp_system.LerpState
    to update "target" attributes and interpolate smoothly between frames."""
    def __init__(self, character, lerp_state):
        self.character = character
        self.lerp_state = lerp_state
        self.prev_recv_t = 0

    def update_lerp_targets(self, time_received, pos, rot):
        """Updates targets for self.lerp_state

        We don't have control over when we receive server updates,
        so make lerp interval time-dependent.
        """
        lerp_time = time_received - self.prev_recv_t
        self.prev_recv_t = time_received
        self.lerp_state.update_targets(pos, rot, lerp_time)
