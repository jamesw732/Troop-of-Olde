from ursina.networking import RPCPeer, rpc
from . import network
from ..ui import ui

@rpc(network.peer)
def remote_print(connection, time_received, msg: str):
    """Remotely print a message for another player"""
    ui.gamewindow.add_message(msg)
