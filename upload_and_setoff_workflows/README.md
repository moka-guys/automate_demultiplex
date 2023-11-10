# Upload And Set Off Workflows

[upload_and_setoff_workflows.py](../upload_and_setoff_workflows.py) handles the DNAnexus workflow / app execution for demultiplexed NGS runs.

## Protocol

1. Identify runfolders in the runfolders directory which have not been processed
2. Collect names and metadata for all samples in the runfolder
3. Write and run the DNAnexus project creation script
4. Carry out pre-pipeline file upload (cluster density files, bcl2fastq2 QC files, fastqs if not a tso run, samplesheet and entire runfolder if a tso run)
5. Build and populate dnanexus commands bash script
6. Create congenica commands bash script (contains the commands to run the congenica upload app, this is set off later manually after QC inspection)
7. Run dnanexus commands bash script (sets off workflows / apps in DNAnexus)
8. Send pipeline emails (Send SQL queries email, and samples being processed email)
9. Carry out the post-pipeline file upload (rest of the runfolder, and the logfiles)

## Configuration

Settings are imported from [ad_config.py](../config/ad_config.py) and [panel_config.py](../config/panel_config.py).

## Usage

## Logging

Logging is performed using [ad_logger](../ad_logger/ad_logger.py).

| Alias | Description | Filename | Location |
| ------------------ | ------------------------------------------------------------------------------ | ----------------------------------------------------- | ---------------------------------------------------------------------------------- |
| Upload and setoff workflows output | Catches any traceback from errors when running the cron job that are not caught by exception handling within the script | `TIMESTAMP.txt` | `/usr/local/src/mokaguys/automate_demultiplexing_logfiles/Upload_agent_stdout` |
| usw (script_loggers) | Records script-level logs for the upload and setoff workflows script | `TIMESTAMP_upload_and_setoff_workflow.log` | `/usr/local/src/mokaguys/automate_demultiplexing_logfiles/usw_script_logfiles/` |
| usw (script_loggers) | Records runfolder-level logs for the upload and setoff workflows script | `RUNFOLDERNAME_upload_and_setoff_workflow.log` | `/usr/local/src/mokaguys/automate_demultiplexing_logfiles/usw_script_logfiles/` |
| upload_agent | Records upload agent logs (stdout and stderr of the upload agent) | `DNANexus_upload_started.txt` |  Within the runfolder |
| dx_run_script | Records the dx run commands for processing the run. N.B. this is not written to by logging | `RUNFOLDERNAME_dx_run_commands.sh` | `/usr/local/src/mokaguys/automate_demultiplexing_logfiles/dx_run_commands` |
| decision_support_upload_cmds | Records the dx run commands to set off the congenica upload apps. N.B. this is not written to by logging | `RUNFOLDERNAME_congenica.sh` | `/usr/local/src/mokaguys/automate_demultiplexing_logfiles/dx_run_commands` |
| proj_creation_script | Records the commands for creating the DNAnexus project. N.B. this is not written to by logging | `create_nexus_project_RUNFOLDERNAME.sh` | `/usr/local/src/mokaguys/automate_demultiplexing_logfiles/nexus_project_creation_scripts` |

## Alerts

Logs from this script containing the follow strings will trigger alerts to the #moka-alerts binfx slack channel:

* USW_FAIL

## Testing

**N.B. Tests and test cases/files MUST be maintained and updated accordingly in conjunction with script development**

This script does not yet have a test suite.

