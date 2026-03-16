# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

`immich-smart-album` is a Python tool that interacts with the [Immich](https://immich.app/) self-hosted photo management API. It reads a `config.yml` to define person IDs and album IDs, then performs operations (e.g., auto-populating albums based on recognized faces/people).

## Setup

Uses `uv` for dependency management.

```bash
uv sync                    # Install dependencies
uv sync --extra dev        # Install with dev dependencies (pytest, ruff, ty)
```

Copy `.env.example` to `.env` and set:
- `IMMICH_API_KEY` — API key from Immich user settings
- `IMMICH_URL` — Base URL of the Immich instance (e.g., `http://192.168.178.98:2283/api`)

## Commands

```bash
uv run python main.py      # Run the tool
uv run pytest              # Run tests
uv run ruff check .        # Lint
uv run ruff format .       # Format
uv run ty check            # Type check
```

## Configuration

`config.yml` maps person UUIDs to album UUIDs:

```yaml
person_ids:
  - <uuid>
album_ids:
  - <uuid>
```

Person and album UUIDs come from the Immich web UI (visible in URLs when browsing people/albums).

## Architecture

Currently a single-file project (`main.py`) at the start of development. The intended pattern is:
- Read `config.yml` for person→album mappings
- Use `requests` to call the Immich REST API (authenticated via `IMMICH_API_KEY` header)
- Add photos of matched persons to the configured albums
