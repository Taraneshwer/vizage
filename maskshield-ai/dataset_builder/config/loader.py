"""
Config loader for MaskShield AI Dataset Builder.

Provides :func:`load_config`, the sole entry-point for reading and
validating the ``config.json`` file into a fully-typed, immutable
:class:`~config.models.AppConfig` instance.

Design decisions
----------------
* The loader is a **pure function** — no global state, no singletons.
  Callers that need a shared config should pass it via dependency injection.
* Validation is performed by Pydantic at load-time.  Any structural or
  semantic error raises :class:`ConfigLoadError` with a human-readable
  message, so startup fails fast rather than silently.
* The default config path points to the ``config/config.json`` file that
  lives alongside this module, making zero-arg usage work out of the box.

Example::

    from config.loader import load_config

    cfg = load_config()                          # uses default path
    cfg = load_config("/path/to/custom.json")    # explicit override
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Final

from pydantic import ValidationError

from config.models import AppConfig

# ---------------------------------------------------------------------------
# Sentinel: default config file path
# ---------------------------------------------------------------------------

_DEFAULT_CONFIG_PATH: Final[Path] = Path(__file__).parent / "config.json"


# ---------------------------------------------------------------------------
# Public exception
# ---------------------------------------------------------------------------


class ConfigLoadError(RuntimeError):
    """Raised when the configuration file cannot be loaded or validated.

    Attributes:
        path: The filesystem path that was attempted.
        reason: A human-readable explanation of the failure.
    """

    def __init__(self, path: Path, reason: str) -> None:
        self.path = path
        self.reason = reason
        super().__init__(f"Failed to load config from '{path}': {reason}")


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def load_config(config_path: str | Path | None = None) -> AppConfig:
    """Load and validate the pipeline configuration from a JSON file.

    The function reads the JSON file at *config_path* (or the bundled
    ``config/config.json`` when *config_path* is ``None``), parses it,
    and validates it against the :class:`~config.models.AppConfig` schema.

    Args:
        config_path: Path to the JSON configuration file.  When ``None``
            the default ``config/config.json`` bundled with this package is
            used.

    Returns:
        A fully validated, immutable :class:`~config.models.AppConfig`
        instance.

    Raises:
        ConfigLoadError: If the file does not exist, is not valid JSON,
            or fails Pydantic validation.

    Example::

        cfg = load_config()
        print(cfg.project.name)
        # → 'MaskShield AI Dataset Builder'
    """
    path = Path(config_path) if config_path is not None else _DEFAULT_CONFIG_PATH

    # ------------------------------------------------------------------ #
    # 1. File existence check
    # ------------------------------------------------------------------ #
    if not path.exists():
        raise ConfigLoadError(path, "File does not exist.")

    if not path.is_file():
        raise ConfigLoadError(path, "Path exists but is not a regular file.")

    # ------------------------------------------------------------------ #
    # 2. JSON parsing
    # ------------------------------------------------------------------ #
    try:
        raw_text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ConfigLoadError(path, f"OS error reading file: {exc}") from exc

    try:
        raw_dict = json.loads(raw_text)
    except json.JSONDecodeError as exc:
        raise ConfigLoadError(
            path,
            f"Invalid JSON at line {exc.lineno}, col {exc.colno}: {exc.msg}",
        ) from exc

    if not isinstance(raw_dict, dict):
        raise ConfigLoadError(path, "Top-level JSON value must be an object.")

    # ------------------------------------------------------------------ #
    # 3. Pydantic validation
    # ------------------------------------------------------------------ #
    try:
        return AppConfig.model_validate(raw_dict)
    except ValidationError as exc:
        # Format pydantic errors into a readable multi-line message.
        error_lines = [
            f"  [{' → '.join(str(loc) for loc in err['loc'])}] "
            f"{err['msg']} (type={err['type']})"
            for err in exc.errors()
        ]
        formatted = "\n".join(error_lines)
        raise ConfigLoadError(
            path,
            f"Schema validation failed with {exc.error_count()} error(s):\n{formatted}",
        ) from exc


def load_config_or_exit(config_path: str | Path | None = None) -> AppConfig:
    """Convenience wrapper around :func:`load_config` that calls ``sys.exit``
    on failure instead of raising, suitable for CLI entry-points.

    Args:
        config_path: Forwarded to :func:`load_config`.

    Returns:
        Validated :class:`~config.models.AppConfig`.
    """
    import sys

    try:
        return load_config(config_path)
    except ConfigLoadError as exc:
        # Print to stderr so it's visible even if stdout is redirected.
        print(f"\n[FATAL] {exc}\n", file=sys.stderr)
        sys.exit(1)
