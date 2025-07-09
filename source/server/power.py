from ursina import *
import os
import json

from .effect import Effect
from .. import network, Power

class ServerPower(Power):
    def __init__(self, power_id):
        """Create unique power instance id and make Power"""
        assert network.peer.is_hosting()
        inst_id = network.power_inst_id_ct
        network.power_inst_id_ct += 1
        super().__init__(power_id, inst_id)

    def use(self, src, tgt):
        """Does the server-side things involved with using a power.
        Used by char on their active target."""
        super().use(src, tgt)
        effect = Effect(self.effect_id, src, tgt)
        # Would like some better logic here eventually, like auto-targetting based on beneficial
        # or harmful
        effect.attempt_apply()
