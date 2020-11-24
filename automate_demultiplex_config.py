"""
Automate demultiplex configuration.

The variables defined in this module are required by the "demultiplex.py" and
"DNANexus_upload_agent.py" scripts.
"""

import os

# Set debug mode
debug = False

# =====location of input/output files=====
# root of folder that contains the apps, automate_demultiplexing_logfiles and
# development_area scripts
# (2 levels up from this file)
document_root = "/".join(os.path.dirname(os.path.realpath(__file__)).split("/")[:-2])

# # path to run folders
runfolders = "/media/data3/share"
# when testing use a different directory
#runfolders = "/media/data3/share/testing"

# samplesheet folder
samplesheets = runfolders + "/samplesheets/"

# path to fastq files
fastq_folder = "/Data/Intensities/BaseCalls"

# path to bcl2fastq
bcl2fastq = "/usr/local/bcl2fastq2-v2.20.0.422/bin/bcl2fastq"

# files for checking NGS runfolders before demultiplexing
file_complete_run = "RTAComplete.txt"
file_demultiplexing = "bcl2fastq2_output.log"
file_demultiplexing_old = "demultiplexlog.txt"

# directories to be ignored when looping through runfolders
ignore_directories = ["samplesheets", "GlacierTest"]

demultiplex_test_folder = ["999999_M02353_0288_demultiplex_test"]

# path to log file which records the output of the upload agent
upload_and_setoff_workflow_logfile = (
    "{document_root}/automate_demultiplexing_logfiles/upload_agent_script_logfiles/"
).format(document_root=document_root)

# name of log file which records the output of the upload agent
upload_started_file = "DNANexus_upload_started.txt"

# runfolder backup files
runfolder_upload_cmds = "add_runfolder_to_nexus_cmds.txt"

# Path to DNA Nexus run command log file
DNA_Nexus_workflow_logfolder = (
    "{document_root}/automate_demultiplexing_logfiles/dx_run_commands/"
).format(document_root=document_root)

# log folder containing project creation logs
DNA_Nexus_project_creation_logfolder = (
    "{document_root}/automate_demultiplexing_logfiles/nexus_project_creation_scripts"
    "/create_nexus_project_"
).format(document_root=document_root)

# folder containing demultiplex logs
demultiplex_logfiles = (
    "{document_root}/automate_demultiplexing_logfiles/Demultiplexing_log_files/"
).format(document_root=document_root)

# path to upload agent
upload_agent_path = ("{document_root}/apps/dnanexus-upload-agent-1.5.17-linux/ua").format(
    document_root=document_root
)

upload_agent_test_command = " --version"
ua_error = "Error Message: 'Could not resolve: api.dnanexus.com"

# path to backup_runfolder script
backup_runfolder_script = (
    "/usr/local/src/mokaguys/apps/workstation_housekeeping/backup_runfolder.py"
)

# backup runfolder folder
backup_runfolder_logfile = (
    "{document_root}/automate_demultiplexing_logfiles"
    "/backup_runfolder_logfiles"
).format(document_root=document_root)

backup_runfolder_success = "backup_runfolder INFO - END"
backup_runfolder_error = "backup_runfolder.UAcaller ERROR"

# command to test dx toolkit
dx_sdk_test = "source ~/dx-toolkit/environment;dx --version"
# expected result from testing
dx_sdk_test_expected_stdout = "dx v0.2"

upload_agent_expected_stdout = "Upload Agent Version:"

# =====Moka settings=====
# Moka IDs for generating SQLs to update the Mokadatabase
# audit trail ID for Mokapipe & sapientia
mokapipe_sapientia_pipeline_ID = "4165"
# audit trail ID for Mokapipe & IVA
mokapipe_iva_pipeline_ID = "4164"
# Current MokaWES ID
mokawes_pipeline_ID = "4160"
# MokaAMP ID
mokaamp_pipeline_ID = "4236"
# MokaONC ID
mokaonc_pipeline_ID = "2405"


