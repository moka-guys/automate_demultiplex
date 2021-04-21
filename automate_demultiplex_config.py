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
runfolders = "/media/data3/share/testing/"

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

# command and output to test agilent connector
agilent_connector_cmd = "/opt/agilent/agilentserviceconnector status"
agilent_connector_output = "agilentserviceconnector is running"

# upload agent test response
upload_agent_expected_stdout = "Upload Agent Version:"

# =====Moka settings=====
# Moka IDs for generating SQLs to update the Mokadatabase
# audit trail ID for Mokapipe & congenica
mokapipe_congenica_pipeline_ID = "4316"
# Current MokaWES ID
mokawes_pipeline_ID = "4318"
# MokaAMP ID
mokaamp_pipeline_ID = "4274"
# MokaONC ID
mokaonc_pipeline_ID = "4532"
# MokaONC ID
archerDx_pipeline_ID = "4562"
# SNP Genotyping ID
snp_genotyping_pipeline_ID = "4480"


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
#app_project = "001_ToolsReferenceData:/"
app_project = "project-ByfFPz00jy1fk6PjpZ95F27J:/"
# path to the workflow in the app project

mokapipe_path = "Workflows/GATK3.5_v2.12"
# path to the WES workflow in the app project
mokawes_path = "Workflows/MokaWES_v1.8"

# path to the oncology workflow in the app project
mokaonc_path = "Workflows/Mokaonc_v1.6"
# path to mokaamp
mokaamp_path = "Workflows/MokaAMP_v1.6"
#path to snp_genotyping
snp_genotyping_path = "Workflows/SNP_Genotyping_v1.0.0"
# path to paddy app
peddy_path = "Apps/peddy_v1.5"
# path to multiqc app
multiqc_path = "Apps/multiqc_v1.13"
# path to congenica upload app
congenica_app_path = "Apps/congenica_upload_v1.2"
# placeholder for IVA - will be changed to QCI when available
iva_app_path = ""

# path to app which uploads multiqc report
upload_multiqc_path = "Apps/upload_multiqc_v1.3"
# smartsheet app
smartsheet_path = "Apps/smartsheet_mokapipe_complete_v1.2"
# RPKM path
RPKM_path = "Apps/RPKM_using_conifer_v1.6"
# FastQC app
fastqc_app = "Apps/fastqc_v1.3"
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

#SNPGenotyping workflow inputs
snp_fastqc1 = " -istage-FgPp4V00YkVJVjKF4kYkBF8v.reads=" # FastQC Read 1
snp_fastqc2 = " -istage-FgPp4V00YkVJVjKF4kYkBF90.reads=" # FastQC Read 2
snp_sentieon_stage_id = "stage-FgPp4XQ0YkV48jZG4Py6F55k"
# BED file used to restrict Senteion variant calling
snp_sentieon_targets_bed = " -i%s.targets_bed=" % snp_sentieon_stage_id
# sample name for sentieon app - prevents sample being incorrectly parsed from fastq filename
snp_sentieon_samplename = " -i%s.sample=" % snp_sentieon_stage_id
#bcftools input
snp_bcftools_input = " -istage-FvGkxzj02Bk06Y687Xk8jJp0.in"

# MokaOnc amplivar fastq input
mokaonc_fq_input = " -istage-F7kPz6Q0vpxb0YpjBgQx5f8v.fastqs="
# ingenuity app input for amplivar workflow
mokaonc_ingenuity = " -istage-F5k1Qyj0jy1VKJb2KYqq7fxG.email="

