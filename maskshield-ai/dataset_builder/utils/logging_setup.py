"""
Loguru logging setup for MaskShield AI Dataset Builder.

Provides :func:`configure_logging`, the single entry-point that
configures Loguru's sink chain for the application.

Design
------
* **No global logger reassignment** — callers import ``logger`` from
  ``loguru`` directly; this module only configures the sinks.
* **Two sinks** — coloured stderr for interactive use, rotating JSON
  file for machine-readable archival.
* **Dependency-injected config** — the function accepts the
  :class:`~config.models.AppConfig` so no global config is needed.
* **Idempotent** — calling :func:`configure_logging` multiple times
  removes previously added sinks first, so tests can reconfigure safely.

Example::

    from config.loader import load_config
    from utils.logging_setup import configure_logging
    from loguru import logger

    cfg = load_config()
    configure_logging(cfg)
    logger.info("Pipeline started.")
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import TYPE_CHECKING

from loguru import logger

if TYPE_CHECKING:
    from config.models import AppConfig

                                                                             
                                                              
                                                                       
                                                                             

_ACTIVE_SINK_IDS: list[int] = []

                                                                             
                    
                                                                             

_CONSOLE_FORMAT: str = (
    "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
    "<level>{level: <8}</level> | "
    "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> — "
    "<level>{message}</level>"
)

_FILE_FORMAT: str = (
    "{time:YYYY-MM-DD HH:mm:ss.SSS} | "
    "{level: <8} | "
    "{name}:{function}:{line} — "
    "{message}"
)

                                                 
_LOG_ROTATION_SIZE: str = "10 MB"

                                
_LOG_RETENTION: str = "5 files"


                                                                             
            
                                                                             


def configure_logging(cfg: AppConfig) -> None:
    """Configure Loguru sinks for the dataset builder pipeline.

    Removes any previously registered sinks added by this function
    (idempotent), then adds:

    1. **Console sink** — coloured, human-readable output to ``stderr``.
    2. **File sink** — rotating plain-text log in the configured log
       directory, named ``dataset_builder.log``.

    The log level for both sinks is taken from
    ``cfg.project.log_level`` (default ``"DEBUG"``).

    Args:
        cfg: Validated :class:`~config.models.AppConfig` instance.

    Example::

        configure_logging(load_config())
        logger.success("Logging is ready.")
    """
    global _ACTIVE_SINK_IDS                                               

                                                                   
    for sink_id in _ACTIVE_SINK_IDS:
        try:
            logger.remove(sink_id)
        except ValueError:
            pass                                   
    _ACTIVE_SINK_IDS.clear()

    level = cfg.project.log_level.upper()
    log_dir = Path(cfg.paths.log_dir)
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "dataset_builder.log"

                                         
    console_id = logger.add(
        sys.stderr,
        level=level,
        format=_CONSOLE_FORMAT,
        colorize=True,
        backtrace=True,
        diagnose=True,
        enqueue=False,
    )
    _ACTIVE_SINK_IDS.append(console_id)

                                       
    file_id = logger.add(
        str(log_file),
        level=level,
        format=_FILE_FORMAT,
        rotation=_LOG_ROTATION_SIZE,
        retention=_LOG_RETENTION,
        compression="gz",
        backtrace=True,
        diagnose=False,                                              
        enqueue=True,                                    
        encoding="utf-8",
    )
    _ACTIVE_SINK_IDS.append(file_id)

    logger.debug(
        "Logging configured: level={level}, log_file={log_file}",
        level=level,
        log_file=log_file,
    )


def configure_logging_minimal(level: str = "DEBUG") -> None:
    """Lightweight log configuration for CLI scripts that do not yet have
    a full :class:`~config.models.AppConfig` (e.g. during ``--help``).

    Only adds a console sink.

    Args:
        level: Loguru level string.
    """
    global _ACTIVE_SINK_IDS                 

    for sink_id in _ACTIVE_SINK_IDS:
        try:
            logger.remove(sink_id)
        except ValueError:
            pass
    _ACTIVE_SINK_IDS.clear()

    sink_id = logger.add(
        sys.stderr,
        level=level.upper(),
        format=_CONSOLE_FORMAT,
        colorize=True,
        backtrace=True,
        diagnose=True,
    )
    _ACTIVE_SINK_IDS.append(sink_id)
