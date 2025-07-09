from ursina.networking import rpc

from .. import network

@rpc(network.peer)
def on_connect(connection, time_received):
    """What server does when a client disconnects. Need to clean up
    character/controller and make clients clean them up as well.
    """
    pass

@rpc(network.peer)
def on_disconnect(connection, time_received):
    """What server does when a client disconnects. Need to clean up
    character/controller, 
    """
    pass