# -- Moka WES test status--
# Test Status = NextSEQ sequencing
mokastat_nextsq_ID = "1202218804"
# Test Status = Data Processing
mokastatus_dataproc_ID = "1202218805"

# =====DNA Nexus settings=====
# project to upload run folder into
NexusProjectPrefix = "002_"

# success statement when creating project
project_success = 'Created new project called "%s"'

# The project containing the app and data
app_project = "001_ToolsReferenceData:/"
# path to the workflow in the app project

mokapipe_path = "Workflows/GATK3.5_v2.12"
# path to the WES workflow in the app project
mokawes_path = "Workflows/MokaWES_v1.8"

# path to the oncology workflow in the app project
mokaonc_path = "Workflows/Mokaonc_v1.4"
# path to mokaamp
mokaamp_path = "Workflows/MokaAMP_v1.4"
# path to paddy app
peddy_path = "Apps/peddy_v1.5"
# path to multiqc app
multiqc_path = "Apps/multiqc_v1.12"
# path to sentieon upload app
sapientia_app_path = "Apps/sapientia_upload_v1.0"
# path to iva upload app
iva_app_path = "app-ingenuity_variant_transfer/1.0.6"

# path to app which uploads multiqc report
upload_multiqc_path = "Apps/upload_multiqc_v1.3"
# smartsheet app
smartsheet_path = "Apps/smartsheet_mokapipe_complete_v1.2"
# RPKM path
RPKM_path = "Apps/RPKM_using_conifer_v1.6"
# bedfile folder
bedfile_folder = "Data/BED/"
# DNA Nexus organisation to create the project within
prod_organisation = "org-viapath_prod"
dev_organisation = "org-viapath_dev"

# project tags to denote live cases
live_tag = "live"

# =====istages=====
mokapipe_variant_annotator_stage = "stage-F2gPqFQ025p601qgGq0QVvX2"
mokapipe_gatk_human_exome_stage = "stage-F28y4qQ0jy1fkqfy5v2b8byx"
# Mokapipe workflow inputs
mokapipe_fastqc1 = " -istage-Bz3YpP80jy1Y1pZKbZ35Bp0x.reads="  # FastQC Read 1
mokapipe_fastqc2 = " -istage-Bz3YpP80jy1x7G5QfG3442gX.reads="  # FastQC Read 2
mokapipe_bwa_rg_sample = " -istage-Byz9BJ80jy1k2VB9xVXBp0Fg.read_group_sample="  # bwa rg samplename
mokapipe_sambamba_input = " -istage-F35zBKQ0jy1XpfzYPZY4bgX6.sambamba_bed="  # Sambamba Bed file
mokapipe_mokapicard_vendorbed_input = (
    " -istage-F9GK4QQ0jy1qj14PPZxxq3VG.vendor_exome_bedfile="  # HSMetrics Bed file
)
mokapipe_iva_email_input = " -istage-Byz9Bj80jy1k2VB9xVXBp0Fp.email="  # ingenuity email address
mokapipe_haplotype_padding_input = " -i" +mokapipe_gatk_human_exome_stage + ".padding="
mokapipe_haplotype_bedfile_input = " -i" +mokapipe_gatk_human_exome_stage + ".bedfile="
mokapipe_vcf_output_name = "vcf"
mokapipe_bam_output_name = "bam"


# MokaWES workflow_inputs
wes_fastqc1 = " -istage-Ff0P5Jj0GYKY717pKX3vX8Z3.reads="  # FastQC Read 1
wes_fastqc2 = " -istage-Ff0P5V00GYKyJfpX5bqX69Yg.reads="  # FastQC Read 2
# bedfile for hs metrics
wes_picard_bedfile = " -istage-Ff0P5pQ0GYKVBB0g1FG27BV8.vendor_exome_bedfile="
sentieon_stage_id = "stage-Ff0P73j0GYKX41VkF3j62F9j"
wes_sambamba_bedfile = " -istage-Ff0P82Q0GYKQ4j8b4gXzjqxX.sambamba_bed="
# sample name for sentieon app - prevents sample being incorrectly parsed from fastq filename
wes_sentieon_samplename = " -i%s.sample=" % sentieon_stage_id
# BED file used to restrict Senteion variant calling
wes_sentieon_targets_bed = " -i%s.targets_bed=" % sentieon_stage_id


