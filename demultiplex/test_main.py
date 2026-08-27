"""
Tests for demultiplex command-line behavior.
"""

from contextlib import nullcontext
from unittest.mock import Mock

from demultiplex import __main__


def test_scheduled_scan_uses_process_lock(monkeypatch):
    process_lock = nullcontext()
    lock_factory = Mock(return_value=process_lock)
    monkeypatch.setattr(__main__, "demultiplex_process_lock", lock_factory)

    assert __main__.get_process_lock(None) is process_lock
    lock_factory.assert_called_once_with(
        __main__.DemultiplexConfig.PROCESS_LOCK_FILE,
        __main__.root_logger,
    )


def test_targeted_manual_run_does_not_use_process_lock(monkeypatch):
    lock_factory = Mock()
    monkeypatch.setattr(__main__, "demultiplex_process_lock", lock_factory)

    with __main__.get_process_lock("runfolder"):
        pass

    lock_factory.assert_not_called()
