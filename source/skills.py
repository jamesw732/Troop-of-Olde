import random

from ursina.networking import rpc

from .ui import ui
from .networking import network
from .gamestate import gs

def attempt_raise_skill(char, skill, prob):
    if random.random() < prob:
        raise_skill(char, skill)

def raise_skill(char, skill):
    char.skills[skill] += 1
    if gs.pc is char:
        ui.playerwindow.skills.set_label_text(skill)
    elif network.peer.is_hosting():
        connection = network.uuid_to_connection[char.uuid]
        network.peer.remote_raise_skill(connection, skill)

@rpc(network.peer)
def remote_raise_skill(connection, time_received, skill: str):
    raise_skill(gs.pc, skill)
    ui.playerwindow.skills.set_label_text(skill)