# MokaOnc amplivar fastq input
mokaonc_fq_input = " -istage-F7kPz6Q0vpxb0YpjBgQx5f8v.fastqs="
# ingenuity app input for amplivar workflow
mokaonc_ingenuity = " -istage-F5k1Qyj0jy1VKJb2KYqq7fxG.email="

# MokaAMP
mokaamp_fastq_R1_stage = " -istage-FPzGj780jy1g3p1F4F8z4J7V.reads_fastqgz="
mokaamp_fastq_R2_stage = " -istage-FPzGj780jy1g3p1F4F8z4J7V.reads2_fastqgz="
mokaamp_bwa_rg_sample = " -istage-FPzGj780jy1g3p1F4F8z4J7V.read_group_sample="
mokaamp_mokapicard_bed_stage = " -istage-FPzGjV80jy1x97jg607Fg22b.vendor_exome_bedfile="
mokaamp_mokapicard_capturetype_stage = " -istage-FPzGjV80jy1x97jg607Fg22b.Capture_panel="
mokaamp_bamclipper_BEDPE_stage = " -istage-FPzGjJQ0jy1fF6505zFP6zz9.primers="
mokaamp_chanjo_cov_level_stage = " -istage-FPzGjfQ0jy1y01vG60K22qG1.coverage_level="
mokaamp_sambamba_bed_stage = " -istage-FPzGjfQ0jy1y01vG60K22qG1.sambamba_bed="
mokaamp_vardict_bed_stage = " -istage-FPzGjgj0jy1Q2JJF2zYx5J5k.bedfile="
mokaamp_varscan_bed_stage = " -istage-FPzGjp80jy1V3Jvb5z6xfpfZ.bed_file="
mokaamp_varscan_strandfilter_stage = " -istage-FPzGjp80jy1V3Jvb5z6xfpfZ.strand_filter="
mokaamp_mpileup_cov_level_stage = " -istage-FxypXb807p1zj3g8Jv45Y54P.min_coverage="

mokaamp_email_message = (
    "If both MokaAMP and MokaOnc (amplivar) have been run,"
    "please record the version of MokaOnc used."
)

# Peddy
peddy_project_input = " -iproject_for_peddy="

# MultiQC and upload_multiqc inputs, outputs and variables
multiqc_project_input = " -iproject_for_multiqc="
multiqc_coverage_level_input = " -icoverage_level="
multiqc_html_output = "multiqc_report"
upload_multiqc_input = " -imultiqc_html="


# Smartsheet
smartsheet_mokapipe_complete = " -iNGS_run="

# RPKM inputs
rpkm_bedfile_input = " -ibedfile="
rpkm_project_input = " -iproject_name="
rpkm_bamfiles_to_download_input = " -ibamfile_pannumbers="

# emails addresses for Ingenuity
oncology_email = "m.neat@nhs.net"  # general oncology email
interpretation_request_email = (
    "gst-tr.interpretation.request@nhs.net"  # email for Interpretation_requests
)
wes_email_address = "gst-tr.wesviapath@nhs.net"  # WES email

# DNA Nexus authentication token
nexus_api_key_file = "{document_root}/.dnanexus_auth_token".format(document_root=document_root)
with open(nexus_api_key_file, "r") as nexus_api:
    Nexus_API_Key = nexus_api.readline().rstrip()

# list of DNA Nexus users with view access to project
view_users = ["org-viapath_prod", "InterpretationRequest"]
# list of DNA Nexus users with admin access of project
admin_users = ["mokaguys"]

