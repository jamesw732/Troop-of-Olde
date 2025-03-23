"""Host is responsible for continuously updating information like health for all characters"""
from ursina import time
from ursina.networking import rpc

from .network import network
from .world_responses import *
from ..gamestate import gs
from ..states.state import State


def update():
    network.peer.update()
