from ursina import *

from ..base import *
from ..network import network


dt = 1/5


class PowerSystem(Entity):
    """Ticks the player character's GCD and responds to server's power updates."""
    def __init__(self, char, ui_callback = lambda: None):
        super().__init__()
        self.char = char
        self.ui_callback = ui_callback

    @every(dt)
    def tick_cooldowns(self):
        """Increment all cooldowns by dt. If ready, performs queued power."""
        for power in self.char.powers:
            if power is not None:
                power.tick_cd(dt)
        if self.char.get_on_gcd():
            self.char.tick_gcd(dt)
        elif self.char.next_power is not None and not self.char.next_power.on_cooldown:
            self.use_power(self.char.next_power)

    def handle_power_input(self, power):
        """Performs the operations caused by entering a power input.

        If not on cooldown, use the power. If on cooldown, queue the power
        Returns True if the power was used, otherwise returns False."""
        if self.char.get_on_gcd() or power.on_cooldown:
            if self.char.next_power is power:
                # Attempted to queue an already queued power, just remove it
                self.char.next_power = None
            else:
                # Queued power will be used once off cooldown
                power.queue(self.char)
        else:
            self.use_power(power)

    def use_power(self, power):
        tgt = power.get_target(self.char)
        if tgt is None:
            return
        if self.char.energy < power.cost:
            return
        self.char.energy -= power.cost
        power.start_cooldown()
        self.char.start_gcd(power.gcd_duration)
        self.ui_callback()
        network.peer.request_use_power(network.server_connection, power.inst_id)

