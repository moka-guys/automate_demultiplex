# Automated demultiplexing
These files are scheduled to run (via cronjob) on the workstation attached to the nextseq and miseqs.

The crontab.txt file contains the cron jobs that are executed (as the root user). Add/edit with `sudo crontab -e`.

# demultiplex.py
This script loops through all the runs in the runfolder share and identifies any runs that:
 1. sequencing has finished (looking for presence of RTAcomplete.txt)
 2. has not already been demultiplexed (demultiplexlog.txt is not present)
 3. sample_sheet is present in the sample_sheets folder matching the name of the run.

If all 3 points are satisfied bcl2fastq is run.

The output is written to a log file and the last line of the log file checked to see if the run was successful or not.

Two log files are written to. One is the 'cron job' log, recording the outcome for each run folder each time the script is run.
If demultiplexing is initiated, a log file is created to record the stdout and stderr of bcl2fastq.

Email notifications are sent to the Moka Guys mailing list in the event of a bcl2fastq failure.

# DNA_Nexus_upload_agent.py
This script looks for newly demultiplexed runs and initiates the upload of the run folder to DNA Nexus using the upload agent
An email is sent upon completion.

# automate_demultiplex_config.py
This module contains configuration settings which are imported and used by the demultiplex.py and DNA_Nexus_upload_agent.py scripts. 
