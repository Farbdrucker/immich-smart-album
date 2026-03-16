import logging
import sys

import requests
import yaml
from pydantic import BaseModel, ValidationError
from pydantic_settings import BaseSettings, SettingsConfigDict
from rich.logging import RichHandler

logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    handlers=[RichHandler(rich_tracebacks=True, show_path=False)],
)
log = logging.getLogger("immich-smart-album")

BATCH_SIZE = 1000


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")
    immich_api_key: str
    immich_url: str


class AlbumMapping(BaseModel):
    album_id: str
    person_ids: list[str]


class AppConfig(BaseModel):
    mappings: list[AlbumMapping]


class ImmichClient:
    def __init__(self, base_url: str, api_key: str) -> None:
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self.session.headers.update({"x-api-key": api_key})

    def get_person_asset_ids(self, person_id: str) -> list[str]:
        asset_ids: list[str] = []
        page = 1
        while True:
            log.debug("Fetching assets for person %s (page %d)", person_id, page)
            response = self.session.post(
                f"{self.base_url}/search/metadata",
                json={"personIds": [person_id], "size": BATCH_SIZE, "page": page},
            )
            response.raise_for_status()
            data = response.json()["assets"]
            asset_ids.extend(item["id"] for item in data["items"])
            if data["nextPage"] is None:
                break
            page += 1
        return asset_ids

    def add_assets_to_album(self, album_id: str, asset_ids: list[str]) -> dict[str, int]:
        added = already_present = failed = 0
        for i in range(0, len(asset_ids), BATCH_SIZE):
            batch = asset_ids[i : i + BATCH_SIZE]
            log.debug("Adding batch of %d assets to album %s", len(batch), album_id)
            response = self.session.put(
                f"{self.base_url}/albums/{album_id}/assets",
                json={"ids": batch},
            )
            response.raise_for_status()
            for result in response.json():
                if result.get("success"):
                    added += 1
                elif result.get("error") == "duplicate":
                    already_present += 1
                else:
                    failed += 1
        return {"added": added, "already_present": already_present, "failed": failed}


def load_config(path: str = "config.yml") -> AppConfig:
    with open(path) as f:
        data = yaml.safe_load(f)
    return AppConfig.model_validate(data)


def main() -> None:
    try:
        settings = Settings()  # type: ignore[call-arg]
    except ValidationError as e:
        log.error("Configuration error: %s", e)
        sys.exit(1)

    try:
        config = load_config("config.yml")
    except (OSError, ValidationError) as e:
        log.error("Failed to load config.yml: %s", e)
        sys.exit(1)

    log.info("Loaded config: %d mapping(s)", len(config.mappings))

    client = ImmichClient(settings.immich_url, settings.immich_api_key)

    for mapping in config.mappings:
        person_sets: list[set[str]] = []
        all_failed = False
        for person_id in mapping.person_ids:
            try:
                ids = client.get_person_asset_ids(person_id)
                log.info("Person %s: %d assets", person_id, len(ids))
                person_sets.append(set(ids))
            except requests.HTTPError as e:
                log.warning("Failed to fetch assets for person %s: %s", person_id, e)
                all_failed = True
                break

        if all_failed or not person_sets:
            log.warning("Skipping album %s due to fetch errors.", mapping.album_id)
            continue

        if len(person_sets) == 1:
            asset_ids = list(person_sets[0])
        else:
            asset_ids = list(person_sets[0].intersection(*person_sets[1:]))
            log.info(
                "Album %s: %d asset(s) where all %d person(s) appear together",
                mapping.album_id, len(asset_ids), len(mapping.person_ids),
            )

        if not asset_ids:
            log.info("Album %s: no matching assets, skipping.", mapping.album_id)
            continue

        try:
            result = client.add_assets_to_album(mapping.album_id, asset_ids)
            log.info(
                "Album %s: added=%d, already_present=%d, failed=%d",
                mapping.album_id,
                result["added"],
                result["already_present"],
                result["failed"],
            )
        except requests.HTTPError as e:
            log.warning("Failed to add assets to album %s: %s", mapping.album_id, e)


if __name__ == "__main__":
    main()
