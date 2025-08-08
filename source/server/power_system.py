from ursina import *

from .effect import *
from ..base import *
from ..network import network


dt = 1/5


class PowerSystem(Entity):
    """Ticks the GCD of each character and responds to client's power inputs."""
    def __init__(self, chars):
        super().__init__()
        self.chars = chars

    @every(dt)
    def tick_gcd(self):
        for char in self.chars:
            if char.get_on_gcd():
                char.tick_gcd(time.dt)

    def char_use_power(self, char, power):
        tgt = power.get_target(char)
        if tgt is None:
            return
        if char.energy < power.cost:
            return
        power.use(char, tgt)
        # Upon using a power, need to update energy to clients
        network.broadcast_cbstate_update(char)
