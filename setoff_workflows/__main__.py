"""
Collect sequencing runs and initiate runfolder processing for those sequencing runs requiring processing.
SequencingRuns calls further classes ProcessRunfolder which calls CollectRunfolderSamples (which calls SampleObject
per sample), BuildDxCommands which generates the dx run commands, and PipelineEmails which generates
and sends the pipeline emails using ad_email.AdEmail
"""
from setoff_workflows.setoff_workflows import SequencingRuns
from toolbox.toolbox import script_start_logmsg, script_end_logmsg
from ad_logger.ad_logger import shutdown_logs


sequencing_runs = SequencingRuns()

script_start_logmsg(sequencing_runs.script_logger, __file__)

sequencing_runs.setoff_processing()

script_end_logmsg(sequencing_runs.script_logger, __file__)

shutdown_logs(sequencing_runs.script_logger)
