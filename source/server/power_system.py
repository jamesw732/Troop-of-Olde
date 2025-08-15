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
    def __init__(self, effect_system):
        self.effect_system = effect_system
        super().__init__()
        self.inst_id_to_power = dict()
        self.power_inst_id_ct = 0

        self.cooldown_powers = dict()
        self.gcd_chars = dict()

    def make_power(self, power_mnem):
        inst_id = self.power_inst_id_ct
        self.power_inst_id_ct += 1
        power = Power(power_mnem, inst_id)
        self.inst_id_to_power[inst_id] = power
        return power

    @every(dt)
    def tick_cooldowns(self):
        """Increment all cooldowns by dt.

        Could optimize this by only looking at powers that are on cooldown
        in the first place, and only looking at characters that are on GCD.
        """
        for uuid, char in list(self.gcd_chars.items()):
            # print(f"Incrementing {char.cname} gcd: {char.gcd_timer}")
            char.tick_gcd(dt)
            if not char.get_on_gcd():
                del self.gcd_chars[uuid]
        for inst_id, power in list(self.cooldown_powers.items()):
            # print(f"Incrementing {power.power_mnem} cooldown: {power.timer}")
            power.tick_cd(dt)
            if not power.on_cooldown:
                del self.cooldown_powers[inst_id]

    def char_use_power(self, src, power):
        tgt = src.target
        if tgt is None:
            return
        if src.energy < power.cost:
            return
        src.start_gcd(power.gcd_duration)
        self.gcd_chars[src.uuid] = src
        power.start_cooldown()
        self.cooldown_powers[power.inst_id] = power
        effect = self.effect_system.make_effect(power.effect_mnem, src, tgt)
        effect.attempt_apply()
        # Upon using a power, need to update stats (mainly energy) to clients
        network.broadcast_cbstate_update(tgt)
