"""
Automate demultiplex configuration.

The variables defined in this module are required by the "demultiplex.py" and
"DNANexus_upload_agent.py" scripts.
"""
# Set debug mode
#debug = True
debug = False

# =====git release for the automate_demultiplexing repo=====
script_release = "v15.0"

# =====location of input/output files=====
# path to run folders
runfolders = "/media/data1/share"

# samplesheet folder
samplesheets = runfolders + "/samplesheets/"

# path to fastq files
fastq_folder = "/Data/Intensities/BaseCalls"

# path to bcl2fastq
bcl2fastq = "/usr/local/bcl2fastq2-v2.20.0.422/bin/bcl2fastq"

# files for checking NGS runfolders before demultiplexing
file_complete_run = "RTAComplete.txt"
file_demultiplexing = "demultiplexlog.txt"

# directories to be ignored when looping through runfolders
ignore_directories = ["samplesheets", "GlacierTest"]

# path to log file which records the output of the upload agent
upload_agent_logfile = "/home/mokaguys/Documents/automate_demultiplexing_logfiles/upload_agent_script_logfiles/"

# name of log file which records the output of the upload agent
upload_started_file = "DNANexus_upload_started.txt"

# runfolder backup files
runfolder_upload_cmds = "add_runfolder_to_nexus_cmds.txt"

# Path to DNA Nexus run command log file
DNA_Nexus_workflow_logfolder = "/home/mokaguys/Documents/automate_demultiplexing_logfiles/dx_run_commands/"

# log folder containing project creation logs
DNA_Nexus_project_creation_logfolder = "/home/mokaguys/Documents/automate_demultiplexing_logfiles/nexus_project_creation_scripts/create_nexus_project_"

# folder containing demultiplex logs
demultiplex_logfiles = "/home/mokaguys/Documents/automate_demultiplexing_logfiles/Demultiplexing_log_files/"

# path to upload agent
upload_agent = "/home/mokaguys/Documents/apps/dnanexus-upload-agent-1.5.17-linux/ua"


# =====Moka settings=====
# Moka IDs for generating SQLs to update the Mokadatabase
# Current Mokapipe ID
mokapipe_pipeline_ID = "2209"
# Current MokaWES ID
mokawes_pipeline_ID = "2210"
# -- Moka WES test status--
# Test Status = NextSEQ sequencing
mokastat_nextsq_ID = "1202218804"
# Test Status = Data Processing
mokastatus_dataproc_ID = "1202218805"

# =====DNA Nexus settings=====
# project to upload run folder into
NexusProjectPrefix = "002_"

# success statement when creating project
project_success = "Created new project called \"%s\""

# The project containing the app and data
app_project = "001_ToolsReferenceData:"
# path to the workflow in the app project
workflow_path = "Workflows/GATK3.5_v2.9"
# path to the WES workflow in the app project
wes_path = "Workflows/MokaWES_v1.1"
# path to the oncology workflow in the app project
onco_path = "Workflows/Mokaonc_v1.3"
# path to paddy app
peddy_path = "Apps/peddy_v1.1"
# path to multiqc app
multiqc_path = "Apps/multiqc_v1.5"
# smartsheet app
smartsheet_path = "Apps/smartsheet_mokapipe_complete_v1.1"
# RPKM path
RPKM_path = "Apps/RPKM_using_conifer_v1.3"
# bedfile folder
bedfile_folder = "Data/BED/"
# DNA Nexus organisation to create the project within
prod_organisation = "org-viapath_prod"
dev_organisation = "org-viapath_dev"

# project tags to denote live cases
live_tag = "live"

# =====istages=====
# GATK and MokaWES workflow input
fastqc1 = " -istage-Bz3YpP80jy1Y1pZKbZ35Bp0x.reads="  # FastQC Read 1
fastqc2 = " -istage-Bz3YpP80jy1x7G5QfG3442gX.reads="  # FastQC Read 2
sambamba_input = " -istage-F35zBKQ0jy1XpfzYPZY4bgX6.sambamba_bed="  # Sambamba Bed file
mokavendor_input = " -istage-F9GK4QQ0jy1qj14PPZxxq3VG.vendor_exome_bedfile="  # HSMetrics Bed file
iva_email_input = " -istage-Byz9Bj80jy1k2VB9xVXBp0Fp.email=" # ingenuity email address

# MokaOnc amplivar fastq input
onco_input = " -istage-F7kPz6Q0vpxb0YpjBgQx5f8v.fastqs=" # 
onco_ingenuity = " -istage-F5k1Qyj0jy1VKJb2KYqq7fxG.email=" # ingenuity app input for amplivar workflow

