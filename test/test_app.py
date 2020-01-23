"""Test upload_and_setoff_workflows.py by mocking external calls"""

# This application is not a python package. Add parent directory to path to import modules
import sys
import os
sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir))
)
import automate_demultiplex_config as config
import upload_and_setoff_workflows as uasw
from upload_and_setoff_workflows import RunfolderProcessor
from mocks import MockRunfolderProcessor, mock_rename

def test_app(monkeypatch):
    # Patch rename. Used by SequencingRuns.loop_through_runs()
    monkeypatch.setattr(uasw, "RunfolderProcessor", MockRunfolderProcessor)
    monkeypatch.setattr(os, "rename", mock_rename)

    runs = uasw.SequencingRuns()
    runs.set_runfolders()
    runs.loop_through_runs()
