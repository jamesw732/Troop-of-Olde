import random

from .gamestate import gs


def check_raise_skill(char, skill):
    """Perform a random check to raise a skill level.
    Will become much more complicated eventually as probability will depend on character, enemy, etc."""
    prob = 0.5
    return random.random() < prob

def raise_skill(char, skill):
    assert gs.network.peer.is_hosting()
    char.skills[skill] += 1
    connection = gs.network.uuid_to_connection[char.uuid]
    gs.network.peer.remote_update_skill(connection, skill, char.skills[skill])

