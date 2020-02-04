
# DNA_Nexus_upload_agent.py
This script looks for newly demultiplexed runs, uploads the fastq files, builds and executes the dx run commands to set off the workflows in DNA Nexus before archiving the rest of the runfolder in DNA Nexus.

#### Log files include:
1. "upload_agent_script_log" (named with a timestamp and any runfolders processed in that run)- records the decisions made each time the script is run (contains information from multiple run folders). Can be found at /usr/local/src/mokaguys/automate_demultiplexing_logfiles/upload_agent_script_logfiles
2. DNANexus_Upload_started.txt - contains the standard err and standard out from the upload agent. - this can be found in the run folder
3. Upload agent script standard err/out - records the standard error and out from cronjob when executing the script. Can be found in /usr/local/src/mokaguys/automate_demultiplexing_logfiles/Upload_agent_stdout
4. bash scripts created by the script detailing
* dx run commands (/usr/local/src/mokaguys/automate_demultiplexing_logfiles/dx_run_commands)
* DNA Nexus project creation commands (/usr/local/src/mokaguys/automate_demultiplexing_logfiles/nexus_project_creation_scripts)

#### Alerts
Alerts are sent to Moka-Alerts slack channel

