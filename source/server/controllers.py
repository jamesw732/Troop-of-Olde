"""Controllers objects attached to Characters which serve as the bridge between inputs
and the game engine/logic API. Functionality is split between client-side player characters,
client-side NPCs, and server-side Characters.
"""
from ursina import *
import json

from ..base import *
from ..combat import *
from ..gamestate import gs
from ..physics import get_displacement, set_jump_vel, set_gravity_vel
from ..skills import *
from ..states import *


class MobController(Entity):
    """Controller for all server-side characters.

    Handles server-side combat and physics.
    Does not, and will not, handle NPC logic such as pathing, aggression, etc.
    These will instead be handled by an NPCLogic (tentative name) class which reads the
    game state and makes "inputs" to be processed by this class. These "inputs" should be
    compatible with the processed outputs sent by PlayerController.
    """
    def __init__(self, character):
        assert gs.network.peer.is_hosting()
        super().__init__()
        self.character = character
        # Relayed back to client to determine where in history this state was updated, always use most recent
        self.sequence_number = 0

    def update(self):
        char = self.character
        if char.health <= 0:
            char.die()
        if char.target and not char.target.alive:
            char.target = None
            char.combat_timer = 0
        if char.target and char.target.alive and char.in_combat:
            mh_slot = slot_to_ind["mh"]
            mh = char.equipment[mh_slot]
            if tick_mh(char) and char.get_target_hittable(mh):
                hit, msg = attempt_attack(char, char.target, "mh")
                mh_skill = get_wpn_style(mh)
                if hit and check_raise_skill(char, mh_skill):
                    raise_skill(char, mh_skill)
                    connection = gs.network.uuid_to_connection[char.uuid]
                    gs.network.peer.remote_update_skill(connection, mh_skill, char.skills[mh_skill])
                conn = gs.network.uuid_to_connection.get(char.uuid, None)
                if conn is not None:
                    gs.network.peer.remote_print(conn, msg)
                    # Should add some sort of check to make sure this isn't happening too often
                    gs.network.broadcast_cbstate_update(char.target)
            # See if we should progress offhand timer too
            # (if has skill dw):
            mh_is_1h = not (mh is not None
                            and mh.type == "weapon"
                            and mh.info.get("style", "")[:2] == "2h")
            oh_slot = slot_to_ind["oh"]
            offhand = char.equipment[oh_slot]
            # basically just check if not wearing a shield
            dual_wielding =  mh_is_1h and (offhand is None or offhand.type == "weapon")
            if dual_wielding and tick_oh(char)\
            and char.get_target_hittable(char.equipment[oh_slot]):
                hit, msg = attempt_attack(char, char.target, "oh")
                oh_skill = get_wpn_style(char.equipment[oh_slot])
                if hit and check_raise_skill(char, oh_skill):
                    raise_skill(char, oh_skill)
                    connection = gs.network.uuid_to_connection[char.uuid]
                    gs.network.peer.remote_update_skill(connection, oh_skill, char.skills[oh_skill])
                conn = gs.network.uuid_to_connection.get(char.uuid, None)
                if conn is not None:
                    gs.network.peer.remote_print(conn, msg)
                    gs.network.broadcast_cbstate_update(char.target)
        else:
            char.mh_combat_timer = 0
            char.oh_combat_timer = 0
        if char.get_on_gcd():
            char.tick_gcd()
        elif char.next_power is not None and not char.next_power.on_cooldown:
            tgt = char.next_power.get_target()
            char.next_power.use(tgt)

    @every(PHYSICS_UPDATE_RATE)
    def tick_physics(self):
        # Assumed that keyboard component gets set by a client
        set_gravity_vel(self.character)
        set_jump_vel(self.character)
        displacement = get_displacement(self.character)
        if displacement == Vec3(0, 0, 0):
            return
        self.character.position += displacement
        self.character.velocity_components["keyboard"] = Vec3(0, 0, 0)
        for conn in gs.network.peer.get_connections():
            if conn not in gs.network.connection_to_char:
                continue
            if self.character is gs.network.connection_to_char[conn]:
                gs.network.peer.update_pc_lerp_attrs(conn, self.sequence_number, self.character.position,
                                                     self.character.rotation_y)
            else:
                gs.network.peer.update_npc_lerp_attrs(conn, self.character.uuid, self.character.position,
                                                      self.character.rotation_y)


class NameLabel(Text):
    def __init__(self, char):
        """Creates a namelabel above a character
        
        Todo: Change parent to character"""
        super().__init__(char.cname, parent=scene, scale=10, origin=(0, 0, 0),
                         position=char.position + Vec3(0, char.height + 1, 0))
        self.char = char

    def adjust_rotation(self):
        """Aim the namelabel at the player with the right direction"""
        if gs.pc:
            direction = gs.pc.position - camera.world_position
            self.look_at(direction + self.world_position)
            self.rotation_z = 0

    def adjust_position(self):
        """Position the namelabel above the character"""
        self.position = self.char.position + Vec3(0, self.char.height + 1, 0)