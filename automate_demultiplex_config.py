"""
Automate demultiplex configuration.

The variables defined in this module are required by the "demultiplex.py" and
"DNANexus_upload_agent.py" scripts.
"""
# Set debug mode
# Debug = True
debug = False

# =====git release for the automate_demultiplexing repo=====
script_release = "v9.0"


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
moka_pipeline_ID = "1941"
# Current MokaWES ID
mokawes_pipeline_ID = "2037"
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
workflow_path = "Workflows/GATK3.5_v2.8"
# path to the WES workflow in the app project
wes_path = "Workflows/MokaWES_v1.0"
# path to the oncology workflow in the app project
onco_path = "Workflows/Mokaonc_v1.2"
# path to paddy app
peddy_path = "Apps/peddy"
# path to multiqc app
multiqc_path = "Apps/multiqc"
# smartsheet app
smartsheet_path = "Apps/smartsheet_mokapipe_complete"
# RPKM path
RPKM_path = "Apps/RPKM_using_conifer"
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
mokavendor_input = " -istage-F35FvQ00jy1pb8f11vB4Xjf1.vendor_exome_bedfile="  # HSMetrics Bed file
iva_email_input = " -istage-Byz9Bj80jy1k2VB9xVXBp0Fp.email=" # ingenuity email address

# GATK workflow
human_exome_gatk_jar_input = " -istage-F28y4qQ0jy1fkqfy5v2b8byx.gatk_jar_file=\"project-ByfFPz00jy1fk6PjpZ95F27J:file-Byy2gGj0V695BXBb6Q33j2Kj\""  # gatk jar file for human exome app in 001_ToolsReferenceData
vcf_annotator_gatk_jar_file_input = " -istage-F2gPqFQ025p601qgGq0QVvX2.gatk_jar_file=\"project-ByfFPz00jy1fk6PjpZ95F27J:file-Byy2gGj0V695BXBb6Q33j2Kj\""  # gatk jar file used for variant annotator in 001_ToolsReferenceData
vcf_annotator_prev_class_vcf_input = " -istage-F2gPqFQ025p601qgGq0QVvX2.prev_class=\"project-ByfFPz00jy1fk6PjpZ95F27J:file-F2YPPj80j4gFP8ZB3VGfkq43\""  # vcf with previous classifications used for vcf annotator in 001_ToolsReferenceData
bwa_ref_genome = " -istage-Byz9BJ80jy1k2VB9xVXBp0Fg.genomeindex_targz=\"project-B6JG85Z2J35vb6Z7pQ9Q02j8:file-B6ZY4942J35xX095VZyQBk0v\""  # reference genome used for bwa (in a dna nexus maintained project) in 001_ToolsReferenceData
picard_fasta_index = " -istage-Bz4Vj200jy1xj2vg9Zb71y9G.fasta_index=\"project-ByfFPz00jy1fk6PjpZ95F27J:file-ByYgX700b80gf4ZY1GxvF3Jv\""  # reference fasta file from 001_ToolsReferenceData
# combine all commands so don't have to edit the main script.
ingenuity_input = human_exome_gatk_jar_input + vcf_annotator_gatk_jar_file_input + vcf_annotator_prev_class_vcf_input + bwa_ref_genome + picard_fasta_index + iva_email_input

# MokaOnc amplivar fastq input
onco_input = " -istage-F7kPz6Q0vpxb0YpjBgQx5f8v.fastqs=" # 
vcf_novariants = " -istage-F5k1PB00jy1zxKZ28JX5b41q.email=" # email if no variants app input for amplivar workflow
onco_ingenuity = " -istage-F5k1Qyj0jy1VKJb2KYqq7fxG.email=" # ingenuity app input for amplivar workflow

