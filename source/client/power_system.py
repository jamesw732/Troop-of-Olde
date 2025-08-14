from ursina import *

from ..base import *
from ..network import network
from ..power import Power


dt = POWER_UPDATE_RATE


class PowerSystem(Entity):
    """Handles the per-tick Power operations."""
    def __init__(self):
        super().__init__()
        self.char = None
        self.inst_id_to_power = dict()
        self.queued_power = None
        # Powers on cooldown keyed by inst id
        self.cooldown_powers = dict()

    def make_power(self, power_mnem, inst_id):
        power = Power(power_mnem, inst_id)
        self.inst_id_to_power[inst_id] = power
        return power

    @every(dt)
    def tick_cooldowns(self):
        """Increment all cooldowns by dt.

        Could optimize this by only looking at powers that are on cooldown
        in the first place, and only looking at characters that are on GCD."""
        for power in list(self.cooldown_powers.values()):
            # If incrementing timer resulted in cooldown finishing, remove from cooldown_powers
            power.tick_cd(dt)
            if not power.on_cooldown:
                del self.cooldown_powers[power.inst_id]
        if self.char is not None and self.char.get_on_gcd():
            self.char.tick_gcd(dt)

    def handle_power_input(self, power):
        """Performs the operations caused by entering a power input.

        If not on cooldown, use the power. If on cooldown, toggle the power queue.
        Returns True if power was used, which allows input handler to update the UI."""
        if self.char.get_on_gcd() or power.on_cooldown:
            if self.queued_power is power:
                # Attempted to queue an already queued power, just remove it
                self.queued_power = None
            else:
                # Queued power will be used once off cooldown
                self.queue_power(power)
            return False
        self.use_power(power)
        return True

    def use_power(self, power):
        """Does the client-side operations involved with using a power.

        Predictively updates the UI for stats/cooldowns, and sends request to server.
        """
        tgt = self.char.target
        if tgt is None:
            return
        if self.char.energy < power.cost:
            return
        self.char.energy -= power.cost
        power.start_cooldown()
        self.char.start_gcd(power.gcd_duration)
        self.queued_power = None
        self.cooldown_powers[power.inst_id] = power
        network.peer.request_use_power(network.server_connection, power.inst_id)

    def queue_power(self, power):
        """Stores queued power.

        InputHandler will call use_power on the queued power once it and the
        player character are off cooldown/GCD.
        """
        self.queued_power = power
