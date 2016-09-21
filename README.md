# Automated demultiplexing
These files are scheduled to run (via cronjob) on the workstation attached to the nextseq

# demultiplex.py
This script loops through all the runs in the runfolder share and identifies any runs that:
 1. sequencing has finished (looking for presence of RTAcomplete.txt)
 2. has not already been demultiplexed (demultiplex_log.txt is not present)
 3. sample_sheet is present in the sample_sheets folder matching the name of the run.
 
If all 3 points are satisfied bcl2fastq is run.
 
The output is written to a log file and the last line of the log file checked to see if the run was successful or not.
 
#future plans
1. A report will be emailed depending on the success
2. A second script to upload the finished project to DNA nexus.