# =====Decision support script
# takes an analysis id and builds inputs for the decision support upload.
decision_support_tool_input_script = "decision_support_tool_inputs.py"
mokawes_sentieon_bam_output_name = "mappings_realigned_bam"
mokawes_sentieon_bai_output_name = "mappings_realigned_bai"
mokawes_sentieon_vcf_output_name = "variants_vcf"
sapientia_vcf_inputname = " -ivcf="
sapientia_bam_inputname = " -ibam="
iva_vcf_inputname = " -ivcfs="
iva_bam_inputname = " -ibam_files="
iva_bai_inputname = " -ibai_files="
iva_email_input_name = " -iemail="
iva_reference_inputname = " -ireference_genome_name="
iva_reference_default = "GRCh37"


# =====List of all panel numbers=====
panel_list = [
    "Pan493",
    "Pan1063",
    "Pan1190",
    "Pan2684",
    "Pan1449",
    "Pan2022",
    "Pan1965",
    "Pan1158",
    "Pan1159",
    "Pan1646",
    "Pan3648",
    "Pan2835",
    "Pan3973",
    "Pan4011",
    "Pan4003",
    "Pan4044",
    "Pan4042",
    "Pan4043",
    "Pan4049"
]

default_panel_properties = {
    "UMI": False,
    "UMI_bcl2fastq": None,  # eg Y145,I8,Y9I8,Y145
    "RPKM_bedfile_pan_number": None,
    "RPKM_also_analyse": None,  # List of Pan Numbers indicating which BAM files to download
    "onePGT": False,
    "mokawes": False,
    "joint_variant_calling": False,
    "mokaamp": False,
    "capture_type": "Hybridisation",  # "Amplicon" or "Hybridisation"
    "mokaonc": False,
    "mokapipe": False,
    "mokapipe_haplotype_caller_padding": False,
    "mokaamp_varscan_strandfilter": True,
    "iva_upload": False,
    "sapientia_upload": False,
    "oncology": False,
    "clinical_coverage_depth": None,  # only found in mokamp command
    "multiqc_coverage_level": 30,
    # Note: hsmetrics_bedfile only used when BED file name differs from Pan number
    "hsmetrics_bedfile": None,
    # Note: variant_calling_bedfile only used when BED file differs from Pan number
    "variant_calling_bedfile": None,
    # Note: sambamba_bedfile only used when BED file differs from Pan number
    "sambamba_bedfile": None,
    "ingenuity_email": interpretation_request_email,
    "sapientia_project": None,
    "peddy": False,
}

