import json
import os
from threading import Lock
from typing import Any, Dict, Tuple, Type

from pydantic import BaseModel, create_model


def create_config_model(name: str, data: dict, root_path: str = "") -> Type[BaseModel]:
    fields: Dict[str, Tuple[Any, Any]] = {}

    for key, value in data.items():
        if isinstance(value, dict):
            submodel = create_config_model(key.capitalize(), value, root_path)
            fields[key] = (submodel, None)
        else:
            fields[key] = (type(value), None)
            if isinstance(value, str) and "_path" in key and root_path:
                full_key = f"full_{key}"
                fields[full_key] = (str, None)

    return create_model(name, **fields)


def instantiate_model(model_cls: Type[BaseModel], data: dict, root_path: str = "") -> BaseModel:
    values: Dict[str, Any] = {}

    for key, value in data.items():
        if isinstance(value, dict):
            submodel_cls = model_cls.__annotations__[key]
            values[key] = instantiate_model(submodel_cls, value, root_path)
        else:
            values[key] = value
            if isinstance(value, str) and "_path" in key and root_path:
                full_key = f"full_{key}"
                values[full_key] = os.path.join(root_path, value)

    return model_cls(**values)


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

        ConfigModel = create_config_model("DynamicConfig", data, root)
        self._config = instantiate_model(ConfigModel, data, root)

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
