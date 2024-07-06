"""
SequencingRuns collects sequencing runs and initiate runfolder processing for those sequencing runs requiring processing.
SequencingRuns calls the ProcessRunfolder class which calls further pipeline-specific classes
(DevPipeline, ArcherDxPipeline, SnpPipeline, OncoDeepPipeline, TsoPipeline, WesPipeline, CustomPanelsPipeline).
These call the BuildRunfolderDxCommands, BuildSampleDxCommands and PipelineEmails classes to build the commands
and emails specific to each pipeline.

BuildRunfolderDxCommands builds dx run commands that are at the runfolder level, for example MultiQC, TSO500
app, peddy, per-sample queries (e.g. WES). BuildSampleDxCommands builds dx run commands that are at the sample level,
for example per-sample workflow commands, coverage commands, decision support upload commands, per-sample queries.
and PipelineEmails generates and sends the pipeline emails (SQL emails and samples emails) using ad_email.AdEmail
"""

from setoff_workflows.setoff_workflows import SequencingRuns
from ad_logger.ad_logger import set_root_logger

set_root_logger()

sequencing_runs = SequencingRuns()

sequencing_runs.setoff_processing()
