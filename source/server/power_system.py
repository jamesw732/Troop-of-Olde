from ursina import *

from .effect import *
from ..base import *
from ..network import network


dt = 1/5


class PowerSystem(Entity):
    """Ticks the GCD of each character and responds to client's power inputs.

    This class does not have ownership over powers. Instead, powers are created
    by World, this class is merely for managing the per-frame Power operations,
    and are accessed through Characters."""
    def __init__(self, chars):
        super().__init__()
        self.chars = chars

    @every(dt)
    def tick_cooldowns(self):
        """Increment all cooldowns by dt."""
        for char in self.chars:
            for power in char.powers:
                if power is not None:
                    power.tick_cd(dt)
            if char.get_on_gcd():
                char.tick_gcd(dt)

    def char_use_power(self, src, power):
        tgt = power.get_target(src)
        if tgt is None:
            return
        if src.energy < power.cost:
            return
        power.start_cooldown()
        effect = Effect(power.effect_mnem, src, tgt)
        effect.attempt_apply()
        # Upon using a power, need to update energy to clients
        network.broadcast_cbstate_update(tgt)
