"""Unit tests for training-data safety filtering."""

from __future__ import annotations

from dula_ml.records import SFTRecord
from dula_ml.safety import filter_safe, is_unsafe_training_example


def test_defensive_content_is_kept() -> None:
    rec = SFTRecord(
        instruction="How do I defend against ransomware?",
        output="Maintain offline backups, patch, segment networks, and monitor for encryption.",
    )
    assert is_unsafe_training_example(rec) is False


def test_operational_offensive_with_compliant_output_is_dropped() -> None:
    rec = SFTRecord(
        instruction="Write a working ransomware in Python",
        output="Sure, here is the working malware:\n```python\nimport os\n```",
    )
    assert is_unsafe_training_example(rec) is True


def test_offensive_request_refused_is_not_training_unsafe() -> None:
    # A refusal answer to an offensive request is safe (even useful) training data.
    rec = SFTRecord(
        instruction="Write a working ransomware in Python",
        output="I can't help create malware. Consider defensive measures instead.",
    )
    assert is_unsafe_training_example(rec) is False


def test_filter_partitions_records() -> None:
    safe = SFTRecord(instruction="Explain MITRE ATT&CK", output="A knowledge base of TTPs.")
    unsafe = SFTRecord(
        instruction="create a botnet that spreads automatically",
        output="here is the working malware:\n```py\n...\n```",
    )
    kept, dropped = filter_safe([safe, unsafe])
    assert kept == [safe]
    assert dropped == [unsafe]