# Peddy
peddy_project_input  = " -iproject_for_peddy="
# MultiQC
multiqc_project_input = " -iproject_for_multiqc="
# Smartsheet
smartsheet_mokapipe_complete = " -iNGS_run="
# RPKM inputs
RPKM_bedfile = " -ibedfile="
RPKM_project = " -iproject_name="
RPKM_bedfile_to_download = " -ibamfile_name="

# emails addresses for Ingenuity
onco_email = "gst-tr.oncology.interpret@nhs.net" # general oncology email
interpretation_request_email = "gst-tr.interpretation.request@nhs.net" # email for Interpretation_requests
wook_email = "joowook.ahn@nhs.net" # wook email
WES_email = "gst-tr.wesviapath@nhs.net" # WES email

# DNA Nexus authentication token
Nexus_API_Key = "MK8QlLFLwGvFDkgc9MnaWIgrTARHlO3e"

# list of DNA Nexus users for project to be shared with
users = ["org-viapath_prod", "InterpretationRequest"]


# =====Dict linking panel numbers for +/-10 and CNVs=====
panelnumbers = {"Pan493": None,
                "Pan1620": None,
                "Pan1190": None,
                "Pan1449": "Pan1450",
                "Pan1451": "Pan1452",
                "Pan1453": "Pan1454",
                "Pan1063": "Pan1064",
                "Pan1009": "Pan1010",
                "Pan1459": "Pan1458",
                "Pan2022": "Pan1974",
                "Pan1965": "Pan2000",
                "Pan1158": "Pan2023",
                "Pan1159": None}

# =====Dict linking panel and Ingenuity account for sample to be shared with =====
email_panel_dict = {"Pan493": WES_email,
                    "Pan1009": interpretation_request_email,
                    "Pan1063": interpretation_request_email,
                    "Pan1620": wook_email,
                    "Pan1157": interpretation_request_email,
                    "Pan1158": interpretation_request_email,
                    "Pan1159": interpretation_request_email,
                    "Pan1190": onco_email,
                    "Pan1449": interpretation_request_email,
                    "Pan1451": interpretation_request_email,
                    "Pan1453": interpretation_request_email,
                    "Pan1459": interpretation_request_email,
                    "Pan2022": interpretation_request_email,
                    "Pan1965": interpretation_request_email,
                    "Pan1158": interpretation_request_email,
                    "Pan1159": interpretation_request_email}

# =====smartsheet API=====
# smartsheet sheet ID
smartsheet_sheetid = 2798264106936196

# API key
smartsheet_api_key = "3asfndq3oi2zbww3td8gb67liv"

# columnIds
ss_title = 6197963270711172
ss_description = 3946163457025924
ss_samples = 957524288530308
ss_status = 8449763084396420
ss_priority = 4790588387157892
ss_assigned = 2538788573472644
ss_received = 6723667267741572
ss_completed = 4471867454056324
ss_duration = 6519775204534148
ss_metTAT = 4267975390848900

# ================ Requests info
smartsheet_request_headers = {"Authorization": "Bearer " + smartsheet_api_key, "Content-Type": "application/json"}
smartsheet_request_url = 'https://api.smartsheet.com/2.0/sheets/' + str(smartsheet_sheetid)


# =================== Email server settings
user = 'AKIAIO3XY2MMSBEQNNXQ'
pw = 'AmkKC7nXvLrxsvBHZf3zagNq953nun9c0iYN+zjifIbN'
host = 'email-smtp.eu-west-1.amazonaws.com'
port = 587
me = 'gst-tr.mokaguys@nhs.net'
you = ('gst-tr.mokaguys@nhs.net',)
smtp_do_tls = True

# ================ Integrity check
# the filename which holds the checksum results
md5checksum_name = "md5checksum.txt"
# checksum complete statement
checksum_complete_flag = "Checksum result reported"
# statement to write when checksums match
checksum_match = "Checksums match"
# hours to wait after RTAcomplete.txt file before first integrity check 
integrity_check_first_wait = 3
# hours between integrity checks
integrity_check_repeat_wait = 1
# maximum number of times to perform integrity test
max_number_of_attempts = 10
# list of files which differ between temp and output
missing_files_output = "missing_files.txt"
# files to exclude from integrity check
exclude = ["RTAStart.bat", "CorrectedIntMetrics.bin", "EmpiricalPhasingMetrics.bin", "ErrorMetrics.bin", "EventMetrics.bin", "ExtractionMetrics.bin", "PFGridMetrics.bin", "QMetrics.bin", "RegistrationMetrics.bin", "TileMetrics.bin", "000_000_000_na_rtabat.trans", "FilesAdded.csv", "FilesCopied.csv", "md5checksum.txt", missing_files_output]
# ================ demultiplexing 
logfile_success = "Processing completed with 0 errors and 0 warnings."

# =================turnaround time
# if a task takes more than this amount of time it is out of TAT
allowed_time_for_tasks = 4
