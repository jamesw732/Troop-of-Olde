from ursina import *

from .effect import *
from ..base import *
from ..network import network
from ..power import Power


dt = POWER_UPDATE_RATE


class PowerSystem(Entity):
    """Ticks the GCD of each character and responds to client's power inputs.

    This class does not have ownership over powers. Instead, powers are created
    by World, this class is merely for managing the per-tick Power operations,
    and are accessed through Characters."""
    def __init__(self, chars):
        super().__init__()
        self.chars = chars
        self.inst_id_to_power = dict()
        self.power_inst_id_ct = 0

    def make_power(self, power_mnem):
        inst_id = self.power_inst_id_ct
        self.power_inst_id_ct += 1
        power = Power(power_mnem, inst_id)
        self.inst_id_to_power[inst_id] = power
        return power

    @every(dt)
    def tick_cooldowns(self):
        """Increment all cooldowns by dt."""
        for char in self.chars:
            if char.get_on_gcd():
                char.tick_gcd(dt)
        for power in self.inst_id_to_power.values():
            power.tick_cd(dt)

    def char_use_power(self, src, power):
        tgt = src.target
        if tgt is None:
            return
        if src.energy < power.cost:
            return
        power.start_cooldown()
        effect = Effect(power.effect_mnem, src, tgt)
        effect.attempt_apply()
        # Upon using a power, need to update energy to clients
        network.broadcast_cbstate_update(tgt)