# MokaAMP - stages that may change between samples/panels
mokaamp_fastq_R1_stage = " -istage-FPzGj780jy1g3p1F4F8z4J7V.reads_fastqgz="
mokaamp_fastq_R2_stage = " -istage-FPzGj780jy1g3p1F4F8z4J7V.reads2_fastqgz="
mokaamp_bwa_rg_sample = " -istage-FPzGj780jy1g3p1F4F8z4J7V.read_group_sample="
mokaamp_mokapicard_bed_stage = " -istage-FPzGjV80jy1x97jg607Fg22b.vendor_exome_bedfile="
mokaamp_mokapicard_capturetype_stage = " -istage-FPzGjV80jy1x97jg607Fg22b.Capture_panel="
mokaamp_bamclipper_BEDPE_stage = " -istage-FPzGjJQ0jy1fF6505zFP6zz9.primers="
mokaamp_chanjo_cov_level_stage = " -istage-FPzGjfQ0jy1y01vG60K22qG1.coverage_level="
mokaamp_sambamba_bed_stage = " -istage-FPzGjfQ0jy1y01vG60K22qG1.sambamba_bed="
mokaamp_vardict_bed_stage = " -istage-G0vKZk80GfYkQx86PJGGjz9Y.bedfile="
mokaamp_varscan_bed_stage = " -istage-FPzGjp80jy1V3Jvb5z6xfpfZ.bed_file="
mokaamp_varscan_strandfilter_stage = " -istage-FPzGjp80jy1V3Jvb5z6xfpfZ.strand_filter="
mokaamp_mpileup_cov_level_stage = " -istage-FxypXb807p1zj3g8Jv45Y54P.min_coverage="

# MokaAMP - stages that SHOULDN'@'T may change between samples/panels - these are used to ensure any input files are taken from 001
mokaamp_bwa_reference_stage = " -istage-FPzGj780jy1g3p1F4F8z4J7V.genomeindex_targz=project-ByfFPz00jy1fk6PjpZ95F27J:file-B6ZY4942J35xX095VZyQBk0v"
mokaamp_mokapicard_reference_stage = " -istage-FPzGjV80jy1x97jg607Fg22b.fasta_index=project-ByfFPz00jy1fk6PjpZ95F27J:file-ByYgX700b80gf4ZY1GxvF3Jv"
mokaamp_vardict_reference_stage = " -istage-G0vKZk80GfYkQx86PJGGjz9Y.ref_genome=project-ByfFPz00jy1fk6PjpZ95F27J:file-ByYgX700b80gf4ZY1GxvF3Jv"
mokaamp_varscan_reference_stage = " -istage-FPzGjp80jy1V3Jvb5z6xfpfZ.ref_genome=project-ByfFPz00jy1fk6PjpZ95F27J:file-ByYgX700b80gf4ZY1GxvF3Jv"

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
oncology_IVA_email = "gst-tr.oncology.interpret@nhs.net"  # general oncology email
interpretation_request_email = (
	"gst-tr.interpretation.request@nhs.net"  # email for Interpretation_requests
)
wes_email_address = "gst-tr.wesviapath@nhs.net"  # WES email

# oncology email address for email alerts
oncology_ops_email = "m.neat@nhs.net"


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
congenica_vcf_inputname = " -ivcf="
congenica_bam_inputname = " -ibam="


# =====List of all panel numbers=====
panel_list = [
	"Pan1190", # swift EGFR
	"Pan2684", # swift 57
	"Pan2835", # twist WES
	"Pan4042", # STG VCP2 BRCA
	"Pan4043", # STG VCP3
	"Pan4044", # STG VCP1
	"Pan4049", # STG VCP2 CrCa
	"Pan3174", # WES trio
	"Pan4119", # VCP1 Viapath FH
	"Pan4121", # VCP1 Viapath CF
	"Pan4122", # VCP1 Viapath FGFR
	"Pan4125", # VCP1 Viapath DMD
	"Pan4126", # VCP1 Viapath CADASIL
	"Pan4145", # VCP3 Viapath CMD
	"Pan4146", # VCP3 Viapath CM
	"Pan4149", # VCP2 Viapath BRCA
	"Pan4150", # VCP2 Viapath ovarian
	"Pan4127", # VCP2 Viapath colorectal
	"Pan4129", # VCP2 Viapath lynch
	"Pan4130", # VCP2 Viapath polyposis
	"Pan4132", # VCP3 Viapath R56
	"Pan4134", # VCP3 Viapath R57
	"Pan4136", # VCP3 Viapath R58
	"Pan4137", # VCP3 Viapath R60
	"Pan4138", # VCP3 Viapath R62
	"Pan4143", # VCP3 Viapath R66
	"Pan4144", # VCP3 Viapath R78
	"Pan4151", # VCP3 Viapath R82
	"Pan4314", # VCP3 Viapath R266
	"Pan4351", # VCP3 Viapath R227
	"Pan4387", # VCP3 Viapath R90
	"Pan4390", # VCP3 Viapath R97
	"Pan2764", # OnePGT
	"Pan4009", # SNP Genotyping
	"Pan4396" # ArcherDx
]


