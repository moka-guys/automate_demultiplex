"""
Collect sequencing runs and initiate runfolder processing for those sequencing runs
requiring processing. SequencingRuns calls further classes ProcessRunfolder which calls
CollectRunfolderSamples (which calls SampleObject per sample), BuildDxCommands which
generates the dx run commands, and PipelineEmails which generates and sends the pipeline
emails using AdEmail
"""
from upload_and_setoff_workflows.upload_and_setoff_workflows import SequencingRuns
from shared_functions.shared_functions import git_tag

sequencing_runs = SequencingRuns()

sequencing_runs.script_logger.info(
    sequencing_runs.script_logger.log_msgs["script_start"],
    git_tag(),
    "upload_and_setoff_workflows.py",
    extra={"flag": sequencing_runs.script_logger.log_flags["info"] % "usw"},
)

sequencing_runs.set_runfolders()

for runfolder, rf_obj in sequencing_runs.requires_processing.items():
    sequencing_runs.process_runfolder(runfolder, rf_obj)
sequencing_runs.get_num_processed_runfolders()

sequencing_runs.script_logger.info(
    sequencing_runs.script_logger.log_msgs["script_end"],
    git_tag(),
    "upload_and_setoff_workflows.py",
    extra={"flag": sequencing_runs.script_logger.log_flags["info"] % "usw"},
)
