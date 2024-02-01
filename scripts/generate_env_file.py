import glob
import re
from pathlib import Path

import jinja2


def generate_env_file() -> None:
    template_generator = jinja2.Environment(
        loader=jinja2.FileSystemLoader("scripts/templates")
    )
    template = template_generator.get_template(".env.jinja")
    with open(".env", "w") as f:
        f.write(
            template.render(
                imod_collector_dev_path=__get_imod_collector_path("develop").resolve(),
                imod_collector_regression_path=__get_imod_collector_path(
                    "regression"
                ).resolve(),
                metaswap_lookup_table_path=__get_metaswap_path().resolve(),
            )
        )


def __get_imod_collector_path(tag: str) -> Path:
    """
    Find an existing path of imod_collector.
    Extract the numeric suffix from each path and find the path with the highest number
    """
    search_path = f".pixi/imod_collector/{tag}_*"
    paths = glob.glob(search_path)
    if not paths:
        raise ValueError(f"No paths found for tag {tag}")
    paths_with_numbers = []
    for path in paths:
        match = re.search(r"(\d+)$", path)
        if match:
            paths_with_numbers.append((path, int(match.group(1))))
    if not paths_with_numbers:
        raise ValueError(f"No numeric suffixes found in paths for tag {tag}")

    path_with_highest_number = max(paths_with_numbers, key=lambda x: x[1])[0]
    return Path(path_with_highest_number)


def __get_metaswap_path() -> Path:
    metaswap_path = Path(".pixi/imod_collector/e150_metaswap")
    if not metaswap_path.exists():
        raise ValueError(f"Metaswap lookup table not found at {metaswap_path}")
    return metaswap_path


if __name__ == "__main__":
    generate_env_file()
