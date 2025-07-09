from ursina import destroy
from ursina.networking import rpc

from .network import network


@rpc(network.peer)
def on_disconnect(connection, time_received):
    """What other clients should do when you disconnect
    When host receives this call, delete all references to character, and
    tell clients to delete those references as well.
    When a non-host receives this call, it means the host disconnected. In this case,
    delete all characters. Eventually, save character state too"""
    # Normal user disconnected
    if network.peer.is_hosting():
        char = network.connection_to_char.get(connection)
        if char:
            uuid = char.uuid
            destroy(char)
            # Character.on_destroy handles most of the rest
            del network.connection_to_char[connection]
            del network.uuid_to_connection[uuid]
            network.broadcast(network.peer.remote_remove_char, uuid)
    # The host disconnected
    else:
        network.my_uuid = None


@rpc(network.peer)
def remote_remove_char(connection, time_received, uuid: int):
    """What a non-host does to remove a character"""
    if network.peer.is_hosting():
        return
    char = world.uuid_to_char.get(uuid)
    if char:
        destroy(char)
