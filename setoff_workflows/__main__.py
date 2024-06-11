"""
Collect sequencing runs and initiate runfolder processing for those sequencing runs requiring processing.
SequencingRuns calls further classes ProcessRunfolder which calls CollectRunfolderSamples (which calls SampleObject
per sample), BuildDxCommands which generates the dx run commands, and PipelineEmails which generates
and sends the pipeline emails using ad_email.AdEmail
"""

from setoff_workflows.setoff_workflows import SequencingRuns
from ad_logger.ad_logger import set_root_logger


set_root_logger()

sequencing_runs = SequencingRuns()

sequencing_runs.setoff_processing()
