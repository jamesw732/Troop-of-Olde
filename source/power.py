from ursina import *
import os
import json

from .effect import Effect
from .gamestate import gs

power_path = os.path.join(os.path.dirname(__file__), "..", "data", "powers.json")
with open(power_path) as power_json:
    id_to_power_data = json.load(power_json)


class Power(Entity):
    def __init__(self, power_id):
        super().__init__()
        self.power_id = power_id
        power_data = id_to_power_data[str(power_id)]
        for k, v in power_data.items():
            setattr(self, k, v)

        # set to True immediately after use
        self.on_cooldown = False
        # ticks up if self.on_cooldown
        self.timer = 0

    def get_effect(self):
        return Effect(self.effect_id)

    def client_use_power(self):
        assert not gs.network.peer.is_hosting()
        if gs.pc.get_on_gcd():
            gs.ui.gamewindow.add_message("Cannot use another power during global cooldown")
            return
        self.set_char_gcd(gs.pc)
        gs.network.peer.request_use_power(gs.network.server_connection, self.power_id)

    def set_char_gcd(self, char):
        char.gcd = self.gcd_duration
        char.gcd_timer = 0