# create lists of pan numbers for each capture panel for use with RPKM
#IMPORTANT: Lists below are used by the trend analysis scripts, if changed the trend analysis script will need to be updated
vcp1_panel_list = ["Pan4119","Pan4121","Pan4122","Pan4125","Pan4126","Pan4044"]
vcp2_panel_list = ["Pan4149","Pan4150","Pan4127","Pan4129","Pan4130","Pan4042","Pan4049"]
vcp3_panel_list = ["Pan4132","Pan4134","Pan4136","Pan4137","Pan4138","Pan4143","Pan4144","Pan4145","Pan4146","Pan4151","Pan4043","Pan4314" "Pan4351","Pan4387","Pan4390"]

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
	"snp_genotyping": False,
	"mokapipe": False,
	"mokapipe_haplotype_caller_padding": 0,
	"mokaamp_varscan_strandfilter": True,
	"iva_upload": False,
	"congenica_upload": True,
	"STG": False,
	"oncology": False,
	"destination_command":None,
	"congenica_credentials": "Viapath", # "Viapath" OR "STG"
	"congenica_IR_template": "priority", # 'priority' or 'non-priority'
	"clinical_coverage_depth": None,  # only found in mokamp command
	"multiqc_coverage_level": 30,
	# Note: hsmetrics_bedfile only used when BED file name differs from Pan number
	"hsmetrics_bedfile": None,
	# Note: variant_calling_bedfile only used when BED file differs from Pan number
	"variant_calling_bedfile": None,
	# Note: sambamba_bedfile only used when BED file differs from Pan number
	"sambamba_bedfile": None,
	# Note: mokaamp_bed_PE_input only used when BED file differs from Pan number
	"mokaamp_bed_PE_input": None,
	# Note: mokaamp_variant_calling_bed only used when BED file differs from Pan number
	"mokaamp_variant_calling_bed":None,
	"ingenuity_email": interpretation_request_email,
	"congenica_project": None,
	"peddy": False,
	"archerdx": False,
}

