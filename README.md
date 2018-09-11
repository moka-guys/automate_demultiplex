# Automated demultiplexing
These files are scheduled to run (via cronjob) on the workstation attached to the nextseq and miseqs.

The crontab.txt file contains the cron jobs that are executed (as the root user). Add/edit with `sudo crontab -e`.

# automate_demultiplex_config.py
This module contains configuration settings which are imported and used by the demultiplex.py and DNA_Nexus_upload_agent.py scripts. 

# demultiplex.py
This script loops through all the runs in the runfolder share and identifies any runs that:
 1. sequencing has finished (looking for presence of RTAcomplete.txt)
 2. has not already been demultiplexed (demultiplexlog.txt is not present)
 3. sample_sheet is present in the sample_sheets folder matching the name of the run.


If all 3 points are satisfied a data integrity check is performed to compare integrity of data on workstation and sequencer. (md5checksums are calculated on the nextseq, whereas the md5checksums are calculated by this script for miseq runs)

If the integrity check passes bcl2fastq (v2.20) is run.

The output is written to a log file and the last line of the log file checked to see if the run was successful or not.

#### Log files include : 
1. "demultiplex_script_log" (named with a timestamp and any runfolders demultiplexed in that run)- records the decisions made each time the script is run (contains information from multiple run folders). This can be found in /home/mokaguys/Documents/automate_demultiplexing_logfiles/Demultiplexing_log_files
2. demultiplexlog.txt - contains the stdout and stderr of bcl2fastq. This can be found in the runfolder
3. demultiplex standard err/out - records the standard error and out from the demultiplexing script - will record any errors from the cron job. Can be found in /home/mokaguys/Documents/automate_demultiplexing_logfiles/Demultiplexing_stdout named with the timestamp

#### Alerts
Alerts are sent to the Moka-Alerts Slack channel , or in the event of a critical failure, such as integrity check failing via email to the moka-guys mailing list.

# DNA_Nexus_upload_agent.py
This script looks for newly demultiplexed runs, uploads the fastq files, builds and executes the dx run commands to set off the workflows in DNA Nexus before archiving the rest of the runfolder in DNA Nexus.

#### Log files include:
1. "upload_agent_script_log" (named with a timestamp and any runfolders processed in that run)- records the decisions made each time the script is run (contains information from multiple run folders). Can be found at /home/mokaguys/Documents/automate_demultiplexing_logfiles/upload_agent_script_logfiles
2. DNANexus_Upload_started.txt - contains the standard err and standard out from the upload agent. - this can be found in the run folder
3. Upload agent script standard err/out - records the standard error and out from cronjob when executing the script. Can be found in /home/mokaguys/Documents/automate_demultiplexing_logfiles/Upload_agent_stdout
4. bash scripts created by the script detailing
* dx run commands (/home/mokaguys/Documents/automate_demultiplexing_logfiles/dx_run_commands)
* DNA Nexus project creation commands (/home/mokaguys/Documents/automate_demultiplexing_logfiles/nexus_project_creation_scripts)

#### Alerts
Alerts are sent to Moka-Alerts slack channel

