from ursina import *
import os
import json

from .effect import Effect
from .. import Power

class ServerPower(Power):
    def __init__(self, power_id, inst_id):
        """Create unique power instance id and make Power"""
        super().__init__(power_id, inst_id)

    def use(self, src, tgt):
        """Does the server-side things involved with using a power.
        Used by char on their active target."""
        super().use(src, tgt)
        effect = Effect(self.effect_mnem, src, tgt)
        effect.attempt_apply()
