'''

'''
debug=True
### location of in/output files
# path to run folders
runfolders = "/media/data1/share"

# path to fastq files
fastq_folder = "Data/Intensities/BaseCalls"

# name of file which denotes demultiplexing is underway/complete
demultiplexed = "demultiplexlog.txt"

# path to log file which records the output of the upload agent
upload_agent_logfile = "/home/mokaguys/Documents/automate_demultiplexing_logfiles/Upload_agent_log/"

# name of log file which records the output of the upload agent
upload_started_file = "DNANexus_upload_started.txt"

# Path to DNA Nexus run command log file
DNA_Nexus_workflow_logfolder = "/home/mokaguys/Documents/automate_demultiplexing_logfiles/DNA_Nexus_workflow_logs/"


### DNA Nexus settings
# project to upload run folder into
NexusProject="NGS_runs"
# The project containing the app and data
app_project="001_ToolsReferenceData:"
#path to the workflow in the app project
workflow_path="Workflows/GATK3.5_v2.3"
# bedfile folder
bedfile_folder="Data/Bed/"

###istages
fastqc1 = " -istage-Bz3YpP80jy1Y1pZKbZ35Bp0x.reads=" # FastQC Read 1
fastqc2 = " -istage-Bz3YpP80jy1x7G5QfG3442gX.reads=" # FastQC Read 2
bwa_fastq1 = " -istage-Byz9BJ80jy1k2VB9xVXBp0Fg.reads_fastqgz=" # BWAFastQ Read1
bwa_fastq2 = " -istage-Byz9BJ80jy1k2VB9xVXBp0Fg.reads2_fastqgz=" # BWA FastQ Read2
samb_bed = " -istage-XXX=" # Sambamba Bed file
HSMetrics_bed = " -istage-YYY=" # HSMetrics Bed file
HC_bed = " -istage-ZZZ=" # GATK HC Bed file
        
# DNA Nexus authentication token
Nexus_API_Key = "rsivxAMylcfpHvIIcZy8hDsFUVyVtvUL"
        



### CNV Gene Panel
CNV_bedfile_dict={"PanCM":"Pan.bed",\
                "PanCMD":"pan.bed",\
                "PanNERD":"pan.bed",\
                "PanGSDA":"pan.bed",\
                "PanGSDM":"pan.bed",\
                "PanGSDL":"pan.bed",\
                "PanMMA":"pan.bed",\
                "PanUCD":"pan.bed"\
                }
### Bedfile for sambamba 
coverage_bedfile_dict={"PanCM":"Pan.bed",\
                "PanCMD":"pan.bed",\
                "PanNERD":"pan.bed",\
                "PanGSDA":"pan.bed",\
                "PanGSDM":"pan.bed",\
                "PanGSDL":"pan.bed",\
                "PanMMA":"pan.bed",\
                "PanUCD":"pan.bed",\
                "WES" : "Pan493dataSambamba.bed"\
                }

### Bedfile for HSmetrics/GATK Haplotype Caller
capture_bedfile_dict={"PanCM":"Pan.bed",\
                "PanCMD":"pan.bed",\
                "PanNERD":"pan.bed",\
                "PanGSDA":"pan.bed",\
                "PanGSDM":"pan.bed",\
                "PanGSDL":"pan.bed",\
                "PanMMA":"pan.bed",\
                "PanUCD":"pan.bed",\
                "WES" : "agilent_sureselect_human_all_exon_v5_b37_targets.bed"\
                }

# message which marks sucessful demultiplexing from bcl2fastq
logfile_success = "Processing completed with 0 errors and 0 warnings."

#path to upload agent
upload_agent = "/home/mokaguys/Documents/apps/dnanexus-upload-agent-1.5.17-linux/ua"

### smartsheet API
# smartsheet sheet ID
smartsheet_sheetid=2798264106936196

#columnIds
ss_title=6197963270711172
ss_description=3946163457025924
ss_samples=957524288530308
ss_status=8449763084396420
ss_priority=4790588387157892
ss_assigned=2538788573472644
ss_received=6723667267741572
ss_completed=4471867454056324
ss_duration=6519775204534148
ss_metTAT=4267975390848900

# API key
smartsheet_api_key="***REMOVED***"

###email server settings
user = 'AKIAIO3XY2MMSBEQNNXQ'
pw   = '***REMOVED***'
host = 'email-smtp.eu-west-1.amazonaws.com'
port = 587
me   = 'gst-tr.mokaguys@nhs.net'
you  = ('gst-tr.mokaguys@nhs.net',)
smtp_do_tls = True
