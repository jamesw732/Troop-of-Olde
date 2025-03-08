import os
import subprocess

from ursina import *

from source.networking import network
from source.networking.connect import *
from source.networking.client_continuous import *
from source.networking.disconnect import *
from source.networking.register import *

try:
    parent_dir = os.path.dirname(os.path.abspath(__file__))
    server = subprocess.Popen(["python", "server.py"], cwd=parent_dir)
    app = Ursina(borderless=False)
    network.peer.start("localhost", 8080, is_host=False)

    app.run()
finally:
    server.kill()
