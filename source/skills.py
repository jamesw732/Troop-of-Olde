import random


def check_raise_skill(char, skill):
    """Perform a random check to raise a skill level.
    Will become much more complicated eventually as probability will depend on character, enemy, etc."""
    prob = 0.5
    return random.random() < prob

def raise_skill(char, skill):
    char.skills[skill] += 1

