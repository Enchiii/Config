import os
import json

from .replacer import Replacer
from typing import Any, Dict, Tuple, Type
from pydantic import BaseModel, create_model


def count_fields(data: dict) -> int:
    count = 0
    for _, value in data.items():
        if isinstance(value, dict):
            count += 1 + count_fields(value)
        elif isinstance(value, str) and value.startswith("@"):
            if value.startswith("@!"):
                path = value[2:]
            else:
                path = value[1:]

            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)

            flat_vars = flatten_dict(data)
            resolved_data = resolve_vars_in_dict(data, flat_vars)
            count += count_fields(resolved_data)
        else:
            count += 1
    return count


def flatten_dict(data: dict, parent_key: str = '', sep: str = '.') -> dict:
    items = {}
    for k, v in data.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.update(flatten_dict(v, new_key, sep=sep))
        else:
            items[new_key] = v
    return items


def create_config(name: str, data: dict, root_path: str = "", progress_bar=None) -> Type[BaseModel]:
    fields: Dict[str, Tuple[Any, Any]] = {}

    for key, value in data.items():
        if isinstance(value, str) and value.startswith('#'):
            continue

        if isinstance(value, str) and value.startswith("@"):
            process_vars = True
            child_path = None

            if value.startswith("@!"):
                process_vars = False
                child_path = value[2:]
            else:
                child_path = value[1:]

            child_data = load_child_config(child_path, process_vars)

            submodel = create_config(key.capitalize(), child_data, root_path, progress_bar)
            fields[key] = (submodel, ...)
            if progress_bar:
                progress_bar.update(1)
            continue

        if isinstance(value, dict):
            submodel = create_config(key.capitalize(), value, root_path, progress_bar)
            fields[key] = (submodel, ...)
        else:
            fields[key] = (type(value), ...)

        if progress_bar:
            progress_bar.update(1)

    return create_model(name, **fields)

def resolve_vars_in_dict(data: dict, variables: dict, base_path: str = "") -> dict:
    replacer = Replacer(variables)

    def resolve_value(v):
        if isinstance(v, dict):
            return {k: resolve_value(val) for k, val in v.items()}

        elif isinstance(v, str):
            if v.startswith("@"):
                process_vars = True
                if v.startswith("@!"):
                    process_vars = False
                    sub_path = v[2:]
                else:
                    sub_path = v[1:]

                full_path = os.path.join(base_path, sub_path) if base_path else sub_path
                with open(full_path, "r", encoding="utf-8") as f:
                    sub_data = json.load(f)

                if process_vars:
                    sub_data = resolve_vars_in_dict(sub_data, flatten_dict(sub_data), base_path=os.path.dirname(full_path))

                return sub_data
            else:
                # Regular variable replacement
                return replacer.replace(v)
        else:
            return v

    return resolve_value(data)



def load_child_config(path: str, process_vars: bool = True) -> dict:
    full_path = path if os.path.isabs(path) else os.path.join("./", path)
    if not os.path.exists(full_path):
        raise FileNotFoundError(f"Child config file '{full_path}' not found.")

    with open(full_path, "r", encoding="utf-8") as f:
        child_data = json.load(f)

    if process_vars:
        flat_child_vars = flatten_dict(child_data)
        child_data = resolve_vars_in_dict(child_data, flat_child_vars)

    return child_data