# amplivar_reference_genome_input = " -istage-F7kPz6Q0vpxb0YpjBgQx5f8v.ref_genome=project-ByfFPz00jy1fk6PjpZ95F27J:file-F4g9Y280jy1ZKkq164Vq0FZ9\""
# amplivar_flanking_seq_input = " -istage-F7kPz6Q0vpxb0YpjBgQx5f8v.ampliconflank=project-ByfFPz00jy1fk6PjpZ95F27J:file-F5VfXQQ0p3fq52zGG21218zZ\""
# amplivar_usual_suspects= " -istage-F7kPz6Q0vpxb0YpjBgQx5f8v.usual_suspects=project-ByfFPz00jy1fk6PjpZ95F27J:file-F3J35f00jy1Z797p8bj9J0Zx\""
# varscan2_ref_genome = " -istage-F5XGzF80jy1y9Q8F2VvvbXkb.ref_genome=project-ByfFPz00jy1fk6PjpZ95F27J:file-F4g9Y280jy1ZKkq164Vq0FZ9
# varscan2_bedfile = " -istage-F5XGzF80jy1y9Q8F2VvvbXkb.bed_file=project-ByfFPz00jy1fk6PjpZ95F27J:file-F516ZyQ0jy1vP3P2FZZ3VFpQ"
# vardict_reference_genome = " -istage-F5XGzG00jy1q5y612VQ9KXxx.ref_genome=project-ByfFPz00jy1fk6PjpZ95F27J:file-F4g9Y280jy1ZKkq164Vq0FZ9"
# vardict_bedfile = " -istage-F5XGzG00jy1q5y612VQ9KXxx.bedfile=project-ByfFPz00jy1fk6PjpZ95F27J:file-F516ZyQ0jy1vP3P2FZZ3VFpQ"
# amplivar_coverage_report = " -istage-F5XGz980jy1VqPVFBgb75K4g.lookup=project-ByfFPz00jy1fk6PjpZ95F27J:file-F516b2Q0jy1QZ4G99XV16Jy4"

# # concatenate all 
# onco_ingenuity = amplivar_reference_genome_input + amplivar_flanking_seq_input + amplivar_usual_suspects + varscan2_ref_genome + varscan2_bedfile + vardict_reference_genome + vardict_bedfile + amplivar_coverage_report + onco_ingenuity

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
Nexus_API_Key = "K2v2COMKM7NdjeHyWdINUSrCrHaJfnxZ"

# list of DNA Nexus users for project to be shared with
users = ["org-viapath_prod", "InterpretationRequest"]


# =====Dict linking panel numbers for +/-10 and CNVs=====
panelnumbers = {"Pan493": "",
                "Pan1120": "",
                "Pan1190": "",
                "Pan1449": "Pan1450",
                "Pan1451": "Pan1452",
                "Pan1453": "Pan1454",
                "Pan1063": "Pan1064",
                "Pan1009": "Pan1010",
                "Pan1459": "Pan1458",
                "Pan1464": "Pan1471",
                "Pan1157": "Pan1455",
                "Pan1158": "Pan1456",
                "Pan1159": "Pan1457"}

# =====Dict linking panel and Ingenuity account for sample to be shared with =====
email_panel_dict = {"Pan493": WES_email,
                    "Pan1009": interpretation_request_email,
                    "Pan1063": interpretation_request_email,
                    "Pan1120": wook_email,
                    "Pan1157": interpretation_request_email,
                    "Pan1158": interpretation_request_email,
                    "Pan1159": interpretation_request_email,
                    "Pan1190": onco_email,
                    "Pan1449": interpretation_request_email,
                    "Pan1451": interpretation_request_email,
                    "Pan1453": interpretation_request_email,
                    "Pan1459": interpretation_request_email,
                    "Pan1464": interpretation_request_email,
                    "Pan1157": interpretation_request_email,
                    "Pan1158": interpretation_request_email,
                    "Pan1159": interpretation_request_email}

# =====smartsheet API=====
# smartsheet sheet ID
smartsheet_sheetid = 2798264106936196

# API key
smartsheet_api_key = "***REMOVED***"

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
pw = '***REMOVED***'
host = 'email-smtp.eu-west-1.amazonaws.com'
port = 587
me = 'gst-tr.mokaguys@nhs.net'
you = ('gst-tr.mokaguys@nhs.net',)
smtp_do_tls = True

# ================ Integrity check
# the filename which holds the checksum results
md5checksum_name = "md5checksum.txt"
# path to mapped miseq sequencer folders
sequencer_share = {"M02353": "/media/M02353_MiSeqTemp/", "M02631": "/media/M02631_MiSeqTemp/"}
#checksum complete statement
checksum_complete_flag="Checksum result reported"
# ================ demultiplexing 
logfile_success = "Processing completed with 0 errors and 0 warnings."

#=================turnaround time
# if a task takes more than this amount of time it is out of TAT
allowed_time_for_tasks=4
