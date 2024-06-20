# Set Off Workflows

[setoff_workflows.py](setoff_workflows.py) handles the DNAnexus workflow / app execution for demultiplexed NGS runs. The script consists of multiple classes:
* SequencingRuns() - Collects sequencing runs and initiates runfolder processing for those sequencing runs requiring processing. Calls:
    - ProcessRunfolder() - A new instance of this class is initiated for each runfolder being assessed. Calls methods to process and upload a runfolder including creation of DNAnexus project, upload of data using upload_runfolder, building and execution of dx run commands to set off sample workflows and apps, creation of decision support tool upload scripts, and sending of pipeline emails. Calls:
        * CollectRunfolderSamples() - Collect attributes for all samples within the runfolder. Calls:
            - SampleObject() - Collect sample-specific attributes for a sample
        * BuildDxCommands() - Build run-wide commands for runfolder, and write sample-level commands from the samples_obj along with the run-wide commands to the dx run script
        * PipelineEmails() - Class for sending the start of pipeline emails. Calls the AdEmail class for email sending. The following emails are sent:
            - SQL emails for all pipelines, to binfx team
            - Emails with details of the samples being processed. Sent to binfx for all runs, plus to additional recipients as defined within the config.ad_config file

## Protocol

1. Identify runfolders in the runfolders directory which have not been processed:
    - Runfolder contains bcl2fastq2 log file with success string
    - Runfolder does not contain upload started flag file
2. Collect names and metadata for all samples in the runfolder
3. Write and run the DNAnexus project creation script
4. Split tso500 SampleSheet into parts with x samples per SampleSheet (no.defined in TSO_BATCH_SIZE) and write to runfolder
5. Carry out pre-pipeline file upload (cluster density files, bcl2fastq2 QC files, fastqs if not a tso run, SampleSheet and entire runfolder if a tso run)
6. Build and populate DNAnexus commands bash script
7. Build and populate post run commands bash script if a TSO run
8. Create decision support commands bash script (contains the commands to run the Congenica upload app if custom panels, LRPCR, or WES run, and contains the commands to run the Qiagen upload app if TSO run). This is set off manually after QC inspection
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
| decision_support_upload_cmds | Records the dx run commands to set off the decision support upload apps. N.B. this is not written to by logging | `RUNFOLDERNAME_decision_support.sh` | `/usr/local/src/mokaguys/automate_demultiplexing_logfiles/dx_run_commands` |
| proj_creation_script | Records the commands for creating the DNAnexus project. N.B. this is not written to by logging | `RUNFOLDERNAME_create_nexus_project.sh` | `/usr/local/src/mokaguys/automate_demultiplexing_logfiles/dx_run_commands` |

## Testing

**N.B. Tests and test cases/files MUST be maintained and updated accordingly in conjunction with script development**

This script does not yet have a test suite.