# override default panel settings
panel_settings = {
    "Pan493": { # WES agilent
        "mokawes": True,
        "iva_upload": True,
        "multiqc_coverage_level": 20,
        "hsmetrics_bedfile": "agilent_sureselect_human_all_exon_v5_b37_targets.bed",
        "variant_calling_bedfile": "agilent_sureselect_human_all_exon_v5_b37_padded.bed",
        "ingenuity_email": wes_email_address,
        "peddy": True,
    },
    "Pan2835": {  # TWIST WES at GSTT
        "mokawes": True,
        "iva_upload": True,
        "multiqc_coverage_level": 20,
        "hsmetrics_bedfile": "Twist_Exome_RefSeq_CCDS_v1.2_targets.bed",
        "sambamba_bedfile": "Pan493dataSambamba.bed",
        "ingenuity_email": wes_email_address,
        "peddy": True,
    },
    "Pan1190": {  # EGFR SWIFT Panel
        "oncology": True,
        "mokaonc": True,
        "capture_type": "Amplicon",
        "ingenuity_email": oncology_email,
        "clinical_coverage_depth": 1000,
        "multiqc_coverage_level": 100,
        "iva_upload": True,
    },
    "Pan2684": {  # 57G panel
        "RPKM_bedfile_pan_number": None,
        "mokaamp": True,
        "oncology": True,
        "capture_type": "Amplicon",
        "iva_upload": True,
        "clinical_coverage_depth": 600,  # only found in mokamp command
        "multiqc_coverage_level": 100,
        "ingenuity_email": oncology_email,
    },
    "Pan1449": {  # germline BRCA
        "mokapipe": True,
        "multiqc_coverage_level": 30,
        "RPKM_bedfile_pan_number": "Pan1450",
        "RPKM_also_analyse": ["Pan3648"],
        "iva_upload": True,
    },
    "Pan3648": {  # STG germline BRCA
        "mokapipe": True,
        "multiqc_coverage_level": 30,
        "RPKM_bedfile_pan_number": "Pan1450",
        "RPKM_also_analyse": ["Pan1449"],
        "sapientia_upload": True,
        "sapientia_project": "1099",
        "hsmetrics_bedfile": "Pan1449data.bed",
        "mokapipe_haplotype_caller_padding":1,
        "variant_calling_bedfile": "Pan1449data.bed",
        "sambamba_bedfile": "Pan1449dataSambamba.bed",
    },
    "Pan1063": {  # IMDv2
        "mokapipe": True,
        "multiqc_coverage_level": 30,
        "RPKM_bedfile_pan_number": "Pan1064",
        "iva_upload": True,
    },
    "Pan2022": {  # CMCMD
        "mokapipe": True,
        "multiqc_coverage_level": 30,
        "RPKM_bedfile_pan_number": "Pan1974",
        "iva_upload": True,
    },
    "Pan4003": {  # VCP1 viapath
        "mokapipe": True,
        "multiqc_coverage_level": 30,
        "RPKM_bedfile_pan_number": "Pan3624",
        "RPKM_also_analyse": ["Pan4044"],
        "iva_upload": True,
    },
    "Pan4044": {  # VCP1 STG
        "mokapipe": True,
        "multiqc_coverage_level": 30,
        "RPKM_bedfile_pan_number": "Pan3624",
        "RPKM_also_analyse": ["Pan4003"],
        "sapientia_upload": True,
        "sapientia_project": "4203",
        "hsmetrics_bedfile": "Pan4003data.bed",
        "variant_calling_bedfile": "Pan4003data.bed",
        "sambamba_bedfile": "Pan4003dataSambamba.bed",
    },
    "Pan4011": {  # VCP2 viapath
        "mokapipe": True,
        "multiqc_coverage_level": 30,
        "RPKM_bedfile_pan_number": "Pan3614",
        "RPKM_also_analyse": ["Pan4042","Pan4049"],
        "iva_upload": True,
    },
    "Pan4042": {  # VCP2 STG BRCA
        "mokapipe": True,
        "multiqc_coverage_level": 30,
        "RPKM_bedfile_pan_number": "Pan3614",
        "RPKM_also_analyse": ["Pan4011","Pan4049"],
        "sapientia_upload": True,
        "sapientia_project": "1099",
        "mokapipe_haplotype_caller_padding":1,
        "hsmetrics_bedfile": "Pan4011data.bed",
        "variant_calling_bedfile": "Pan4011data.bed",
        "sambamba_bedfile": "Pan4011dataSambamba.bed",
    },
    "Pan4049": {  # VCP2 STG CrCa
        "mokapipe": True,
        "multiqc_coverage_level": 30,
        "RPKM_bedfile_pan_number": "Pan3614",
        "RPKM_also_analyse": ["Pan4011","Pan4042"],
        "sapientia_upload": True,
        "sapientia_project": "4202",
        "mokapipe_haplotype_caller_padding":1,
        "hsmetrics_bedfile": "Pan4011data.bed",
        "variant_calling_bedfile": "Pan4011data.bed",
        "sambamba_bedfile": "Pan4011dataSambamba.bed",
    },
    "Pan3973": {  # VCP3 viapath
        "mokapipe": True,
        "multiqc_coverage_level": 30,
        "RPKM_bedfile_pan_number": "Pan3974",
        "RPKM_also_analyse": ["4043"],
        "iva_upload": True,
    },
    "Pan4043": {  # VCP3 STG
        "mokapipe": True,
        "multiqc_coverage_level": 30,
        "RPKM_bedfile_pan_number": "Pan3974",
        "RPKM_also_analyse": ["3973"],
        "sapientia_upload": True,
        "sapientia_project": "4201",
        "mokapipe_haplotype_caller_padding":1,
        "hsmetrics_bedfile": "Pan3973data.bed",
        "variant_calling_bedfile": "Pan3973data.bed",
        "sambamba_bedfile": "Pan3973dataSambamba.bed",
    },
    "Pan1965": {  # NGSEQ1
        "mokapipe": True,
        "multiqc_coverage_level": 30,
        "RPKM_bedfile_pan_number": "Pan2000",
        "iva_upload": True,
    },
    "Pan1158": {  # NGSEQ2
        "mokapipe": True,
        "multiqc_coverage_level": 30,
        "RPKM_bedfile_pan_number": "Pan2023",
        "iva_upload": True,
    },
    "Pan1159": {  # NGSEQ3
        "mokapipe": True,
        "multiqc_coverage_level": 30,
        "RPKM_bedfile_pan_number": "Pan1973",
        "iva_upload": True,
    },
    "Pan1646": {  # ICTHYOSIS - use same settings as WES and Pan1646 for coverage
        "mokawes": True,
        "iva_upload": True,
        "multiqc_coverage_level": 20,
        "hsmetrics_bedfile": "agilent_sureselect_human_all_exon_v5_b37_targets.bed",
        "variant_calling_bedfile": "agilent_sureselect_human_all_exon_v5_b37_padded.bed",
        "ingenuity_email": wes_email_address,
        "peddy": True,
    },
}

