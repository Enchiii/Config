from config import Config


def print_config_vars(config, prefix="config"):
    if hasattr(config, "__dict__"):
        for attr, value in vars(config).items():
            full_name = f"{prefix}.{attr}"
            # If value is a nested config or dict-like, recurse
            if hasattr(value, "__dict__") or isinstance(value, dict):
                print_config_vars(value, full_name)
            elif isinstance(value, list):
                # print lists as is
                print(f"{full_name}: {value}")
            else:
                print(f"{full_name}: {value}")
    elif isinstance(config, dict):
        for k, v in config.items():
            full_name = f"{prefix}.{k}"
            if isinstance(v, (dict, list)):
                print_config_vars(v, full_name)
            else:
                print(f"{full_name}: {v}")
    elif isinstance(config, list):
        print(f"{prefix}: {config}")
    else:
        print(f"{prefix}: {config}")


def main():
    config = Config()

    print_config_vars(config)


if __name__ == "__main__":
    main()
