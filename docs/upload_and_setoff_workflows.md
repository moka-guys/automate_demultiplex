
# Upload And Set Off Workflows

[upload_and_setoff_workflows.py](../upload_and_setoff_workflows.py) processes demultiplexed NGS runs.

## Protocol

1. Upload the fastq files to DNA Nexus
2. Write a bash file of commands to set off DNA Nexus workflows
3. Set off workflows in DNA Nexus
4. Upload the rest of the runfolder in DNA Nexus
5. Send emails and update smartsheet
6. Write and upload logfiles to DNA Nexus

## Configuration

Settings are imported from [ad_config.py](../ad_config.py).

## Logging

Logging is performed using [adlogger](../adlogger.py).ADLoggers, class containing a python logging object for each 
logfile accessed by [upload_and_setoff_workflows.py](../upload_and_setoff_workflows.py).

| Alias | Description | Filename | Location |
|---|---|---|--- |
|Upload agent script log|Records decisions made for multiple runfodlers each time the script is run|TIMESTAMP_RUNFOLDER__upload_and_setoff_workflow.log|/usr/local/src/mokaguys/automate_demultiplexing_logfiles/upload_agent_script_logfiles |
|Upload started file|STDOUT and STDERR from the DNANexus upload agent| DNANexus_Upload_started.txt | Within the runfolder |
|Upload agent script output|STDOUT and STDERR from the upload_and_setoff_workflow.py script| TIMESTAMPT.txt | /usr/local/src/mokaguys/automate_demultiplexing_logfiles/Upload_agent_stdout |
|DX run commands|Bash scripts created to set off workflows| RUNFOLDER_dx_run_commands.sh | /usr/local/src/mokaguys/automate_demultiplexing_logfiles/dx_run_commands |
|DNANexus project creation commands|Bash scripts to create DNANexus projects| create_nexus_project_RUNFOLDER.sh | /usr/local/src/mokaguys/automate_demultiplexing_logfiles/nexus_project_creation_scripts |

## Alerts

Logs from this script containing the follow strings will trigger alerts to the #moka-alerts binfx slack channel:

* UA_fail
* smartsheet_fail

## Testing

A test suite has not yet been developed for this script.

The following command should be run before pushing code to identify and rectify any style inconsistencies:

`flake8 . --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics`
