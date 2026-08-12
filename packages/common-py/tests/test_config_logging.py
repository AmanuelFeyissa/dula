"""Tests for common settings and JSON logging."""

from __future__ import annotations

import json
import logging

import pytest
from dula_common.config import CommonSettings
from dula_common.logging import configure_logging


def test_settings_defaults_and_env(monkeypatch: pytest.MonkeyPatch) -> None:
    assert CommonSettings().env == "dev"
    monkeypatch.setenv("DULA_ENV", "staging")
    monkeypatch.setenv("DULA_LOG_LEVEL", "DEBUG")
    settings = CommonSettings()
    assert settings.env == "staging"
    assert settings.log_level == "DEBUG"


def test_json_logging_emits_structured_line(capsys: pytest.CaptureFixture[str]) -> None:
    configure_logging("INFO")
    logging.getLogger("test").info("hello", extra={"tenant_id": "tenant-a"})
    err = capsys.readouterr().err.strip().splitlines()[-1]
    record = json.loads(err)
    assert record["message"] == "hello"
    assert record["level"] == "INFO"
    assert record["tenant_id"] == "tenant-a"
