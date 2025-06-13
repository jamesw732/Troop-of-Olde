from ursina import *
import os
import json

from .effect import Effect
from .gamestate import gs

power_path = os.path.join(os.path.dirname(__file__), "..", "data", "powers.json")
with open(power_path) as power_json:
    id_to_power_data = json.load(power_json)


class Power(Entity):
    def __init__(self, power_id):
        super().__init__()
        self.power_id = power_id
        power_data = id_to_power_data[str(power_id)]
        for k, v in power_data.items():
            setattr(self, k, v)

        # set to True immediately after use
        self.on_cooldown = False
        # ticks up if self.on_cooldown
        self.timer = 0

        self.ui_elmnt = None

    def handle_power_input(self):
        """Handles client's input to use a power"""
        assert not gs.network.peer.is_hosting()
        tgt = self.get_target(gs.pc)
        if gs.pc.get_on_gcd():
            if gs.pc.next_power is self:
                # Attempted to queue an already queued power, just remove it
                gs.pc.next_power = None
            else:
                # Queued powers are currently handled by PlayerController
                self.queue(gs.pc)
        else:
            self.client_use_power()
            gs.network.peer.request_use_power(gs.network.server_connection, self.power_id)

    def get_target(self, char):
        """Returns the correct target based on the type of power and character's target

        Currently just returns the character's target, will be more complicated eventually"""
        return char.target

    def queue(self, char):
        char.next_power = self

    def client_use_power(self):
        """Does the client-side things involved with using a power.

        Currently, just sets the GCD. Eventually, will also invoke animation."""
        assert not gs.network.peer.is_hosting()
        char = gs.pc
        tgt = char.target
        if char.get_on_gcd():
            return
        if tgt is None:
            return
        self.set_char_gcd(gs.pc)
        char.next_power = None
        gs.ui.actionbar.start_gcd_animation()

    def set_char_gcd(self, char):
        char.gcd = self.gcd_duration
        char.gcd_timer = 0

    def use(self, char, tgt):
        """Does the server-side things involved with using a power.
        Used by char on their active target."""
        assert gs.network.peer.is_hosting()
        if tgt is None:
            return
        self.set_char_gcd(char)
        char.next_power = None

        effect = self.get_effect(char, tgt)
        # Would like some better logic here eventually, like auto-targetting based on beneficial
        # or harmful
        effect.attempt_apply()

    def get_effect(self, src, tgt):
        return Effect(self.effect_id, src, tgt)
