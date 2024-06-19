from .base import *

from ..combat import *


@rpc(network.peer)
def remote_attempt_melee_hit(connection, time_received, src_uuid: int, tgt_uuid: int):
    src = network.uuid_to_char[src_uuid]
    tgt = network.uuid_to_char[tgt_uuid]
    attempt_melee_hit(src, tgt)