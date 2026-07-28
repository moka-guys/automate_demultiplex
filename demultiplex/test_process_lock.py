"""
Tests for the process-level demultiplex lock.
"""

import fcntl
from unittest.mock import Mock, call

import pytest

from demultiplex.process_lock import demultiplex_process_lock


def test_process_lock_acquired_without_waiting(tmp_path, monkeypatch):
    logger = Mock()
    flock = Mock()
    monkeypatch.setattr(fcntl, "flock", flock)

    with demultiplex_process_lock(str(tmp_path / "demultiplex.lock"), logger):
        pass

    flock.assert_called_once()
    assert flock.call_args.args[1] == fcntl.LOCK_EX | fcntl.LOCK_NB
    assert "acquired by process" in logger.info.call_args.args[0]


def test_process_lock_logs_and_waits_when_already_held(tmp_path, monkeypatch):
    logger = Mock()
    flock = Mock(side_effect=[BlockingIOError, None])
    monkeypatch.setattr(fcntl, "flock", flock)

    with demultiplex_process_lock(str(tmp_path / "demultiplex.lock"), logger):
        pass

    assert flock.call_args_list == [
        call(flock.call_args_list[0].args[0], fcntl.LOCK_EX | fcntl.LOCK_NB),
        call(flock.call_args_list[1].args[0], fcntl.LOCK_EX),
    ]
    assert "currently running" in logger.info.call_args_list[0].args[0]
    assert "after waiting" in logger.info.call_args_list[1].args[0]


def test_process_lock_released_when_processing_fails(tmp_path):
    lock_file = str(tmp_path / "demultiplex.lock")

    with pytest.raises(RuntimeError):
        with demultiplex_process_lock(lock_file, Mock()):
            raise RuntimeError("processing failed")

    with open(lock_file, "a+", encoding="utf-8") as lock_handle:
        fcntl.flock(lock_handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
