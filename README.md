# Repository for the game Troop of Olde
This is a currently extremely incomplete prototype for a game which is planned
to be an Everquest-style MMORPG, minus the M in "Massively". You play with your
friends (or by yourself), kill stuff, get more powerful, and cut out all the
drama in between all that.

## Repository Tour

### `Doc`
Directory containing all documentation for the codebase and the game itself.
Currently extremely incomplete because this repository is still young. I am still
in the "constantly refactor everything" stage of this project since managing this
potentially large codebase is a first for me. Eventually, I hope to have complete
documents on the code design, and also on the philosophy/motivation/goals of this
game. This is both for myself and for anybody else who wants to contribute to this
project.

### `data`
The `data` repository is a too-all-encompassing directory that contains assets,
and also the essential "database" of the game, although this database is actually
just a bunch of `.json` files. Eventually, will probably be split up into two
directories for assets and database.

### `source`
This is the source code for the game. Eventually see `Doc` for documentation
on the code design.

### `tests`
Eventually, I hope to have a complete test suite for everything.
Right now, this is not going so well, similar to the reason `Doc` is pretty much
empty. Too much of the code is changing for tests to be effective (more accurately,
the interface is changing while the core of the code is not).

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