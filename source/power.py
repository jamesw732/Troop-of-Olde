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

    def get_effect(self):
        return Effect(self.effect_id)

    def get_target(self, char):
        """Returns the correct target based on the type of power and character's target

        Currently just returns the character's target, will be more complicated eventually"""
        return char.target

    def use(self, char, tgt):
        """Does the server-side things involved with using a power.
        Used by char on their active target."""
        assert gs.network.peer.is_hosting()
        if tgt is None:
            return
        self.set_char_gcd(char)

        effect = self.get_effect()
        # Would like some better logic here eventually, like auto-targetting based on beneficial
        # or harmful
        effect.attempt_apply(char, tgt)

    def client_use_power(self, char, tgt):
        """Does the client-side things involved with using a power.

        Currently, just sets the GCD. Eventually, will also invoke animation."""
        assert not gs.network.peer.is_hosting()
        if char.get_on_gcd():
            return
        if tgt is None:
            return
        self.set_char_gcd(gs.pc)

    def set_char_gcd(self, char):
        char.gcd = self.gcd_duration
        char.gcd_timer = 0

    def queue(self, char):
        char.next_power = self


