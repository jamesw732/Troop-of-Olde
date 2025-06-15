from ursina import *
import os
import json

from .effect import Effect
from .gamestate import gs

power_path = os.path.join(os.path.dirname(__file__), "..", "data", "powers.json")
with open(power_path) as power_json:
    id_to_power_data = json.load(power_json)


def make_power_from_data(char, power_data):
    """Make a power by handling cases for whether hosting or not

    Powers are mostly client/server agnostic, except for creation.
    Server needs to increment the unique id count, while clients should just"""
    if gs.network.peer.is_hosting():
        assert isinstance(power_data, int)
        # Set the instance ID. Server needs to externally transmit this upon item creation.
        power_id = power_data
        inst_id = gs.network.power_inst_id_ct
        gs.network.power_inst_id_ct += 1
    else:
        assert isinstance(power_data, tuple)
        power_id = power_data[0]
        inst_id = power_data[1]
    if inst_id >= 0 and inst_id not in gs.network.inst_id_to_power:
        power = Power(char, power_id, inst_id)
        gs.network.inst_id_to_power[inst_id] = power
        return power
    return None



class Power(Entity):
    """Powers are abilities and spells that a player has access to.

    Dual relationship with Effects. Basic difference is that Powers are permanent objects which
    depend only on a source character, while Effects are temporary objects that consider
    a source and target character. Main reason for the distinction is in the functionality."""
    def __init__(self, char, power_id, inst_id):
        """
        char: Character that has access to this Power
        power_id: id that refers to a row in the database, note unique WRT instances
        inst_id: unique instance id used to refer to this power over the network"""
        super().__init__()
        self.char = char
        self.power_id = power_id
        self.inst_id = inst_id
        power_data = id_to_power_data[str(power_id)]
        # Would it be better to be more explicit about this?
        for k, v in power_data.items():
            setattr(self, k, v)
        # set to True immediately after use
        self.on_cooldown = False
        # ticks up if self.on_cooldown
        self.timer = 0

    def handle_power_input(self):
        """Handles client's input to use a power"""
        assert not gs.network.peer.is_hosting()
        tgt = self.get_target()
        if gs.pc.get_on_gcd():
            if gs.pc.next_power is self:
                # Attempted to queue an already queued power, just remove it
                gs.pc.next_power = None
            else:
                # Queued powers are currently handled by PlayerController
                self.queue()
        else:
            self.client_use_power()
            gs.network.peer.request_use_power(gs.network.server_connection, self.power_id)

    def get_target(self):
        """Returns the correct target based on the type of power and character's target

        Currently just returns the character's target, will be more complicated eventually"""
        return self.char.target

    def queue(self):
        self.char.next_power = self

    def client_use_power(self):
        """Does the client-side things involved with using a power.

        Currently, just sets the GCD. Eventually, will also invoke animation."""
        assert not gs.network.peer.is_hosting()
        tgt = self.get_target()
        if self.char.get_on_gcd():
            return
        if tgt is None:
            return
        if self.char.energy < self.cost:
            return
        self.char.energy -= self.cost
        self.set_char_gcd()
        self.char.next_power = None
        gs.ui.actionbar.start_gcd_animation()

    def set_char_gcd(self):
        self.char.gcd = self.gcd_duration
        self.char.gcd_timer = 0

    def use(self, tgt):
        """Does the server-side things involved with using a power.
        Used by char on their active target."""
        assert gs.network.peer.is_hosting()
        if tgt is None:
            return
        if self.char.energy < self.cost:
            return
        self.char.energy -= self.cost
        self.set_char_gcd()
        self.char.next_power = None
        effect = Effect(self.effect_id, self.char, tgt)
        # Would like some better logic here eventually, like auto-targetting based on beneficial
        # or harmful
        effect.attempt_apply()
