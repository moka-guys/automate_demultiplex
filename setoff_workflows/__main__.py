"""
Collect sequencing runs and initiate runfolder processing for those sequencing runs requiring processing.
SequencingRuns calls further classes ProcessRunfolder which calls CollectRunfolderSamples (which calls SampleObject
per sample), BuildDxCommands which generates the dx run commands, and PipelineEmails which generates
and sends the pipeline emails using ad_email.AdEmail
"""
from setoff_workflows import setoff_workflows
from toolbox import toolbox
from ad_logger import ad_logger


sequencing_runs = setoff_workflows.SequencingRuns()

toolbox.script_start_logmsg(sequencing_runs.script_logger, __file__)

sequencing_runs.setoff_processing()

toolbox.script_end_logmsg(sequencing_runs.script_logger, __file__)

ad_logger.shutdown_logs(sequencing_runs.script_logger)
