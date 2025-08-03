# Repository for the game Troop of Olde
This repository is for an early-development game, which is planned to be a solo/multiplayer RPG.
It hopes to emulate MMORPG-style dungeon crawling and combat, but on a much smaller scale.
A good comparison of the vision to existing games is a mix between EverQuest and Slay the Spire.

This game will not remain open source forever, the reason it's open source right now is the
hope that it will be useful to the Ursina community once the prototype version is complete. 
The current goal is to get a working prototype of all desired functionality in
the game, and after that point, this branch will be archived, and development will continue on another
(private) one. 

## Repository Tour

### Root directory
- The `server.py` program will launch a headless server that handles the core game
logic and that clients can connect to.
- The `main.py` program will launch a client, and also spawn a `server` child process
that hosts the server locally.
- The `main_multiplayer.py` program will launch a client. To connect to an existing
server, press `c`. This is has not been tested on multiple devices, but works (perhaps in
a restricted form) by connecting from two terminals on the same device.
- `todo.txt` is just a list of planned things to do, ordered by priority.
This will eventually evolve into Github issues once the development plan becomes
more stable.

### `Doc`
Directory containing all documentation for the codebase and the game itself.
`developer.tex` contains details on implementation choices, but may be out of
date at any given point in time.
On the other hand, `gameplay.txt` is more of an informal plan for game features
and content.

### `data`
This directory contains the essential "database" for the static game data,
which is just a collection of `.json` files. This may evolve into an SQLite
database, depending on needs later on.

### `source`
This is the source code for the game. See `Doc` for some details
on the code design.