# =====smartsheet API=====
# smartsheet sheet ID
smartsheet_sheetid = 2798264106936196

# API key
smartsheet_api_key_file = "{document_root}/.smartsheet_auth_token".format(
    document_root=document_root
)
with open(smartsheet_api_key_file, "r") as ss_api:
    smartsheet_api_key = ss_api.readline().rstrip()

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
smartsheet_request_headers = {
    "Authorization": "Bearer " + smartsheet_api_key,
    "Content-Type": "application/json",
}
smartsheet_request_url = "https://api.smartsheet.com/2.0/sheets/" + str(smartsheet_sheetid)

# =================turnaround time
# if a task takes more than this amount of time it is out of TAT
allowed_time_for_tasks = 4

# =================== Email server settings
mokaguys_email = "gst-tr.mokaguys@nhs.net"
username_file_path = "{document_root}/.amazon_email_username".format(document_root=document_root)
with open(username_file_path, "r") as username_file:
    user = username_file.readline().rstrip()
pw_file = "{document_root}/.amazon_email_pw".format(document_root=document_root)
with open(pw_file, "r") as email_password_file:
    pw = email_password_file.readline().rstrip()
host = "email-smtp.eu-west-1.amazonaws.com"
port = 587
me = "moka.alerts@gstt.nhs.uk"
you = mokaguys_email
oncology_you = oncology_email
smtp_do_tls = True

# ================ Integrity check
# the filename which holds the checksum results
md5checksum_name = "md5checksum.txt"
# checksum complete statement
checksum_complete_flag = "Checksum result reported"
# statement to write when checksums match
checksum_match = "Checksums match"

# ================ demultiplexing
demultiplex_success_match = r".*Processing completed with 0 errors and 0 warnings.$"
# list of sequencers which require md5 checksums from integrity check to be assessed
sequencers_with_integrity_check = ["NB551068", "NB552085"]

# ================ cluster density calculation
cluster_density_success_statement = "picard.illumina.CollectIlluminaLaneMetrics done"
cluster_density_file_suffix = ".illumina_lane_metrics"
phasing_metrics_file_suffix = ".illumina_phasing_metrics"