# override default panel settings
panel_settings = {
	"Pan2835": {  # TWIST WES at GSTT
		"mokawes": True,
		"multiqc_coverage_level": 20,
		"hsmetrics_bedfile": "Twist_Exome_RefSeq_CCDS_v1.2_targets.bed",
		"sambamba_bedfile": "Pan493dataSambamba.bed",
		"peddy": True,
	},
	"Pan3174": {  # TWIST WES TRIO at GSTT
		"mokawes": True,
		"multiqc_coverage_level": 20,
		"hsmetrics_bedfile": "Twist_Exome_RefSeq_CCDS_v1.2_targets.bed",
		"sambamba_bedfile": "Pan493dataSambamba.bed",
		"peddy": True,
	},
	"Pan1190": {  # EGFR SWIFT Panel
		"oncology": True,
		"mokaonc": True,
		"mokaamp": True,
		"capture_type": "Amplicon",
		"clinical_coverage_depth": 600,
		"multiqc_coverage_level": 100,
		"mokaamp_bed_PE_input":"Pan3638_PE.bed",
		"mokaamp_variant_calling_bed":"Pan3638_flat.bed",
		"hsmetrics_bedfile": "Pan3638.bed",
		"sambamba_bedfile": "Pan3638Sambamba.bed",
		"destination_command": "MokaAMP_EGFR_trial"
	},
	"Pan2684": {  # 57G SWIFT panel
		"RPKM_bedfile_pan_number": None,
		"mokaamp": True,
		"oncology": True,
		"capture_type": "Amplicon",
		"clinical_coverage_depth": 600,  # only found in mokamp command
		"multiqc_coverage_level": 100,
	},
	"Pan4044": {  # VCP1 STG
		"mokapipe": True,
		"multiqc_coverage_level": 30,
		"RPKM_bedfile_pan_number": "Pan4399",
		"RPKM_also_analyse": vcp1_panel_list,
		"congenica_credentials": "STG",
		"congenica_IR_template":"non-priority",
		"congenica_project": "4203",
		"hsmetrics_bedfile": "Pan4003data.bed",
		"variant_calling_bedfile": "Pan4003data.bed",
		"sambamba_bedfile": "Pan4003dataSambamba.bed",
		"STG": True,
	},
	"Pan4042": {  # VCP2 STG BRCA
		"mokapipe": True,
		"multiqc_coverage_level": 30,
		"RPKM_bedfile_pan_number": "Pan3614",
		"RPKM_also_analyse": vcp2_panel_list,
		"congenica_credentials": "STG",
		"congenica_IR_template":"non-priority",
		"congenica_project": "1099",
		"mokapipe_haplotype_caller_padding":1,
		"hsmetrics_bedfile": "Pan4011data.bed",
		"variant_calling_bedfile": "Pan4011data.bed",
		"sambamba_bedfile": "Pan4011dataSambamba.bed",
	},
	"Pan4009": {  # SNP Genotyping
		"snp_genotyping": True,
		"multiqc_coverage_level": 30,
		"variant_calling_bedfile": "Pan4009.bed",
	},
	"Pan4049": {  # VCP2 STG CrCa
		"mokapipe": True,
		"multiqc_coverage_level": 30,
		"RPKM_bedfile_pan_number": "Pan3614",
		"RPKM_also_analyse": vcp2_panel_list,
		"congenica_credentials": "STG",
		"congenica_IR_template":"non-priority",
		"congenica_project": "4202",
		"mokapipe_haplotype_caller_padding":1,
		"hsmetrics_bedfile": "Pan4011data.bed",
		"variant_calling_bedfile": "Pan4011data.bed",
		"sambamba_bedfile": "Pan4011dataSambamba.bed",
	},
	"Pan4043": {  # VCP3 STG
		"mokapipe": True,
		"multiqc_coverage_level": 30,
		"RPKM_bedfile_pan_number": "Pan3974",
		"RPKM_also_analyse": vcp3_panel_list,
		"congenica_credentials": "STG",
		"congenica_IR_template":"non-priority",
		"congenica_project": "4201",
		"mokapipe_haplotype_caller_padding":1,
		"hsmetrics_bedfile": "Pan4278data.bed",
		"variant_calling_bedfile": "Pan4278data.bed",
		"sambamba_bedfile": "Pan4278dataSambamba.bed",
	},
	"Pan4119": {  #VCP1 R134_Familial hypercholesterolaemia-Familial hypercholesterolaemia Small panel (Viapath)
	    "mokapipe": True,
	    "multiqc_coverage_level": 30,
	    "RPKM_bedfile_pan_number": "Pan4399",
	    "congenica_project": "4664",
	    "RPKM_also_analyse": vcp1_panel_list,
	    "hsmetrics_bedfile": "Pan4397data.bed",
	    "sambamba_bedfile": "Pan4397dataSambamba.bed",
	    "variant_calling_bedfile": "Pan4398data.bed",
	},
	"Pan4121": {  #VCP1 R184 CF (Viapath)
	    "mokapipe": True,
	    "multiqc_coverage_level": 30,
	    "RPKM_bedfile_pan_number": "Pan4399",
	    "congenica_project": "4862",
	    "RPKM_also_analyse": vcp1_panel_list,
	    "hsmetrics_bedfile": "Pan4397data.bed",
	    "sambamba_bedfile": "Pan4397dataSambamba.bed",
	    "variant_calling_bedfile": "Pan4398data.bed",
	},
	"Pan4122": {  #VCP1 R25 FGFR Viapath
	    "mokapipe": True,
	    "multiqc_coverage_level": 30,
	    "RPKM_bedfile_pan_number": "Pan4399",
	    "congenica_project": "5291",
	    "RPKM_also_analyse": vcp1_panel_list,
	    "hsmetrics_bedfile": "Pan4397data.bed",
	    "sambamba_bedfile": "Pan4397dataSambamba.bed",
	    "variant_calling_bedfile": "Pan4398data.bed",
	},
	"Pan4125": {  #VCP1 R73 DMD (Viapath)
	    "mokapipe": True,
	    "multiqc_coverage_level": 30,
	    "RPKM_bedfile_pan_number": "Pan4399",
	    "congenica_project": "4861",
	    "RPKM_also_analyse": vcp1_panel_list,
	    "hsmetrics_bedfile": "Pan4397data.bed",
	    "sambamba_bedfile": "Pan4397dataSambamba.bed",
	    "variant_calling_bedfile": "Pan4398data.bed",
	},
	"Pan4126": {  #VCP1 R337_CADASIL Viapath
	    "mokapipe": True,
	    "multiqc_coverage_level": 30,
	    "RPKM_bedfile_pan_number": "Pan4399",
	    "congenica_project": "4865",
	    "RPKM_also_analyse": vcp1_panel_list,
	    "hsmetrics_bedfile": "Pan4397data.bed",
	    "sambamba_bedfile": "Pan4397dataSambamba.bed",
	    "variant_calling_bedfile": "Pan4398data.bed",
	},
	"Pan4149": {  #VCP2 BRCA (Viapath)
		"mokapipe": True,
		"multiqc_coverage_level": 30,
		"RPKM_bedfile_pan_number": "Pan3614",
		"congenica_project": "4665",
		"RPKM_also_analyse": vcp2_panel_list,
		"hsmetrics_bedfile": "Pan4310data.bed",
		"sambamba_bedfile": "Pan4310dataSambamba.bed",
		"variant_calling_bedfile": "Pan4301data.bed",
	},
	"Pan4150": {  #VCP2 R207 ovarian cancer (Viapath)
	    "mokapipe": True,
	    "multiqc_coverage_level": 30,
	    "RPKM_bedfile_pan_number": "Pan3614",
	    "congenica_project": "4864",
	    "RPKM_also_analyse": vcp2_panel_list,
	    "hsmetrics_bedfile": "Pan4310data.bed",
	    "sambamba_bedfile": "Pan4310dataSambamba.bed",
	    "variant_calling_bedfile": "Pan4301data.bed",
	},
	"Pan4127": {  #VCP2 R209 colorectal cancer (Viapath)
	    "mokapipe": True,
	    "multiqc_coverage_level": 30,
	    "RPKM_bedfile_pan_number": "Pan3614",
	    "congenica_project": "5093",
	    "RPKM_also_analyse": vcp2_panel_list,
	    "hsmetrics_bedfile": "Pan4310data.bed",
	    "sambamba_bedfile": "Pan4310dataSambamba.bed",
	    "variant_calling_bedfile": "Pan4301data.bed",
	},
	"Pan4129": {  #VCP2 R210 Lynch syndrome (Viapath)
	    "mokapipe": True,
	    "multiqc_coverage_level": 30,
	    "RPKM_bedfile_pan_number": "Pan3614",
	    "congenica_project": "5094",
	    "RPKM_also_analyse": vcp2_panel_list,
	    "hsmetrics_bedfile": "Pan4310data.bed",
	    "sambamba_bedfile": "Pan4310dataSambamba.bed",
	    "variant_calling_bedfile": "Pan4301data.bed",
	},
	"Pan4130": {  #VCP2 R211 polyposis (Viapath)
	    "mokapipe": True,
	    "multiqc_coverage_level": 30,
	    "RPKM_bedfile_pan_number": "Pan3614",
	    "congenica_project": "5095",
	    "RPKM_also_analyse": vcp2_panel_list,
	    "hsmetrics_bedfile": "Pan4310data.bed",
	    "sambamba_bedfile": "Pan4310dataSambamba.bed",
	    "variant_calling_bedfile": "Pan4301data.bed",
	},
	"Pan4132": {  #VCP3 R56 (Viapath)
		"mokapipe": True,
		"multiqc_coverage_level": 30,
		"RPKM_bedfile_pan_number": "Pan4362",
		"congenica_project": "5092",
		"RPKM_also_analyse": vcp3_panel_list,
		"hsmetrics_bedfile": "Pan4361data.bed",
		"sambamba_bedfile": "Pan4361dataSambamba.bed",
		"variant_calling_bedfile": "Pan4361data.bed",
	},
	"Pan4134": {  #VCP3 R57 (Viapath)
		"mokapipe": True,
		"multiqc_coverage_level": 30,
		"RPKM_bedfile_pan_number": "Pan4362",
		"congenica_project": "5092",
		"RPKM_also_analyse": vcp3_panel_list,
		"hsmetrics_bedfile": "Pan4361data.bed",
		"sambamba_bedfile": "Pan4361dataSambamba.bed",
		"variant_calling_bedfile": "Pan4361data.bed",
	},
	"Pan4136": {  #VCP3 R58 (Viapath)
		"mokapipe": True,
		"multiqc_coverage_level": 30,
		"RPKM_bedfile_pan_number": "Pan4362",
		"congenica_project": "5092",
		"RPKM_also_analyse": vcp3_panel_list,
		"hsmetrics_bedfile": "Pan4361data.bed",
		"sambamba_bedfile": "Pan4361dataSambamba.bed",
		"variant_calling_bedfile": "Pan4361data.bed",
	},
	"Pan4137": {  #VCP3 R60 (Viapath)
		"mokapipe": True,
		"multiqc_coverage_level": 30,
		"RPKM_bedfile_pan_number": "Pan4362",
		"congenica_project": "5092",
		"RPKM_also_analyse": vcp3_panel_list,
		"hsmetrics_bedfile": "Pan4361data.bed",
		"sambamba_bedfile": "Pan4361dataSambamba.bed",
		"variant_calling_bedfile": "Pan4361data.bed",
	},
	"Pan4138": {  #VCP3 R62 (Viapath)
		"mokapipe": True,
		"multiqc_coverage_level": 30,
		"RPKM_bedfile_pan_number": "Pan4362",
		"congenica_project": "5092",
		"RPKM_also_analyse": vcp3_panel_list,
		"hsmetrics_bedfile": "Pan4361data.bed",
		"sambamba_bedfile": "Pan4361dataSambamba.bed",
		"variant_calling_bedfile": "Pan4361data.bed",
	},
	"Pan4143": {  #VCP3 R66 (Viapath)
		"mokapipe": True,
		"multiqc_coverage_level": 30,
		"RPKM_bedfile_pan_number": "Pan4362",
		"congenica_project": "5092",
		"RPKM_also_analyse": vcp3_panel_list,
		"hsmetrics_bedfile": "Pan4361data.bed",
		"sambamba_bedfile": "Pan4361dataSambamba.bed",
		"variant_calling_bedfile": "Pan4361data.bed",
	},
	"Pan4144": {  #VCP3 R78 (Viapath)
		"mokapipe": True,
		"multiqc_coverage_level": 30,
		"RPKM_bedfile_pan_number": "Pan4362",
		"congenica_project": "5092",
		"RPKM_also_analyse": vcp3_panel_list,
		"hsmetrics_bedfile": "Pan4361data.bed",
		"sambamba_bedfile": "Pan4361dataSambamba.bed",
		"variant_calling_bedfile": "Pan4361data.bed",
	},
	"Pan4145": {  #VCP3 R79 - CMD (Viapath)
		"mokapipe": True,
		"multiqc_coverage_level": 30,
		"RPKM_bedfile_pan_number": "Pan4362",
		"congenica_project": "4666",
		"RPKM_also_analyse": vcp3_panel_list,
		"hsmetrics_bedfile": "Pan4361data.bed",
		"sambamba_bedfile": "Pan4361dataSambamba.bed",
		"variant_calling_bedfile": "Pan4361data.bed",
	},
	"Pan4146": {  #VCP3 R81 CM (Viapath)
		"mokapipe": True,
		"multiqc_coverage_level": 30,
		"RPKM_bedfile_pan_number": "Pan4362",
		"congenica_project": "4666",
		"RPKM_also_analyse": vcp3_panel_list,
		"hsmetrics_bedfile": "Pan4361data.bed",
		"sambamba_bedfile": "Pan4361dataSambamba.bed",
		"variant_calling_bedfile": "Pan4361data.bed",
	},
	"Pan4151": {  #VCP3 R82 limb girdle (Viapath)
		"mokapipe": True,
		"multiqc_coverage_level": 30,
		"RPKM_bedfile_pan_number": "Pan4362",
		"congenica_project": "5092",
		"RPKM_also_analyse": vcp3_panel_list,
		"hsmetrics_bedfile": "Pan4361data.bed",
		"sambamba_bedfile": "Pan4361dataSambamba.bed",
		"variant_calling_bedfile": "Pan4361data.bed",
	},
	"Pan2764": { # OnePGT
		"onePGT": True,
		"congenica_upload": False
	},
	"Pan4351": { #VCP3 R227 (Viapath)
		"mokapipe": True,
		"multiqc_coverage_level": 30,
		"RPKM_bedfile_pan_number": "Pan4362",
		"congenica_project": "5522",
		"RPKM_also_analyse": vcp3_panel_list,
		"hsmetrics_bedfile": "Pan4361data.bed",
		"sambamba_bedfile": "Pan4361dataSambamba.bed",
		"variant_calling_bedfile": "Pan4361data.bed",
	},
	"Pan4387": { #VCP3 R90 Bleeding and platelet disorders (Viapath)
		"mokapipe": True,
		"multiqc_coverage_level": 30,
		"RPKM_bedfile_pan_number": "Pan4362",
		"congenica_project": "4699",
		"RPKM_also_analyse": vcp3_panel_list,
		"hsmetrics_bedfile": "Pan4361data.bed",
		"sambamba_bedfile": "Pan4361dataSambamba.bed",
		"variant_calling_bedfile": "Pan4361data.bed",
	},
	"Pan4390": { #VCP3 R97 Thrombophilia with a likely monogenic cause (Viapath)
		"mokapipe": True,
		"multiqc_coverage_level": 30,
		"RPKM_bedfile_pan_number": "Pan4362",
		"congenica_project": "4699",
		"RPKM_also_analyse": vcp3_panel_list,
		"hsmetrics_bedfile": "Pan4361data.bed",
		"sambamba_bedfile": "Pan4361dataSambamba.bed",
		"variant_calling_bedfile": "Pan4361data.bed",
	},
	"Pan4314": { #VCP3 R266 (Viapath)
		"mokapipe": True,
		"multiqc_coverage_level": 30,
		"RPKM_bedfile_pan_number": "Pan4362",
		"congenica_project": "5290",
		"RPKM_also_analyse": vcp3_panel_list,
		"hsmetrics_bedfile": "Pan4361data.bed",
		"sambamba_bedfile": "Pan4361dataSambamba.bed",
		"variant_calling_bedfile": "Pan4361data.bed",
	},
	"Pan4396": { #ArcherDx
		"archerdx": True,
		"congenica_upload": False,
	}
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
oncology_you = oncology_ops_email
WES_sample_name_email_list = ["DNAdutyscientist@viapath.co.uk", "Suzanne.lillis@viapath.co.uk", mokaguys_email]
smtp_do_tls = True

# ================ Integrity check
# the filename which holds the checksum results
md5checksum_name = "md5checksum.txt"
# checksum complete statement
checksum_complete_flag = "Checksum result reported"
# statement to write when checksums match
checksum_match = "Checksums match"

# ================ cluster density calculation
cluster_density_success_statement = "picard.illumina.CollectIlluminaLaneMetrics done"
cluster_density_error_statement = "PicardException"
cluster_density_file_suffix = ".illumina_lane_metrics"
phasing_metrics_file_suffix = ".illumina_phasing_metrics"
novaseq_id = "A01229"

# ================ demultiplexing
demultiplex_success_match = r".*Processing completed with 0 errors and 0 warnings.$"
# list of sequencers which require md5 checksums from integrity check to be assessed
sequencers_with_integrity_check = ["NB551068", "NB552085", novaseq_id]
bcl2fastq_stats_filename = "Stats.json"
bcl2fastq_stats_path = os.path.join(fastq_folder,"Stats")

# ================ onePGT
agilent_upload_folder = "/media/data1/share/agilent_OnePGT_uploads/"
max_filesize_in_bytes = 5368709120 # 5GB (max size is 10GB per pair of fastq)
max_filesize_in_GB = "5GB"
rsync_logfile = "rsync_output.txt"
