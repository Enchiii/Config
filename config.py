from pydantic import BaseModel, create_model
from typing import Any, Dict, Tuple, Type
import json
import os
from threading import Lock


def create_config(name: str, data: dict, root_path: str = "") -> Type[BaseModel]:
    fields: Dict[str, Tuple[Any, Any]] = {}
    for key, value in data.items():
        if isinstance(value, dict):
            submodel = create_config(key.capitalize(), value, root_path)
            fields[key] = (submodel, ...)
        else:
            fields[key] = (type(value), ...)
            if isinstance(value, str) and "_path" in key and root_path:
                fields[f"full_{key}"] = (str, os.path.join(root_path, value))

    return create_model(name, **fields)


class Config:
    _instance = None
    _lock = Lock()

    def __new__(cls, json_path: str = "config.json"):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._load(json_path)
        return cls._instance

    def _load(self, json_path: str):
        if not os.path.exists(json_path):
            raise FileNotFoundError(f"Config file '{json_path}' does not exist.")

        self._json_path = json_path
        print(f"Loading config from: '{json_path}'...")

        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        self._raw_data = data
        root = data.get("root", "")

        ConfigModel = create_config("DynamicConfig", data, root)
        self._config = ConfigModel(**data)

        print(f"Loaded config from: '{json_path}'")

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
            json.dump(self._raw_data, f, indent=4)
