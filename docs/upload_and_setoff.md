
# Upload and Set Off Workflows

`upload_and_setoff_workflows.py` processes demultiplexed NGS runs.

## Protocol

1. Upload the fastq files to DNA Nexus
1. Write a bash file of commands to set off DNA Nexus workflows
1. Set off workflows in DNA Nexus
1. Upload the rest of the runfolder in DNA Nexus
1. Send emails and update smartsheet
1. Write and upload logfiles to DNA Nexus


## Configuration

Settings are imported from `automate_demultiplex_config.py`.

## Logging
TODO!
1. "upload_agent_script_log" (named with a timestamp and any runfolders processed in that run)- records the decisions made each time the script is run (contains information from multiple run folders). Can be found at /usr/local/src/mokaguys/automate_demultiplexing_logfiles/upload_agent_script_logfiles
2. DNANexus_Upload_started.txt - contains the standard err and standard out from the upload agent. - this can be found in the run folder
3. Upload agent script standard err/out - records the standard error and out from cronjob when executing the script. Can be found in /usr/local/src/mokaguys/automate_demultiplexing_logfiles/Upload_agent_stdout
4. bash scripts created by the script detailing
* dx run commands (/usr/local/src/mokaguys/automate_demultiplexing_logfiles/dx_run_commands)
* DNA Nexus project creation commands (/usr/local/src/mokaguys/automate_demultiplexing_logfiles/nexus_project_creation_scripts)

## Alerts TODO
## Alerts

Logs from this script containing the follow strings will trigger alerts to the #moka-alerts binfx slack channel:

* demultiplex_fail
* smartsheet_fail
