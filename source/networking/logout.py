from .base import *



@rpc(network.peer)
def on_disconnect(connection, time_received):
    """What other clients should do when you disconnect
    When host receives this call, delete all references to character, and
    tell clients to delete those references as well.
    When a non-host receives this call, it means the host disconnected. In this case,
    delete all characters. Eventually, save character state too"""
    pass

@rpc(network.peer)
def remote_remove_char(connection, time_received, uuid: int):
    """What a non-host does to remove a character"""
    pass

def remove_char(uuid:int):
    """Helper function for removing a box.
    Whether to remove reference in connection_to_char depends on peer.is_hosting()"""
    pass