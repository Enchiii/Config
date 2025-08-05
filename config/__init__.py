import os
import json
from tqdm import tqdm
from typing import Any
from threading import Lock
from .utils import count_fields, flatten_dict, create_config, resolve_vars_in_dict


class Config:
    _instance = None
    _lock = Lock()

    def __new__(cls, json_path: str = "config.json", show_progress: bool = True):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._load(json_path, show_progress)
        return cls._instance

    def _load(self, json_path: str, show_progress: bool):
        if not os.path.exists(json_path):
            raise FileNotFoundError(f"Config file '{json_path}' does not exist.")

        self._json_path = json_path
        print(f"Loading settings from '{json_path}'")

        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        self._raw_data = data

        flat_vars = flatten_dict(data)

        resolved_data = resolve_vars_in_dict(data, flat_vars)

        root = resolved_data.get("root", "")

        if show_progress:
            total_fields = count_fields(resolved_data)
            with tqdm(
                total=total_fields,
                desc="Parsing config",
                ncols=60,
                colour="cyan",
                bar_format="{n_fmt}/{total_fmt} [{bar}] {percentage:3.0f}%"
            ) as pbar:
                ConfigModel = create_config("DynamicConfig", resolved_data, root, progress_bar=pbar)
        else:
            ConfigModel = create_config("DynamicConfig", resolved_data, root)

        self._config = ConfigModel(**resolved_data)

    def __getattr__(self, name):
        return getattr(self._config, name)

    def get(self, dotted_key: str, default=None):
        keys = dotted_key.split(".")
        val = self._config
        for k in keys:
            try:
                val = getattr(val, k)
            except AttributeError:
                return default
        return val

    def reload(self):
        type(self)._instance = None
        return Config(self._json_path)

    def set(self, key: str, value: Any):
        keys = key.split(".")
        data = self._raw_data

        for k in keys[:-1]:
            if k not in data or not isinstance(data[k], dict):
                data[k] = {}
            data = data[k]

        data[keys[-1]] = value

        with open(self._json_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
