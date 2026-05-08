import hashlib
import json
from pathlib import Path


class CacheManager:
    def __init__(self, cache_dir: str = ".cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def get_cache_key(
        self,
        pdf_path: str,
        page_num: int,
        model_name: str,
        output_mode: str,
        dpi: int,
        image_format: str,
        prompt_version: str,
    ) -> str:
        pdf_hash = self._hash_file(pdf_path)
        raw_key = "|".join(
            [
                pdf_hash,
                str(page_num),
                model_name,
                output_mode,
                str(dpi),
                image_format,
                prompt_version,
            ]
        )
        return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()

    def load_text(self, cache_key: str):
        cache_file = self.cache_dir / f"{cache_key}.txt"
        if not cache_file.exists():
            return None
        return cache_file.read_text(encoding="utf-8")

    def save_text(self, cache_key: str, content: str):
        cache_file = self.cache_dir / f"{cache_key}.txt"
        cache_file.write_text(content, encoding="utf-8")

    def load_json(self, cache_key: str):
        cache_file = self.cache_dir / f"{cache_key}.json"
        if not cache_file.exists():
            return None
        return json.loads(cache_file.read_text(encoding="utf-8"))

    def save_json(self, cache_key: str, content: dict):
        cache_file = self.cache_dir / f"{cache_key}.json"
        cache_file.write_text(json.dumps(content, ensure_ascii=False), encoding="utf-8")

    def _hash_file(self, file_path: str) -> str:
        digest = hashlib.sha256()
        with open(file_path, "rb") as file:
            for chunk in iter(lambda: file.read(8192), b""):
                digest.update(chunk)
        return digest.hexdigest()
