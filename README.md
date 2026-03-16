# immich-smart-album

Automatically populates [Immich](https://immich.app/) albums based on recognized people. Supports single-person albums (all photos of that person) and multi-person albums (only photos where all listed people appear together).

## Setup

```bash
uv sync
cp .env.example .env
# edit .env with your Immich URL and API key
```

**.env**
```
IMMICH_API_KEY=your-api-key
IMMICH_URL=http://your-immich-ip:port/api
```

## Configuration

Edit `config.yml` to define album→person mappings. Person and album UUIDs are visible in the Immich web UI URLs.

```yaml
mappings:
  # Single person → all their photos added to the album
  - album_id: <album-uuid>
    person_ids:
      - <person-uuid>

  # Multiple people → only photos where all of them appear together
  - album_id: <album-uuid>
    person_ids:
      - <person-uuid-a>
      - <person-uuid-b>
```

## Usage

```bash
uv run python main.py
```
