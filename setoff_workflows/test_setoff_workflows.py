""" setoff_workflows.py pytest unit tests. Test suite is incomplete
"""

# TODO finish this test suite as it is currently incomplete

from unittest.mock import MagicMock, patch
from setoff_workflows.setoff_workflows import OncoDeepPipeline


def _make_rf_obj(failed_fastqs=None):
    rf_obj = MagicMock()
    rf_obj.runfolder_name = "999999_A01229_0000_00000OKD1"
    rf_obj.masterfile_name = "masterfile.txt"
    rf_obj.DNANEXUS_PROJ_ID = "project-xxx"
    rf_obj.failed_fastqs = failed_fastqs or []
    return rf_obj


def _make_rf_samples(samples):
    rf_samples = MagicMock()
    rf_samples.pipeline = "oncodeep"
    rf_samples.samples_dict = samples
    rf_samples.nexus_runfolder_suffix = "OKD1234"
    return rf_samples


def _sample_dict(sample_name):
    return {
        "panel_settings": {"pipeline": "oncodeep"},
        "fastqs": {
            "R1": {
                "name": f"{sample_name}_R1_001.fastq.gz",
                "nexus_path": f"project-xxx:/fastqs/{sample_name}_R1_001.fastq.gz",
            },
            "R2": {
                "name": f"{sample_name}_R2_001.fastq.gz",
                "nexus_path": f"project-xxx:/fastqs/{sample_name}_R2_001.fastq.gz",
            },
        },
    }


def _get_upload_call_args(mock_sample_cmds_cls):
    return [
        call.args[0]
        for call in mock_sample_cmds_cls.return_value.build_oncodeep_upload_cmd.call_args_list
    ]


@patch("setoff_workflows.setoff_workflows.BuildRunfolderDxCommands")
@patch("setoff_workflows.setoff_workflows.BuildSampleDxCommands")
def test_failed_r1_excludes_both_reads_from_oncodeep_upload(mock_sample_cmds_cls, mock_rf_cmds_cls):
    sample_name = "OKD123_S1"
    rf_obj = _make_rf_obj(failed_fastqs=[f"{sample_name}_R1_001.fastq.gz"])
    rf_samples = _make_rf_samples({sample_name: _sample_dict(sample_name)})

    OncoDeepPipeline(rf_obj, rf_samples, MagicMock())

    called_with = _get_upload_call_args(mock_sample_cmds_cls)
    assert f"{sample_name}-R1" not in called_with
    assert f"{sample_name}-R2" not in called_with


@patch("setoff_workflows.setoff_workflows.BuildRunfolderDxCommands")
@patch("setoff_workflows.setoff_workflows.BuildSampleDxCommands")
def test_failed_r2_excludes_both_reads_from_oncodeep_upload(mock_sample_cmds_cls, mock_rf_cmds_cls):
    sample_name = "OKD123_S1"
    rf_obj = _make_rf_obj(failed_fastqs=[f"{sample_name}_R2_001.fastq.gz"])
    rf_samples = _make_rf_samples({sample_name: _sample_dict(sample_name)})

    OncoDeepPipeline(rf_obj, rf_samples, MagicMock())

    called_with = _get_upload_call_args(mock_sample_cmds_cls)
    assert f"{sample_name}-R1" not in called_with
    assert f"{sample_name}-R2" not in called_with


@patch("setoff_workflows.setoff_workflows.BuildRunfolderDxCommands")
@patch("setoff_workflows.setoff_workflows.BuildSampleDxCommands")
def test_no_failed_fastqs_both_reads_uploaded(mock_sample_cmds_cls, mock_rf_cmds_cls):
    sample_name = "OKD123_S1"
    rf_obj = _make_rf_obj(failed_fastqs=[])
    rf_samples = _make_rf_samples({sample_name: _sample_dict(sample_name)})

    OncoDeepPipeline(rf_obj, rf_samples, MagicMock())

    called_with = _get_upload_call_args(mock_sample_cmds_cls)
    assert f"{sample_name}-R1" in called_with
    assert f"{sample_name}-R2" in called_with
