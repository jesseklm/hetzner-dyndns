from pathlib import Path

import tomli_w
import yaml


def get_config_local(filename: Path) -> dict:
    if not filename.exists():
        return {'error': 'file does not exist'}
    with open(filename, 'r') as file:
        try:
            return yaml.safe_load(file)
        except yaml.YAMLError as e:
            print(e, flush=True)
            return {'error': str(e)}


if __name__ == '__main__':
    config = get_config_local(Path('config.yaml'))
    with open('config.toml', 'wb') as f:
        tomli_w.dump(config, f)
