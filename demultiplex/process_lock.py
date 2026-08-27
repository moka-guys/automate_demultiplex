"""
Process-level locking for demultiplex invocations.
"""

import fcntl
import os
from contextlib import contextmanager
from typing import Iterator, TextIO


@contextmanager
def demultiplex_process_lock(lock_file: str, logger: object) -> Iterator[None]:
    """
    Allow only one demultiplex process to run at a time.

    Try the lock without blocking first so contention can be logged, then wait
    for the active process to finish. Closing the file releases the lock,
    including when processing raises an exception.
    """
    lock_handle: TextIO = open(lock_file, "a+", encoding="utf-8")
    try:
        try:
            fcntl.flock(lock_handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            logger.info(
                "Another demultiplex process is currently running; waiting for "
                "the process lock: %s",
                lock_file,
            )
            fcntl.flock(lock_handle, fcntl.LOCK_EX)
            logger.info("Demultiplex process lock acquired after waiting")
        else:
            logger.info(
                "Demultiplex process lock acquired by process %s", os.getpid()
            )

        yield
    finally:
        lock_handle.close()
