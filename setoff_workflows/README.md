# Set Off Workflows

The setoff_workflows module handles the DNAnexus workflow / app execution for demultiplexed NGS runs. The module contains
multiple scripts:

| Script | Class | Functionality|
|--------|--------|---------------|
|[setoff_workflows.py](setoff_workflows.py)| SequencingRuns | Collects sequencing runs and initiates runfolder processing for those sequencing runs requiring processing |
| [setoff_workflows.py](setoff_workflows.py) | ProcessRunfolder | A new instance of this class is initiated by the SequencingRuns class for each runfolder being assessed. Calls methods to process and upload a runfolder including creation of DNAnexus project, upload of data using upload_runfolder, building and execution of dx run commands to set off sample workflows and apps, creation of decision support tool upload scripts, and sending of pipeline emails |
|[setoff_workflows.py](setoff_workflows.py) | Pipeline-specific classes (DevPipeline, ArcherDxPipeline, SnpPipeline, OncoDeepPipeline, TsoPipeline, WesPipeline, CustomPanelsPipeline), which collate lists of commands for each runtype by calling the  imported BuildRunfolderDxCommands, BuildSampleDxCommands and PipelineEmails classes. |
| [build_dx_commands.py](build_dx_commands.py)| BuildRunfolderDxCommands | Builds dx run commands that are at the runfolder level, for example MultiQC, TSO500 app, peddy, per-sample queries (e.g. WES). |
| [build_dx_commands.py](build_dx_commands.py)| BuildSampleDxCommands| Builds dx run commands that are at the sample level,
for example per-sample workflow commands, coverage commands, decision support upload commands, per-sample queries.
| [pipeline_emails.py](pipeline_emails.py)| PipelineEmails | Sends the start of pipeline emails. It calls the [AdEmail](../ad_email/ad_email.py) class for email sending, and sends the pipeline started email (contains SQL queries used to update the Moka database), and the samples being processed email |

The module uses various functions and classes from the [Toolbox module](../toolbox/toolbox.py).


## Protocol

1. Identify runfolders in the runfolders directory which have not been processed:
    - Runfolder contains bclconvert log file with success string
    - Runfolder does not contain upload started flag file (has not yet been uploaded to DNAnexus)
2. Collect names and metadata for all samples in the runfolder, using the RunfolderSamples() class from the [Toolbox module](../toolbox/toolbox.py).
3. Write and run the DNAnexus project creation script
4. Split tso500 SampleSheet into parts with x samples per SampleSheet (no.defined in TSO_BATCH_SIZE) and write to runfolder
5. Generate the pre-pipeline upload commands (cluster density files, bclconvert QC files, logfiles, fastqs if not a tso run, SampleSheets, MasterFile if an oncodeep run)
6. Generate the SQL queries
7. Set off the pre-pipeline file upload, and the rest of the runfolder upload in addition to this if the run is a TSO run
8. Build dx run commands and write these to the DNAnexus commands bash scripts:
- Dx run script - contains most dx run commands for all runs
- Postprocessing script - contains downstream app commands for TSO500 runs and is manually run upon pipeline completion (this is due to issues with the TSO500 pipeline app not having named file outputs which means file dependency does not work)
- Decision support upload script - contains the commands to run the Congenica upload app (custom panels, LRPCR, WES), Qiagen upload app (TSO), or OncoDEEP upload app (OncoDEEP), if required. These are set off manually after QC inspection, apart from OncoDEEP which is an automated upload
9. Run DNAnexus commands bash script (sets off workflows / apps in DNAnexus)
10. Send pipeline emails (Send SQL queries email, and samples being processed email)
11. Carry out the post-pipeline file upload (rest of the runfolder, and the logfiles)

## Configuration

Settings are imported from [ad_config.py](../config/ad_config.py) and [panel_config.py](../config/panel_config.py).

## Usage

The module can be used either from the command line or as a module import:

```bash
python3 -m setoff_workflows
```

```python
from setoff_workflows.setoff_workflows import SequencingRuns

set_root_logger()

sequencing_runs = SequencingRuns()
sequencing_runs.setoff_processing()
```

## Logging

Logging is performed using [ad_logger](../ad_logger/ad_logger.py).

| Alias | Description | Filename | Location |
| ------------------ | ------------------------------------------------------------------------------ | ----------------------------------------------------- | ---------------------------------------------------------------------------------- |
| Setoff workflows output | Catches any traceback from errors when running the cron job that are not caught by exception handling within the script | `TIMESTAMP.txt` | `/usr/local/src/mokaguys/automate_demultiplexing_logfiles/Setoff_workflows_cron_stdout` |
| sw (script_loggers) | Records script-level logs for the setoff workflows script | `TIMESTAMP_setoff_workflow.log` | `/usr/local/src/mokaguys/automate_demultiplexing_logfiles/sw_script_logfiles/` |
| sw (rf_loggers["sw"]) | Records runfolder-level logs for the setoff workflows script | `RUNFOLDERNAME_setoff_workflow.log` | `/usr/local/src/mokaguys/automate_demultiplexing_logfiles/sw_script_logfiles/` |
| dx_run_script | Records the dx run commands for processing the run. N.B. this is not written to by logging | `RUNFOLDERNAME_dx_run_commands.sh` | `/usr/local/src/mokaguys/automate_demultiplexing_logfiles/dx_run_commands` |
| decision_support_upload_cmds | Records the dx run commands to set off the Congenica upload apps. N.B. this is not written to by logging | `RUNFOLDERNAME_decision_support.sh` | `/usr/local/src/mokaguys/automate_demultiplexing_logfiles/dx_run_commands` |
| proj_creation_script | Records the commands for creating the DNAnexus project. N.B. this is not written to by logging | `RUNFOLDERNAME_create_nexus_project.sh` | `/usr/local/src/mokaguys/automate_demultiplexing_logfiles/dx_run_commands` |

## Testing

**N.B. Tests and test cases/files MUST be maintained and updated accordingly in conjunction with script development**

This script does not yet have a test suite.

