from ursina import *
import os
import json

from .. import Power
from .ui import ui


class ClientPower(Power):
    def __init__(self, char, power_id, inst_id):
        """Make power"""
        super().__init__(char, power_id, inst_id)

    def handle_power_input(self):
        """Handles client's input to use a power"""
        tgt = self.get_target()
        if self.char.get_on_gcd() or self.on_cooldown:
            if self.char.next_power is self:
                # Attempted to queue an already queued power, just remove it
                self.char.next_power = None
            else:
                # Queued powers are currently handled by PlayerController
                self.queue()
            return False
        else:
            self.use()
            return True

    def use(self):
        """Does the client-side things involved with using a power.

        Currently, just sets the GCD. Eventually, will also invoke animation."""
        tgt = self.get_target()
        if tgt is None:
            return
        if self.char.energy < self.cost:
            return
        super().use()
