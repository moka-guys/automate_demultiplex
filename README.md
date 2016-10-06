# Automated demultiplexing
These files are scheduled to run (via cronjob) on the workstation attached to the nextseq

# demultiplex.py
This script loops through all the runs in the runfolder share and identifies any runs that:
 1. sequencing has finished (looking for presence of RTAcomplete.txt)
 2. has not already been demultiplexed (demultiplex_log.txt is not present)
 3. sample_sheet is present in the sample_sheets folder matching the name of the run.
 
If all 3 points are satisfied bcl2fastq is run.

The output is written to a log file and the last line of the log file checked to see if the run was successful or not.

Two log files are written to. One is the 'cron job' log, recording the outcome for each run folder each time the script is run.
If the demultiplexing is initiated a log file is created to record the stdout or stderr of bcl2fastq.

Email notifications are sent to say demultiplexing has started and one upon completion reporting success or failure (after readingt the log file).

# DNA_Nexus_upload_agent.py
This script looks for newly demultiplexed runs and initiates the upload of the run folder to DNA Nexus using the upload agent
An email is sent upon completion.
