'''
DNA Nexus Upload agent configuration
'''
#set debug mode
#debug=True
debug=False



########################### location of input/output files####################
# path to run folders
runfolders = "/media/data1/share"

#samplesheet folder
samplesheets=runfolders+"/samplesheets/"
# path to fastq files
fastq_folder = "/Data/Intensities/BaseCalls"

# path to log file which records the output of the upload agent
upload_agent_logfile = "/home/mokaguys/Documents/automate_demultiplexing_logfiles/upload_agent_script_logfiles/"

# name of log file which records the output of the upload agent
upload_started_file = "DNANexus_upload_started.txt"

#runfolder backup files
runfolder_upload_cmds="add_runfolder_to_nexus_cmds.txt"

# Path to DNA Nexus run command log file
DNA_Nexus_workflow_logfolder = "/home/mokaguys/Documents/automate_demultiplexing_logfiles/dx_run_commands/"

#log folder containing project creation logs
DNA_Nexus_project_creation_logfolder = "/home/mokaguys/Documents/automate_demultiplexing_logfiles/nexus_project_creation_scripts/create_nexus_project_"

# folder containing demultiplex logs
demultiplex_logfiles="/home/mokaguys/Documents/automate_demultiplexing_logfiles/Demultiplexing_log_files/"

# message which marks sucessful demultiplexing from bcl2fastq
logfile_success = "Processing completed with 0 errors and 0 warnings."

#path to upload agent
upload_agent = "/home/mokaguys/Documents/apps/dnanexus-upload-agent-1.5.17-linux/ua"

####################### Moka settings ######################
moka_pipeline_ID="1854"

########################## DNA Nexus setting#############################
# project to upload run folder into
NexusProjectPrefix="002_"

#success statement when creating project 
project_success="Created new project called \"%s\""

# The project containing the app and data
app_project="001_ToolsReferenceData:"
#path to the workflow in the app project
workflow_path="Workflows/GATK3.5_v2.8"
#path to the oncology workflow in the app project
onco_path="Workflows/Mokaonc_v1.1"
#path to multiqc app
multiqc_path="Apps/multiqc"
#smartsheet app
smartsheet_path="Apps/smartsheet_mokapipe_complete"
#RPKM path
RPKM_path="Apps/RPKM_using_conifer"
# bedfile folder
bedfile_folder="Data/BED/"
# DNA Nexus organisation to create the project within
prod_organisation="org-viapath_prod"
dev_organisation="org-viapath_dev"

# project tags to denote live
live_tag="live"

############################istages######################################
#GATK workflow
fastqc1 = " -istage-Bz3YpP80jy1Y1pZKbZ35Bp0x.reads=" # FastQC Read 1
fastqc2 = " -istage-Bz3YpP80jy1x7G5QfG3442gX.reads=" # FastQC Read 2
#bwa_fastq1 = " -istage-Byz9BJ80jy1k2VB9xVXBp0Fg.reads_fastqgz=" # BWAFastQ Read1
#bwa_fastq2 = " -istage-Byz9BJ80jy1k2VB9xVXBp0Fg.reads2_fastqgz=" # BWA FastQ Read2
sambamba_input = " -istage-F35zBKQ0jy1XpfzYPZY4bgX6.sambamba_bed=" # Sambamba Bed file
mokavendor_input = " -istage-F35FvQ00jy1pb8f11vB4Xjf1.vendor_exome_bedfile=" # HSMetrics Bed file
#GATK_Human_Exome_Pipeline_input = " -istage-F28y4qQ0jy1fkqfy5v2b8byx.vendor_exome_bedfile=" # uses same bedfile as moka vendor so can specify this in bedfile
ingenuity_input=" -istage-Byz9Bj80jy1k2VB9xVXBp0Fp.email="

# amplivar fastq input
onco_input=" -istage-F5XGz7j0jy1VqPVFBgb75K4f.fastqs="
# general oncology email
onco_email="gst-tr.oncology.interpret@nhs.net"
#email for Interpretation_requests
interpretation_request_email="gst-tr.interpretation.request@nhs.net"
#wook email
wook_email="joowook.ahn@nhs.net"

# email if no variants app input for amplivar workflow
vcf_novariants=" -istage-F5k1PB00jy1zxKZ28JX5b41q.email="
# ingenuity app input for amplivar workflow
onco_ingenuity=" -istage-F5k1Qyj0jy1VKJb2KYqq7fxG.email="
#MultiQC
multiqc_project_input=" -iproject_for_multiqc="

#Smartsheet
smartsheet_mokapipe_complete=" -iNGS_run="

#RPKM inputs
RPKM_bedfile=" -ibedfile="
RPKM_project=" -iproject_name="
RPKM_bedfile_to_download=" -ibamfile_name="
        
# DNA Nexus authentication token
#Nexus_API_Key = "rsivxAMylcfpHvIIcZy8hDsFUVyVtvUL" 
Nexus_API_Key = "K2v2COMKM7NdjeHyWdINUSrCrHaJfnxZ" 
        
users=["aledjones","wook","mokaguys","andyb","AmyS","InterpretationRequest"]

################## Dict linking panel numbers for +/-10 and CNVs ####################
panelnumbers={"Pan493":"",\
					"Pan1120":"",\
                    "Pan1190":"",\
                    "Pan1449":"Pan1450",\
                    "Pan1451":"Pan1452",\
                    "Pan1453":"Pan1454",\
                    "Pan1063":"Pan1064",\
                    "Pan1009":"Pan1010",\
                    "Pan1459":"Pan1458",\
                    "Pan1464":"Pan1471"}

#Pan numbers to add in to above  dict once bed files are in 001.                 
#"Pan1157":"Pan1455",\
#"Pan1158":"Pan1456",\
#"Pan1159":"Pan1457",\


email_panel_dict={"Pan493":wook_email,\
					"Pan1009":interpretation_request_email,\
					"Pan1063":interpretation_request_email,\
					"Pan1120":wook_email,\
					"Pan1157":interpretation_request_email,\
					"Pan1158":interpretation_request_email,\
					"Pan1159":interpretation_request_email,\
                    "Pan1190":onco_email,\
                    "Pan1449":interpretation_request_email,\
                    "Pan1451":interpretation_request_email,\
                    "Pan1453":interpretation_request_email,\
                    "Pan1459":interpretation_request_email,\
                    "Pan1464":interpretation_request_email}

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

#####################Loggly
# log command
echo_to_log="echo %s 2>&1 | /usr/bin/logger -t %s"