from dynalog import config, get_logger
from pathlib import Path

config = config.from_env(
    "default",
    keep=True,
    SETTINGS_FILE_FOR_DYNACONF=[
        Path(__file__).parent.joinpath("settings.toml").as_posix()
    ],
)

logger = get_logger()
