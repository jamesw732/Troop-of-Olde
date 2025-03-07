import random

from ursina.networking import rpc

from .. import all_skills
from ..networking import network
from ..gamestate import gs
from ..ui import ui


class SkillState(dict):
    def __init__(self, skills={}):
        for skill in all_skills:
            self[skill] = skills.get(skill, 1)


def attempt_raise_skill(char, skill, prob):
    if random.random() < prob:
        raise_skill(char, skill)

def raise_skill(char, skill):
    char.skills[skill] += 1
    if gs.pc is char:
        ui.playerwindow.skills.set_label_text(skill)
    # Not sure how this could possibly be untrue but better safe than sorry
    elif network.peer.is_hosting():
        connection = network.uuid_to_connection[char.uuid]
        network.peer.remote_raise_skill(connection, skill)

@rpc(network.peer)
def remote_raise_skill(connection, time_received, skill: str):
    raise_skill(gs.pc, skill)
    ui.playerwindow.skills.set_label_text(skill)

def serialize_skill_state(writer, state):
    for k, v in state.items():
        writer.write(k)
        writer.write(v)
    writer.write("end")

def deserialize_skill_state(reader):
    state = SkillState()
    while reader.iter.getRemainingSize() > 0:
        k = reader.read(str)
        if k == "end":
            return state
        v = reader.read(int)
        state[k] = v
    return state
