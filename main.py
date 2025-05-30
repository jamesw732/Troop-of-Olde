import os
import subprocess
import time

from ursina import *

from source.networking import network
from source.networking.connect import *
from source.networking.disconnect import *
from source.networking.register import *

try:
    parent_dir = os.path.dirname(os.path.abspath(__file__))
    server = subprocess.Popen(["python", "server.py"], cwd=parent_dir)
    time.sleep(1)
    app = Ursina(borderless=False)
    network.peer.start("localhost", 8080, is_host=False)

    app.run()
finally:
    server.kill()
