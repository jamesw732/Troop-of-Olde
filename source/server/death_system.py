from ursina import *

from .effect import *
from ..base import *
from ..network import network


dt = 1/5


class DeathSystem(Entity):
    """Handles deaths for all characters.

    If a character's health is 0, kill it."""
    def __init__(self, chars):
        super().__init__()
        self.chars = chars

    @every(dt)
    def check_deaths(self):
        for char in list(self.chars):
            if char.health <= 0:
                char.alive = False
                uuid = char.uuid
                # Lots of complicated stuff handled in char.on_destroy
                # See World.make_char_on_destroy
                destroy(char)
                network.broadcast(network.peer.remote_kill, uuid)
