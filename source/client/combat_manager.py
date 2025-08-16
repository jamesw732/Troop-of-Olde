from ursina import *

from ..network import network


class CombatManager(Entity):
    """Provides a shallow combat API to input handler/network."""
    def __init__(self, animation_system):
        super().__init__()
        self.pc = None
        self.animation_system = animation_system

    def input_set_target(self, target):
        """Set player character's target locally and send request to server.

        target: Character"""
        self.pc.set_target(target)
        network.peer.request_set_target(network.server_connection, target.uuid)

    def input_toggle_combat(self):
        network.peer.request_toggle_combat(network.server_connection)

    def char_set_target(self, char, tgt):
        char.target = tgt

    def char_set_in_combat(self, char, toggle):
        char.in_combat = toggle
        if toggle:
            self.animation_system.char_enter_combat(char)
        else:
            self.animation_system.char_exit_combat(char)
