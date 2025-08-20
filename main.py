import os
import subprocess
import time

from ursina import *

from source.client.input_handler import InputHandler
from source.client.connect import *
from source.client.world_responses import *
from source.network import network

try:
    parent_dir = os.path.dirname(os.path.abspath(__file__))
    server = subprocess.Popen(["python", "server.py"], cwd=parent_dir)
    time.sleep(1)
    app = Ursina(borderless=False)
    input_handler = InputHandler()
    network.peer.start("localhost", 8080, is_host=False)

    app.run()
finally:
    server.kill()
