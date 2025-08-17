from ursina import *

from .effect import *
from ..base import *
from ..network import network


dt = 1/5


class DeathSystem(Entity):
    """Handles deaths for all characters.

    If a character's health is 0, kill it."""
    def __init__(self, gamestate):
        super().__init__()
        self.chars = gamestate.uuid_to_char.values()

    @every(dt)
    def check_deaths(self):
        """Loop over all characters and check if they need to die

        Could be optimized by storing characters that need to die
        upon updating their stats, and only looping over those."""
        for char in list(self.chars):
            if char.health <= 0:
                char.alive = False
                uuid = char.uuid
                # Lots of complicated stuff handled in char.on_destroy
                # See World.make_char_on_destroy
                destroy(char)
                network.broadcast(network.peer.remote_kill, uuid)
