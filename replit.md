# FiveM Discord Bot

## Overview
A Discord bot for monitoring FiveM (cfx.re) game servers. It can list configured servers, show all online players, search for players by name, and add new servers. Built with `discord.py` and `requests`.

## Project Structure
- `bot.py` — Main Discord bot with all commands (`=serverlist`, `=allplayer`, `=player`, `=addserver`, `=help`).
- `server_manager.py` — Loads/saves server configs and fetches FiveM player data via the cfx.re API.
- `config.json` — Persistent list of configured FiveM servers (id, name, join_code).
- `requirements.txt` — Python dependencies: `discord.py`, `requests`, `python-dotenv`.

## Setup
- Language: Python 3.12
- Required secret: `DISCORD_TOKEN` (Discord bot token from the Discord Developer Portal)
- Workflow: `Discord Bot` runs `python bot.py` as a console process (no frontend).

## Deployment
- Target: `vm` (always-on, required for a Discord bot to maintain its gateway connection).
- Run command: `python bot.py`.
