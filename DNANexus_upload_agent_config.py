'''
DNA Nexus Upload agent configuration
'''
#set debug mode
#debug=True
debug=False


########################### location of input/output files####################
# path to run folders
runfolders = "/media/data1/share"

# path to fastq files
fastq_folder = "/Data/Intensities/BaseCalls"

# path to log file which records the output of the upload agent
upload_agent_logfile = "/home/mokaguys/Documents/automate_demultiplexing_logfiles/Upload_agent_log/"

# name of log file which records the output of the upload agent
upload_started_file = "DNANexus_upload_started.txt"

#runfolder backup file
runfolder_upload_file="add_runfolder_to_nexus_logfile.txt"

# Path to DNA Nexus run command log file
DNA_Nexus_workflow_logfolder = "/home/mokaguys/Documents/automate_demultiplexing_logfiles/DNA_Nexus_workflow_logs/"

#log folder containing project creation logs
DNA_Nexus_project_creation_logfolder = "/home/mokaguys/Documents/automate_demultiplexing_logfiles/Nexus_project_creation_logs/create_nexus_project_"


# folder containing demultiplex logs
demultiplex_logfiles="/home/mokaguys/Documents/automate_demultiplexing_logfiles/Demultiplexing_log_files/"

# message which marks sucessful demultiplexing from bcl2fastq
logfile_success = "Processing completed with 0 errors and 0 warnings."

#path to upload agent
upload_agent = "/home/mokaguys/Documents/apps/dnanexus-upload-agent-1.5.17-linux/ua"

####################### Moka settings ######################
moka_pipeline_ID="1363"

########################## DNA Nexus setting#############################
# project to upload run folder into
NexusProjectPrefix="002_"

#success statement when creating project 
project_success="Created new project called \"%s\""

# The project containing the app and data
app_project="001_ToolsReferenceData:"
#path to the workflow in the app project
workflow_path="Workflows/GATK3.5_v2.4"
#path to multiqc app
multiqc_path="Apps/multiqc"
#smartsheet app
smartsheet_path="Apps/smartsheet_mokapipe_complete"
# bedfile folder
bedfile_folder="Data/BED/"
# DNA Nexus organisation to create the project within
organisation="org-viapath_prod"

############################istages######################################
fastqc1 = " -istage-Bz3YpP80jy1Y1pZKbZ35Bp0x.reads=" # FastQC Read 1
fastqc2 = " -istage-Bz3YpP80jy1x7G5QfG3442gX.reads=" # FastQC Read 2
#bwa_fastq1 = " -istage-Byz9BJ80jy1k2VB9xVXBp0Fg.reads_fastqgz=" # BWAFastQ Read1
#bwa_fastq2 = " -istage-Byz9BJ80jy1k2VB9xVXBp0Fg.reads2_fastqgz=" # BWA FastQ Read2
sambamba_input = " -istage-F35zBKQ0jy1XpfzYPZY4bgX6.sambamba_bed=" # Sambamba Bed file
mokavendor_input = " -istage-F35FvQ00jy1pb8f11vB4Xjf1.vendor_exome_bedfile=" # HSMetrics Bed file
#GATK_Human_Exome_Pipeline_input = " -istage-F28y4qQ0jy1fkqfy5v2b8byx.vendor_exome_bedfile=" # uses same bedfile as moka vendor so can specify this in bedfile
ingenuity_input=" -istage-Byz9Bj80jy1k2VB9xVXBp0Fp.email="
multiqc_project_input=" -iproject_for_multiqc="
smartsheet_mokapipe_complete=" -iNGS_run="
        
# DNA Nexus authentication token
#Nexus_API_Key = "rsivxAMylcfpHvIIcZy8hDsFUVyVtvUL" 
Nexus_API_Key = "K2v2COMKM7NdjeHyWdINUSrCrHaJfnxZ" 
        
users=["aledjones","wook","mokaguys","andyb","AmyS"]

################## Dict linking panel numbers for +/-10 and CNVs ####################
panelnumbers={"Pan1001":"Pan992",\
                    "Pan1000":"Pan991",\
                    "Pan994":"Pan943",\
                    "Pan996":"Pan945",\
                    "Pan995":"Pan944",\
                    "Pan998":"Pan947",\
                    "Pan1009":"Pan1010",\
                    "Pan999":"Pan989",\
                    "Pan493":""}


email_panel_dict={"Pan1001":"joowook.ahn@nhs.net",\
                    "Pan1000":"joowook.ahn@nhs.net",\
                    "Pan994":"joowook.ahn@nhs.net",\
                    "Pan996":"joowook.ahn@nhs.net",\
                    "Pan995":"joowook.ahn@nhs.net",\
                    "Pan998":"joowook.ahn@nhs.net",\
                    "Pan1009":"joowook.ahn@nhs.net",\
                    "Pan999":"joowook.ahn@nhs.net",\
                    "Pan493":"joowook.ahn@nhs.net"}

################################# smartsheet API ################################
# smartsheet sheet ID
smartsheet_sheetid=2798264106936196

# API key
smartsheet_api_key="3asfndq3oi2zbww3td8gb67liv"

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


########################email server settings
user = 'AKIAIO3XY2MMSBEQNNXQ'
pw   = 'AmkKC7nXvLrxsvBHZf3zagNq953nun9c0iYN+zjifIbN'
host = 'email-smtp.eu-west-1.amazonaws.com'
port = 587
me   = 'gst-tr.mokaguys@nhs.net'
you  = ('gst-tr.mokaguys@nhs.net',)
smtp_do_tls = True
