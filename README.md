# Repository for the game Troop of Olde
This is a currently extremely incomplete prototype for a game which is planned
to be an solo/multiplayer fantasy RPG with Everquest-style combat, but with a small replayable world.
The hope is to provide a "dungeon crawl with your friends" experience - it will not be massively
multiplayer, the tentative plan is to make it private-server based (think Minecraft).

This game is still in the earliest of development stages, and this is the first game I've
developed. This game will not remain open source forever. The current goal is to get a working
prototype of all desired functionality in the game, and after that point, I will archive this
repository and not contribute to it or maintain it anymore, and open a closed respository for
developing content.

## Repository Tour

### `Doc`
Directory containing all documentation for the codebase and the game itself.
This directory is not exactly up to date, but currently `gameplay.txt` contains
plans for many future aspects of the game from the perspective of the player,
and `developer.tex` contains details on implementation choices.

### `data`
The `data` repository is a too-all-encompassing directory that contains assets,
and also the essential "database" of the game, although this database is actually
just a bunch of `.json` files. Eventually, will probably be split up into two
directories for assets and database.

### `source`
This is the source code for the game. See `Doc` for some details
on the code design.

### `tests`
Eventually, I hope to have a complete test suite for everything.
Currently, too much of the code is changing for tests to be effective, more than
half of my time is spent refactoring.

### Root directory
I do not currently have a build process. This is probably a mistake.
- The `server.py` program will launch a headless server that handles the core game
logic and that clients can connect to.
- The `main.py` program will launch a client, and also spawn a `server` child process
that hosts the server locally. I haven't tested connections from other devices
yet, but I think LAN multiplayer may just work for this.
- The `main_multiplayer.py` program will launch a client. To connect to an existing
server, press `c`. This is unlikely to work with multiple devices right out of the
box. Yes, I'll eventually make a launch screen.
- `todo.txt` is just a list of things I plan to do, ordered by priority.
This will eventually evolve into Github issues.

## Github
The hope is to eventually integrate Issues and Projects, but this is surprisingly a lot
to keep up with. Once progress is more stable, I will spend some time trying to get
these back up to speed. But right now they're super overwhelming, and I'm not even
sure if I want to implement half of them.