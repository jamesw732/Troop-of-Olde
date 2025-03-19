"""Top-level networking file. Any other submodule that uses networking can mostly just import this.
This does NOT import client_continuous or host_continuous, since those files should
really only be imported by the main file."""
from ursina.networking import RPCPeer, rpc

from .network import network
from .world_requests import *
from .connect import *
from .disconnect import *
from .register import *
