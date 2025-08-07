# 🛠️ Config

A **minimalistic configuration system** for Python using JSON and Pydantic.

---

## 📥 Installation

Using **pip**:

```bash
pip install -r config_reqs.txt
```

Using **conda**:

```bash
conda install --file config_reqs.txt
```

---

## 🔣 Marker Reference

| Marker | Syntax         | Description                                                                                              |
|--------|----------------|----------------------------------------------------------------------------------------------------------|
| `.`    | `base.var`     | Access nested config fields (usable within other markers)                                                |
| `#`    | `"#info": ""`  | Add comment for clarity or documentation purposes; ignored during processing                             |
| `!`    | `!var!`        | Insert variable **directly**, without recursive resolution                                               |
| `$`    | `$var$`        | Insert variable **with recursive** resolution                                                            |
| `%`    | `%var%`        | Insert variable as a **normalized path** (auto adds slashes and resolves structure)                      |
| `{}`   | `{ENV_VAR}`    | Insert environment variable (requires manual loading of environment into the process)                    |
| `[]`   | `var[index]`   | Access list element by index or dictionary value by key inside markers (e.g., `$arr[0]$`, `$dict[key]$`) |
| `@`    | `@path.json`   | Import and merge external config file with **marker processing enabled**                                 |
| `@!`   | `@!path.json`  | Import and merge external config file as **raw JSON** (skips marker processing)                          |


---

## ⚙️ Usage

**Example python usage:**

```python
from config import Config

config = Config()  # Automatically loads 'config.json'

# Access values directly
print(config.root)
print(config.sub.model_weights)

# Reload configuration from disk
config.reload()

# Programmatic access & editing
config.get("sub.model_weights")
config.set("sub.new_value", 123)
```

**Example `config.json`:**

```json
{
  "root": "./data",
  "env_path": "{HOME}/project",
  "sub": {
    "root": "%root%/models",
    "dirs": [
      "$sub.root$",
      "!sub.root!",
      "%sub.root%/pink"
    ]
  },
  "model_weights": ["weights-n.pt", "weights-s.pt", "weights-m.pt"],
  "default_weight": "$model_weights[1]$",
  "path_to_weight": "%sub.dirs[2]%/%default_weight%",
  "#outer configs": "(this kv-pair is skipped)",
  "external_config": "@configs/extra.json",
  "raw_import": "@!configs/raw_extra.json"
}
```

---

[TODO] fix double slash ("\\\\") bug  
[TODO] add possibility to go up a config hierarchy in child configs by adding "^" marker**s** before a variable (like so: `$^var$` to go 1 up, or `$^^var$` to go 2 up and so on) 
