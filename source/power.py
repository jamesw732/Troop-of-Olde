from ursina import *
import os
import json

from .effect import make_effect
from .gamestate import gs

power_path = os.path.join(os.path.dirname(__file__), "..", "data", "powers.json")
with open(power_path) as power_json:
    id_to_power_data = json.load(power_json)


class Power():
    """Base class for Powers which is the intersection of Client/Server Powers

    Powers are permanent objects which are bound to a character and database id.
    Dual relationship with Effects, which are temporary objects spawned when a Power is used.
    """
    def __init__(self, char, power_id, inst_id):
        """
        char: Character that has access to this Power
        power_id: id that refers to a row in the database, note unique WRT instances
        inst_id: unique instance id used to refer to this power over the network"""
        self.char = char
        self.power_id = power_id
        self.inst_id = inst_id
        gs.network.inst_id_to_power[self.inst_id] = self
        power_data = id_to_power_data[str(power_id)]
        # Would it be better to be more explicit about this?
        for k, v in power_data.items():
            setattr(self, k, v)
        # set to True immediately after use
        self.on_cooldown = False
        # ticks up if self.on_cooldown
        self.timer = 0

    def get_target(self):
        """Returns the correct target based on the type of power and character's target

        Currently just returns the character's target, will be more complicated eventually"""
        return self.char.target

    def queue(self):
        self.char.next_power = self

    def set_char_gcd(self):
        self.char.gcd = self.gcd_duration
        self.char.gcd_timer = 0


class ServerPower(Power):
    def __init__(self, char, power_id):
        """Create unique power instance id and make Power"""
        assert gs.network.peer.is_hosting()
        inst_id = gs.network.power_inst_id_ct
        gs.network.power_inst_id_ct += 1
        super().__init__(char, power_id, inst_id)

    def use(self, tgt):
        """Does the server-side things involved with using a power.
        Used by char on their active target."""
        if tgt is None:
            return
        if self.char.energy < self.cost:
            return
        self.char.energy -= self.cost
        self.set_char_gcd()
        self.char.next_power = None
        effect = make_effect(self.effect_id, self.char, tgt)
        # Would like some better logic here eventually, like auto-targetting based on beneficial
        # or harmful
        effect.attempt_apply()


class ClientPower(Power):
    def __init__(self, char, power_id, inst_id):
        """Make power"""
        assert not gs.network.peer.is_hosting()
        super().__init__(char, power_id, inst_id)

    def handle_power_input(self):
        """Handles client's input to use a power"""
        tgt = self.get_target()
        if gs.pc.get_on_gcd():
            if gs.pc.next_power is self:
                # Attempted to queue an already queued power, just remove it
                gs.pc.next_power = None
            else:
                # Queued powers are currently handled by PlayerController
                self.queue()
        else:
            self.use()
            gs.network.peer.request_use_power(gs.network.server_connection, self.inst_id)

    def use(self):
        """Does the client-side things involved with using a power.

        Currently, just sets the GCD. Eventually, will also invoke animation."""
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
