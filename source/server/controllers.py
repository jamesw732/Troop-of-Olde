"""Controllers objects attached to Characters which serve as the bridge between inputs
and the game engine/logic API. Functionality is split between client-side player characters,
client-side NPCs, and server-side Characters.
"""
from ursina import *
import json

from .. import *


class MobController(Entity):
    """Controller for all server-side characters.

    Handles server-side combat and physics.
    Does not, and will not, handle NPC logic such as pathing, aggression, etc.
    These will instead be handled by an NPCLogic (tentative name) class which reads the
    game state and makes "inputs" to be processed by this class. These "inputs" should be
    compatible with the processed outputs sent by PlayerController.
    """
    def __init__(self, character, on_destroy=lambda: None):
        assert network.peer.is_hosting()
        super().__init__()
        self.character = character
        self.on_destroy=on_destroy
        # Relayed back to client to determine where in history this state was updated, always use most recent
        self.sequence_number = 0
        self.moving = False

    def update(self):
        char = self.character
        # Death handling
        if char.health <= 0:
            self.kill()
            return
        # Queued power handling
        if char.get_on_gcd():
            char.tick_gcd()
        # Need to update 

    def use_power(self, power):
        tgt = power.get_target(self.character)
        if tgt is None:
            return
        if self.character.energy < power.cost:
            return
        power.use(self.character, tgt)
        # Upon using a power, need to update energy to clients
        network.broadcast_cbstate_update(self.character)

    @every(PHYSICS_UPDATE_RATE)
    def tick_physics(self):
        # Assumed that keyboard component gets set by a client
        set_gravity_vel(self.character)
        set_jump_vel(self.character)
        displacement = get_displacement(self.character)
        self.character.position += displacement
        self.character.velocity_components["keyboard"] = Vec3(0, 0, 0)
        # This executes client-side movement/rotation correct, to test movement without this
        # overhead, comment the rest of this function.
        for conn, uuid in network.connection_to_uuid.items():
            if self.character.uuid == uuid:
                network.peer.update_pc_lerp_attrs(conn, self.sequence_number, self.character.position,
                                                     self.character.rotation_y)
            else:
                network.peer.update_npc_lerp_attrs(conn, self.character.uuid, self.character.position,
                                                      self.character.rotation_y)

    def handle_movement_inputs(self, sequence_number, kb_direction, kb_y_rotation, mouse_y_rotation):
        """Processes movement inputs from a client"""
        char = self.character
        char_speed = get_speed_modifier(char.speed)
        vel = (char.right * kb_direction[0] + char.forward * kb_direction[1]).normalized() * 10 * char_speed
        if "keyboard" not in char.velocity_components:
            char.velocity_components["keyboard"] = vel
        char.velocity_components["keyboard"] += vel
        # char_rotation = Vec3(0, kb_y_rotation[1] * 100 * math.cos(math.radians(self.focus.rotation_x)), 0)
        y_rotation = kb_y_rotation * 100 * PHYSICS_UPDATE_RATE + mouse_y_rotation
        char.rotation_y += y_rotation
        # Will send back the most recently received sequence number to match the predicted state.
        # If packets arrive out of order, we want to update based on last sequence number
        if sequence_number > self.sequence_number:
            self.sequence_number = sequence_number
        # Update client's NPC animation
        if kb_direction != Vec2(0, 0) and self.moving == False:
            self.moving = True
            for conn, uuid in network.connection_to_uuid.items():
                if char.uuid != uuid:
                    network.peer.remote_start_run_anim(conn, char.uuid)
        elif kb_direction == Vec2(0, 0) and self.moving == True:
            self.moving = False
            for conn, uuid in network.connection_to_uuid.items():
                if char.uuid != uuid:
                    network.peer.remote_end_run_anim(conn, char.uuid)

    def kill(self):
        self.character.alive = False
        uuid = self.character.uuid
        destroy(self.character)
        destroy(self)
        network.broadcast(network.peer.remote_kill, uuid)