# coding=utf-8
"""
Automate demultiplex configuration.

The variables defined in this module are required by scripts in the automate_demultiplex repository
(https://github.com/moka-guys/automate_demultiplex)
"""

import os

# ================ GENERAL ======================================================================

testing = True # Set debug mode

# Root of folder containing apps, automate_demultiplexing_logfiles and development_area scripts
# (2 levels up from this file)
document_root = "/".join(os.path.dirname(os.path.realpath(__file__)).split("/")[:-2])

runfolder_pattern = "^[0-9]{6}.*$" # Runfolders start with 6 digits

# Path to run folders - use testing flag to determine folders
if not testing:
	runfolders = "/media/data3/share"
else:
	# When testing use a different directory
	runfolders = "/media/data3/share/testing/"


samplesheets_dir = os.path.join(runfolders,"samplesheets") # Samplesheet folder

# Directories to be ignored when looping through runfolders
ignore_directories = ["samplesheets"]

novaseq_id = "A01229"

fastq_folder = "/Data/Intensities/BaseCalls" # Path to fastq files

# ================ Samplesheet Verification (samplesheet_validator.py) ===================================

sequencer_ids = ["NB551068", "NB552085", "M02353", "M02631", "A01229"]
runtype_list = ["NGS", "ADX", "ONC", "SNP", "PGT", "TSO", "LRPCR"]


# ================ DEMULTIPLEXING (demultiplex.py) ======================================================

# Integrity check
md5checksum_name = "md5checksum.txt" # File holding checksum results
checksum_complete_flag = "Checksum result reported" # Checksum complete statement
checksum_match = "Checksums match" # Statement to write when checksums match
# Sequencers requiring md5 checksums from integrity check to be assessed
sequencers_with_integrity_check = ["NB551068", "NB552085", novaseq_id]

# Demultiplex
demultiplex_test_folder = ["999999_M02353_0496_000000000-D8ICF", "999999_NB552085_0077_WESPIPECAN",
						   "999999_A01229_0010_AHY5TWDICP"]
# files for checking NGS runfolders before demultiplexing
file_complete_run = "RTAComplete.txt"
file_demultiplexing = "bcl2fastq2_output.log"
file_demultiplexing_old = "demultiplexlog.txt"

bcl2fastq = "/usr/local/bcl2fastq2-v2.20.0.422/bin/bcl2fastq" # Path to bcl2fastq
bcl2fastq_stats_filename = "Stats.json"
bcl2fastq_stats_path = os.path.join(fastq_folder,"Stats")

demultiplex_success_match = r".*Processing completed with 0 errors and 0 warnings.$"
demultiplexing_log_file_TSO500_message = "TSO500 run. Does not need demultiplexing locally"


# ================ UPLOAD AND SETOFF WORKFLOWS ===========================================================

reference_sample_ids = ["NA12878", "136819"] # NA12878 identifiers to exclude from congenica upload

# ---- Filepaths -----------------------------------------------------------------------------------------

# Path to log file which records the output of the upload agent
upload_and_setoff_workflow_logfile = \
	"{document_root}/automate_demultiplexing_logfiles/upload_agent_script_logfiles/".format(document_root=document_root)


upload_started_file = "DNANexus_upload_started.txt" # Name of log file which records the output of the upload agent

# Path to DNAnexus run command log file
DNA_Nexus_workflow_logfolder = \
	"{document_root}/automate_demultiplexing_logfiles/dx_run_commands/".format(document_root=document_root)

# Log folder containing project creation logs
DNA_Nexus_project_creation_logfolder = \
	"{document_root}/automate_demultiplexing_logfiles/nexus_project_creation_scripts/" \
	"create_nexus_project_".format(document_root=document_root)

# Folder containing demultiplex logs
demultiplex_logfiles = \
	"{document_root}/automate_demultiplexing_logfiles/Demultiplexing_log_files/".format(document_root=document_root)

# Path to upload agent
upload_agent_path = "{document_root}/apps/dnanexus-upload-agent-1.5.17-linux/ua".format(document_root=document_root)

# Path to backup_runfolder script
backup_runfolder_script = "/usr/local/src/mokaguys/apps/workstation_housekeeping/backup_runfolder.py"

# Backup runfolder folder
backup_runfolder_logfile = \
	"{document_root}/automate_demultiplexing_logfiles/backup_runfolder_logfiles".format(document_root=document_root)

# ---- Commands -----------------------------------------------------------------------------------------
upload_agent_test_command = " --version"
ua_error = "Error Message: 'Could not resolve: api.dnanexus.com"
sdk_source_cmd = "/etc/profile.d/dnanexus.environment.sh"
dx_sdk_test = "source {};dx --version".format(sdk_source_cmd) # Command to test dx toolkit

# ---- Expected output strings ---------------------------------------------------------------------------
backup_runfolder_success = "backup_runfolder INFO - END"
backup_runfolder_error = "backup_runfolder.UAcaller ERROR"
dx_sdk_test_expected_stdout = "dx v0.2" # Expected result from testing
upload_agent_expected_stdout = "Upload Agent Version:" # Upload agent test response

# ---- Cluster density strings -------------------------------------------------------------------------
cluster_density_success_statement = "picard.illumina.CollectIlluminaLaneMetrics done"
cluster_density_error_statement = "PicardException"
cluster_density_file_suffix = ".illumina_lane_metrics"
phasing_metrics_file_suffix = ".illumina_phasing_metrics"


# ===== MOKA SETTINGS ===================================================================================

# Moka IDs for generating SQLs to update the Mokadatabase (audit trail) ---------------------------------
mokapipe_congenica_pipeline_ID = "5137" # Mokapipe & congenica ID
mokawes_pipeline_ID = "5078" # MokaWES ID
mokaamp_pipeline_ID = "4851" # MokaAMP ID
archerDx_pipeline_ID = "4562" # Archer ID
mokasnp_pipeline_ID = "5091" # MokaSNP ID
mokacan_pipeline_ID = "4728" # mokacan pipeline ID
TSO_pipeline_ID = "5095" # TSO500 pipeline ID

# ---- Moka WES test status -----------------------------------------------------------------------------
mokastat_nextsq_ID = "1202218804" # Test Status = NextSEQ sequencing
mokastatus_dataproc_ID = "1202218805" # Test Status = Data Processing


# ===== DNANEXUS SETTINGS ===============================================================================

NexusProjectPrefix = "002_" # Project to upload run folder into
project_success = 'Created new project called "%s"' # Success statement when creating project
app_project = "project-ByfFPz00jy1fk6PjpZ95F27J:/" # 001_ToolsReferenceData (contains apps/workflows)

# ---- Paths to workflows and apps in the project ------------------------------------------------------
mokapipe_path = "Workflows/GATK3.5_v2.16"
mokawes_path = "Workflows/MokaWES_v1.8"
mokaamp_path = "Workflows/MokaAMP_v2.2"
mokacan_path = "Workflows/MokaCAN_v1.0"
mokasnp_path = "Workflows/MokaSNP_v1.2.0"
peddy_path = "Apps/peddy_v1.5"
multiqc_path = "Apps/multiqc_v1.15.0"
congenica_app_path = "Apps/congenica_upload_v1.3.2"
congenica_SFTP_upload_app = "applet-GFfJpj80jy1x1Bz1P1Bk3vQf"

# ---- TSO500 app --------------------------------------------------------------------------------------
tso500_app = "applet-GBKvYFQ0jy1Vx4zJ126gX4xp" # Apps/TSO500_v1.4.0
tso500_app_name = "TSO500_v1.4.0"
tso500_docker_image = "project-ByfFPz00jy1fk6PjpZ95F27J:file-Fz9Zyx00b5j8xKVkKv4fZ6JB"

# ----- TSO500_output_parser app -----------------------------------------------------------------------
tso500_output_parser_app = "applet-GBKvX5j0jy1kK8jj9F7jjVY7" # Apps/tso500_output_parser_v1.2.0
# Inputs for tso500_output_parser_app
coverage_app_id = "project-ByfFPz00jy1fk6PjpZ95F27J:applet-G6vyyf00jy1kPkX9PJ1YkxB1"
fastqc_app_id = "project-ByfFPz00jy1fk6PjpZ95F27J:applet-FBPFfkj0jy1Q114YGQ0yQX8Y"
sompy_app_id = "project-ByfFPz00jy1fk6PjpZ95F27J:applet-G9yPb780jy1p660k6yBvQg07"
multiqc_app_id = "project-ByfFPz00jy1fk6PjpZ95F27J:applet-G7QB6zj0jy1z1ZV1P5VZBj9p"
upload_multiqc_app_id = "project-ByfFPz00jy1fk6PjpZ95F27J:applet-G2XY8QQ0p7kzvPZBJGFygP6f"
TSO500_output_parser_coverage_commands = "'-imerge_overlapping_mate_reads=true -iexclude_failed_quality_control=true " \
										 "-iexclude_duplicate_reads=true -imin_base_qual=%s -imin_mapping_qual=%s'"

# ----- MultiQC Upload App ----------------------------------------------------------------------------
upload_multiqc_path = "Apps/upload_multiqc_v1.4.0"
RPKM_path = "Apps/RPKM_using_conifer_v1.6"
fastqc_app = "Apps/fastqc_v1.3"
bedfile_folder = "Data/BED/"
prod_organisation = "org-viapath_prod" # DNAnexus organisation to create the project within

# ===== istages : DNANEXUS WORKFLOW INPUTS =============================================================

# ----- DNAnexus authentication token ------------------------------------------------------------------
nexus_api_key_file = "{document_root}/.dnanexus_auth_token".format(document_root=document_root)
with open(nexus_api_key_file, "r") as nexus_api:
	Nexus_API_Key = nexus_api.readline().rstrip()

# ----- DNAnexus users --------------------------------------------------------------------------------
view_users = ["org-viapath_prod", "InterpretationRequest"] # DNAnexus users with view access to project
admin_users = ["mokaguys"] # DNAnexus users with admin access to project

# ----- Inputs shared across workflows ----------------------------------------------------------------
peddy_project_input = " -iproject_for_peddy="
multiqc_project_input = " -iproject_for_multiqc="
multiqc_coverage_level_input = " -icoverage_level="
multiqc_html_output = "multiqc_report"
upload_multiqc_input = " -imultiqc_html="

# ----- Email addresses -------------------------------------------------------------------------------
# If sending to multiple addresses provide in a list
mokaguys_email = "gst-tr.mokaguys@nhs.net"
if testing:
	# Oncology email address for email alerts
	oncology_ops_email = mokaguys_email
	WES_sample_name_email_list = [mokaguys_email]
else:
	# Oncology email address for email alerts
	oncology_ops_email = "m.neat@nhs.net"
	WES_sample_name_email_list = ["gst-tr.ViapathGeneticsAdmin@nhs.net", "Suzanne.lillis@viapath.co.uk",
								  mokaguys_email, "eblab@gstt.nhs.uk", "lu.liu@viapath.co.uk"]

# ----- MokaPIPE workflow inputs -----------------------------------------------------------------------
mokapipe_filter_vcf_with_bedfile_stage = "stage-G5Kpgv80zB02Q64zFf94G05F"
mokapipe_gatk_human_exome_stage = "stage-F28y4qQ0jy1fkqfy5v2b8byx"
mokapipe_fastqc1 = " -istage-Bz3YpP80jy1Y1pZKbZ35Bp0x.reads="  # FastQC Read 1
mokapipe_fastqc2 = " -istage-Bz3YpP80jy1x7G5QfG3442gX.reads="  # FastQC Read 2
mokapipe_bwa_rg_sample = " -istage-Byz9BJ80jy1k2VB9xVXBp0Fg.read_group_sample="  # BWA rg samplename
mokapipe_bwa_ref_genome = " -istage-Byz9BJ80jy1k2VB9xVXBp0Fg.genomeindex_targz=%s"  # BWA reference genome
mokapipe_mokapicard_vendorbed_input = " -istage-F9GK4QQ0jy1qj14PPZxxq3VG.vendor_exome_bedfile="  # HSMetrics Bed file
mokapipe_mokapicard_capturetype_stage = " -istage-F9GK4QQ0jy1qj14PPZxxq3VG.Capture_panel=%s"
mokapipe_haplotype_padding_input = " -i{}.padding=".format(mokapipe_gatk_human_exome_stage)
mokapipe_haplotype_vcf_output_format = " -i{}.output_format=both".format(mokapipe_gatk_human_exome_stage)
mokapipe_filter_vcf_with_bedfile_bed_input = " -i.bedfile=".format(mokapipe_filter_vcf_with_bedfile_stage)
mokapipe_vcf_output_name = "filtered_vcf"
mokapipe_bam_output_name = "bam"
mokapipe_happy_skip = " -istage-G8V205j0fB6QGKXQ2gZ5pB1z.skip=%s"
mokapipe_happy_prefix = " -istage-G8V205j0fB6QGKXQ2gZ5pB1z.prefix=%s"
mokapipe_sambamba_bed_input = " -istage-F35zBKQ0jy1XpfzYPZY4bgX6.sambamba_bed="
mokapipe_sambamba_min_base_qual = " -istage-F35zBKQ0jy1XpfzYPZY4bgX6.min_base_qual=10"
mokapipe_sambamba_min_mapping_qual = " -istage-F35zBKQ0jy1XpfzYPZY4bgX6.min_mapping_qual=20"
mokapipe_sambamba_coverage_level = " -istage-F35zBKQ0jy1XpfzYPZY4bgX6.coverage_level=30"
mokapipe_sambamba_filter_cmds = " -istage-F35zBKQ0jy1XpfzYPZY4bgX6.additional_filter_commands='not " \
								"(unmapped or secondary_alignment)'"
mokapipe_sambamba_exclude_duplicates = " -istage-F35zBKQ0jy1XpfzYPZY4bgX6.exclude_duplicate_reads=true"
mokapipe_sambamba_exclude_failed_qual = " -istage-F35zBKQ0jy1XpfzYPZY4bgX6.exclude_failed_quality_control=true"
mokapipe_sambamba_count_overlapping_mates = " -istage-F35zBKQ0jy1XpfzYPZY4bgX6.merge_overlapping_mate_reads=true"
mokapipe_fhPRS_skip = " -istage-G9BfkZQ0fB6jZY7v1PfJ81F6.skip=false"
mokapipe_fhPRS_bedfile_input = " -istage-G9BfkZQ0fB6jZY7v1PfJ81F6.BEDfile="
mokapipe_FH_humanexome_instance_type= "mem3_ssd1_v2_x8" # Required when creating gVCFs
mokapipe_GATK_human_exome_appletID = "applet-FYZ097j0jy1ZZPx30GykP63J"
# Set timeout policy of 6 hours to gatk app and add the jobtimeoutexceeded reason to the auto restart list
mokapipe_FH_GATK_timeout_args = " --extra-args '{\"timeoutPolicyByExecutable\": {\"%s\": {\"*\":{\"hours\": 6}}}, " \
								"\"executionPolicy\": {\"restartOn\": {\"JobTimeoutExceeded\":1,\"JMInternalError\":" \
								" 1, \"UnresponsiveWorker\": 2, \"ExecutionError\":1}}}'" % \
								mokapipe_GATK_human_exome_appletID

FH_PRS_bedfile_name = "Pan4909.bed" # Mokapipe FH_PRS BED file

# RPKM inputs
rpkm_bedfile_input = " -ibedfile="
rpkm_project_input = " -iproject_name="
rpkm_bamfiles_to_download_input = " -ibamfile_pannumbers="

# ----- MokaWES workflow inputs --------------------------------------------------------------------------
wes_fastqc1 = " -istage-Ff0P5Jj0GYKY717pKX3vX8Z3.reads="  # FastQC Read 1
wes_fastqc2 = " -istage-Ff0P5V00GYKyJfpX5bqX69Yg.reads="  # FastQC Read
wes_picard_bedfile = " -istage-Ff0P5pQ0GYKVBB0g1FG27BV8.vendor_exome_bedfile=" # Bedfile for hs metrics
sentieon_stage_id = "stage-Ff0P73j0GYKX41VkF3j62F9j"
wes_sambamba_bedfile = " -istage-Ff0P82Q0GYKQ4j8b4gXzjqxX.sambamba_bed="
# Sample name for sentieon app - prevents sample being incorrectly parsed from fastq filename
wes_sentieon_samplename = " -i%s.sample=" % sentieon_stage_id
# BED file used to restrict Senteion variant calling
wes_sentieon_targets_bed = " -i%s.targets_bed=" % sentieon_stage_id

# ----- MokaSNP workflow inputs --------------------------------------------------------------------------
snp_fastqc1 = " -istage-FgPp4V00YkVJVjKF4kYkBF8v.reads=" # FastQC Read 1
snp_fastqc2 = " -istage-FgPp4V00YkVJVjKF4kYkBF90.reads=" # FastQC Read 2
snp_sentieon_stage_id = "stage-FgPp4XQ0YkV48jZG4Py6F55k"
# BED file used to restrict Senteion variant calling
snp_sentieon_targets_bed = " -i%s.targets_bed=" % snp_sentieon_stage_id
# Sample name for sentieon app - prevents sample being incorrectly parsed from fastq filename
snp_sentieon_samplename = " -i%s.sample=" % snp_sentieon_stage_id

# ----- MokaAMP workflow inputs --------------------------------------------------------------------------
# Stages that may change between samples/panels
mokaamp_fastq_R1_stage = " -istage-FPzGj780jy1g3p1F4F8z4J7V.reads_fastqgz="
mokaamp_fastq_R2_stage = " -istage-FPzGj780jy1g3p1F4F8z4J7V.reads2_fastqgz="
mokaamp_bwa_rg_sample = " -istage-FPzGj780jy1g3p1F4F8z4J7V.read_group_sample="
mokaamp_mokapicard_bed_stage = " -istage-FPzGjV80jy1x97jg607Fg22b.vendor_exome_bedfile="
mokaamp_mokapicard_capturetype_stage = " -istage-FPzGjV80jy1x97jg607Fg22b.Capture_panel="
mokaamp_ampliconfilter_BEDPE_stage = " -istage-FPzGjJQ0jy1fF6505zFP6zz9.PE_BED="
mokaamp_chanjo_cov_level_stage = " -istage-FPzGjfQ0jy1y01vG60K22qG1.coverage_level="
mokaamp_sambamba_bed_stage = " -istage-FPzGjfQ0jy1y01vG60K22qG1.sambamba_bed="
mokaamp_vardict_bed_stage = " -istage-G0vKZk80GfYkQx86PJGGjz9Y.bedfile="
mokaamp_vardict_samplename_stage = " -istage-G0vKZk80GfYkQx86PJGGjz9Y.sample_name=vardict_"
mokaamp_varscan_bed_stage = " -istage-FPzGjp80jy1V3Jvb5z6xfpfZ.bed_file="
mokaamp_varscan_samplename_stage = " -istage-FPzGjp80jy1V3Jvb5z6xfpfZ.samplename=varscan_"
mokaamp_varscan_strandfilter_stage = " -istage-FPzGjp80jy1V3Jvb5z6xfpfZ.strand_filter="
mokaamp_mpileup_cov_level_stage = " -istage-FxypXb807p1zj3g8Jv45Y54P.min_coverage="

# Stages with inputs that shouldn't change between samples/panels (project ID ensures inputs taken from 001_Tools)
mokaamp_bwa_reference_stage = " -istage-FPzGj780jy1g3p1F4F8z4J7V.genomeindex_targz=" \
							  "project-ByfFPz00jy1fk6PjpZ95F27J:file-B6ZY4942J35xX095VZyQBk0v"
mokaamp_mokapicard_reference_stage = " -istage-FPzGjV80jy1x97jg607Fg22b.fasta_index=" \
									 "project-ByfFPz00jy1fk6PjpZ95F27J:file-ByYgX700b80gf4ZY1GxvF3Jv"
mokaamp_vardict_reference_stage = " -istage-G0vKZk80GfYkQx86PJGGjz9Y.ref_genome=" \
								  "project-ByfFPz00jy1fk6PjpZ95F27J:file-ByYgX700b80gf4ZY1GxvF3Jv"
mokaamp_varscan_reference_stage = " -istage-FPzGjp80jy1V3Jvb5z6xfpfZ.ref_genome=" \
								  "project-ByfFPz00jy1fk6PjpZ95F27J:file-ByYgX700b80gf4ZY1GxvF3Jv"
mokaamp_email_message = \
	"If both MokaAMP and MokaOnc (amplivar) have been run, please record the version of MokaOnc used."

# ----- MokaCAN workflow inputs -------------------------------------------------------------------
# Stages that may change between samples
mokacan_fastqc_r1_stage = " -istage-FPzGj6Q0jy1fF6505zFP6zz5.reads="
mokacan_fastqc_r2_stage = " -istage-FPzGj5j0jy1x97jg607Fg229.reads="
mokacan_picard_bedfile_stage = " -istage-FPzGjV80jy1x97jg607Fg22b.vendor_exome_bedfile="
mokacan_picard_capturetype_stage = " -istage-FPzGjV80jy1x97jg607Fg22b.Capture_panel="
mokacan_sambamba_bedfile_stage = " -istage-FPzGjfQ0jy1y01vG60K22qG1.sambamba_bed="
mokacan_vardict_bedfile_stage = " -istage-FPzGjgj0jy1Q2JJF2zYx5J5k.bedfile="
mokacan_sentieon_sample_name_stage = " -istage-FgYgB2Q087fjzvxy9f4q1K8X.sample="
mokacan_sambamba_coverage_level_stage = " -istage-FPzGjfQ0jy1y01vG60K22qG1.coverage_level="
mokacan_vardict_sample_name_stage = " -istage-FPzGjgj0jy1Q2JJF2zYx5J5k.sample_name=vardict_"
mokacan_varscan_bedfile_stage = " -istage-FPzGjp80jy1V3Jvb5z6xfpfZ.bed_file="

# Stages with inputs that shouldn't change between samples/panels (project ID ensures inputs taken from 001_Tools)
mokacan_senteion_bwa_reference_stage = " -istage-FgYgB2Q087fjzvxy9f4q1K8X.genomebwaindex_targz=" \
									   "project-ByfFPz00jy1fk6PjpZ95F27J:file-B6ZY4942J35xX095VZyQBk0v"
mokacan_senteion_reference_stage = " -istage-FgYgB2Q087fjzvxy9f4q1K8X.genome_fastagz=" \
								   "project-ByfFPz00jy1fk6PjpZ95F27J:file-B6ZY7VG2J35Vfvpkj8y0KZ01"
mokacan_picard_reference_stage = " -istage-FPzGjV80jy1x97jg607Fg22b.fasta_index=" \
								 "project-ByfFPz00jy1fk6PjpZ95F27J:file-ByYgX700b80gf4ZY1GxvF3Jv"
mokacan_vardict_reference_stage = " -istage-FPzGjgj0jy1Q2JJF2zYx5J5k.ref_genome=" \
								  "project-ByfFPz00jy1fk6PjpZ95F27J:file-ByYgX700b80gf4ZY1GxvF3Jv"
mokacan_varscan_reference_stage = " -istage-FPzGjp80jy1V3Jvb5z6xfpfZ.ref_genome=" \
								  "project-ByfFPz00jy1fk6PjpZ95F27J:file-ByYgX700b80gf4ZY1GxvF3Jv"

# ----- TSO500 workflow inputs -------------------------------------------------------------------
# TSO500 stage ids
TSO500_docker_image_stage = " -iTSO500_ruo="
TSO500_runfolder_tar_stage = " -irun_folder="
TSO500_samplesheet_stage = " -isamplesheet="
TSO500_analysis_options_stage = " -ianalysis_options="
# TSO500 output parser stage ids
TSO500_output_parser_project_name_stage = " -iproject_name="
TSO500_output_parser_project_id_stage = " -iproject_id="
TSO500_output_parser_job_id_stage = " -itso500_jobid="
TSO500_output_parser_coverage_bedfile_id_stage = " -icoverage_bedfile_id="
TSO500_output_parser_coverage_app_id_stage = " -icoverage_app_id="
TSO500_output_parser_fastqc_app_id_stage = " -ifastqc_app_id="
TSO500_output_parser_sompy_app_id_stage = " -isompy_app_id="
TSO500_output_parser_multiqc_app_id_stage = " -imultiqc_app_id="
TSO500_output_parser_upload_multiqc_app_id_stage = " -iupload_multiqc_app_id="
TSO500_output_parser_coverage_commands_stage = " -icoverage_commands="
TSO500_output_parser_coverage_level_stage = " -icoverage_level="
TSO500_output_parser_multiqc_coverage_level_stage = " -imultiqc_coverage_level="
# App instance types
TSO500_analysis_instance_high_throughput = "mem1_ssd1_v2_x72"
TSO500_analysis_instance_low_throughput = "mem1_ssd1_v2_x36"


# ===== DECISION SUPPORT SCRIPT (decision_support_tool_inputs.py) ========================================

decision_support_tool_input_script = "decision_support_tool_inputs.py"
mokawes_sentieon_bam_output_name = "mappings_bam"
mokawes_sentieon_bai_output_name = "mappings_bam_bai"
mokawes_sentieon_vcf_output_name = "variants_vcf"
congenica_vcf_inputname = " -ivcf="
congenica_bam_inputname = " -ibam="
congenica_samplename = " -ianalysis_name="


# ================ PANEL NUMBERS AND PANEL PROPERTIES ====================================================

# ----- List of all panel numbers ----
panel_list = [
	"Pan4081", # Swift EGFR
	"Pan4082", # Swift 57
	"Pan2835", # Twist WES
	"Pan4940", # Twist WES for EB lab
	"Pan4042", # STG VCP2 BRCA
	"Pan4043", # STG VCP3
	"Pan4044", # STG VCP1
	"Pan4049", # STG VCP2 CrCa
	"Pan3174", # WES trio
	"Pan4119", # VCP1 Viapath_R134(FH)
	"Pan4121", # VCP1 Viapath_R184(CF)
	"Pan4122", # VCP1 Viapath_R25(FGFR)
	"Pan4125", # VCP1 Viapath_R73(DMD)
	"Pan4126", # VCP1 Viapath_R337(CADASIL)
	"Pan4974", # VCP1 Viapath (Molecular Haemostasis) R112
	"Pan4975", # VCP1 Viapath (Molecular Haemostasis) R115
	"Pan4976", # VCP1 Viapath (Molecular Haemostasis) R116
	"Pan4977", # VCP1 Viapath (Molecular Haemostasis) R117
	"Pan4978", # VCP1 Viapath (Molecular Haemostasis) R118
	"Pan4979", # VCP1 Viapath (Molecular Haemostasis) R119
	"Pan4980", # VCP1 Viapath (Molecular Haemostasis) R120
	"Pan4981", # VCP1 Viapath (Molecular Haemostasis) R121
	"Pan4982", # VCP1 Viapath (Molecular Haemostasis) R122
	"Pan4983", # VCP1 Viapath (Molecular Haemostasis) R123
	"Pan4984", # VCP1 Viapath (Molecular Haemostasis) R124
	"Pan4145", # VCP3 Viapath_R79(CMD)
	"Pan4146", # VCP3 Viapath_R81(CM)
	"Pan4149", # VCP2 Viapath_R208(BRCA)
	"Pan4150", # VCP2 Viapath_R207(ovarian)
	"Pan4127", # VCP2 Viapath_R209(colorectal)
	"Pan4129", # VCP2 Viapath_R210(lynch)
	"Pan4964", # VCP2 Viapath_R259(nijmegen)
	"Pan4130", # VCP2 Viapath_R211(polyposis)
	"Pan4132", # VCP3 Viapath_R56
	"Pan4134", # VCP3 Viapath_R57
	"Pan4136", # VCP3 Viapath_R58
	"Pan4137", # VCP3 Viapath_R60
	"Pan4138", # VCP3 Viapath_R62
	"Pan4143", # VCP3 Viapath_R66
	"Pan4144", # VCP3 Viapath_R78
	"Pan4151", # VCP3 Viapath_R82
	"Pan4314", # VCP3 Viapath_R229
	"Pan4351", # VCP3 Viapath_R227
	"Pan4387", # VCP3 Viapath_R90
	"Pan4390", # VCP3 Viapath_R97
	"Pan4009", # MokaSNP
	"Pan4396", # ArcherDx
	"Pan4579", # VCP2_M1.1(somatic)
	"Pan4574", # VCP2_M1.2(somatic)
	"Pan4969", # TSO500 - no UTRS TERT promotor
	"Pan5085", # TSO500 High throughput Synnovis. no UTRS TERT promotor
	"Pan5086", # TSO500 High throughput BSPS. no UTRS TERT promotor
	"Pan4821", # VCP1 STG R134_FH
	"Pan4822", # VCP1 STG R184_CF
	"Pan4823", # VCP1 STG R25_FGFR
	"Pan4824", # VCP1 STG R73_DMD
	"Pan4825", # VCP1 STG R337_CADASIL
	"Pan4816", # VCP2 STG R208 BRCA
	"Pan4817", # VCP2 STG R207 ovarian
	"Pan4818", # VCP2 STG R209 colorectal
	"Pan4819", # VCP2 STG R210 lynch
	"Pan4820", # VCP2 STG R211 polyposis
	"Pan4826", # VCP3 STG R56
	"Pan4827", # VCP3 STG R57
	"Pan4828", # VCP3 STG R58
	"Pan4829", # VCP3 STG R60
	"Pan4830", # VCP3 STG R62
	"Pan4831", # VCP3 STG R66
	"Pan4832", # VCP3 STG R78
	"Pan4833", # VCP3 STG R79 CMD
	"Pan4834", # VCP3 STG R81 CM
	"Pan4835", # VCP3 STG R82 limb girdle
	"Pan4836", # VCP3 STG R229
	"Pan5007", # LRPCR Via R207 PMS2
	"Pan5008", # LRPCR STG R207 PMS2
	"Pan5009", # LRPCR Via R208 CHEK2
	"Pan5010", # LRPCR STG R208 CHEK2
	"Pan5011", # LRPCR Via R210 PMS2
	"Pan5012", # LRPCR STG R210 PMS2
	"Pan5013", # LRPCR Via R211 PMS2
	"Pan5014", # LRPCR STG R211 PMS2
	"Pan5015", # LRPCR Via R71 SMN1
	"Pan5016", # LRPCR Via R239	IKBKG
]

# Create lists of pan numbers for each capture panel for use with RPKM
# IMPORTANT: Lists below are used by the trend analysis scripts. If changed, trend analysis script needs updating
vcp1_panel_list = ["Pan4119","Pan4121","Pan4122","Pan4125","Pan4126","Pan4044","Pan4821","Pan4822","Pan4823",
				   "Pan4824","Pan4825","Pan4974","Pan4975","Pan4976","Pan4977","Pan4978","Pan4979","Pan4980",
				   "Pan4981","Pan4982","Pan4983","Pan4984"]
vcp2_panel_list = ["Pan4149","Pan4150","Pan4127","Pan4129","Pan4130","Pan4042","Pan4049","Pan4816","Pan4817",
				   "Pan4818","Pan4819","Pan4820","Pan4964"]
vcp3_panel_list = ["Pan4132","Pan4134","Pan4136","Pan4137","Pan4138","Pan4143","Pan4144","Pan4145","Pan4146",
				   "Pan4151","Pan4043","Pan4314","Pan4351","Pan4387","Pan4390","Pan4826","Pan4827","Pan4828",
				   "Pan4829","Pan4830","Pan4831","Pan4832","Pan4833","Pan4834","Pan4835","Pan4836"]
WES_panel_lists = ["Pan2835","Pan3174","Pan4940"]
SNP_panel_lists = ["Pan4009"]
archer_panel_list = ["Pan4396"]
swift_57G_panel_list = ["Pan4082"]
swift_egfr_panel_list = ["Pan4081"]
mokacan_panel_list = ["Pan4579","Pan4574"]
LRPCR_panel_list = ["Pan5007","Pan5008","Pan5009","Pan5010","Pan5011","Pan5012","Pan5013","Pan5014","Pan5015","Pan5016"]
tso500_panel_list = ["Pan4969","Pan5085","Pan5086"] # Settings from first item used when setting off dx run commands


default_panel_properties = {
	"UMI": False,
	"UMI_bcl2fastq": None,  # E.g. Y145,I8,Y9I8,Y145
	"RPKM_bedfile_pan_number": None,
	"RPKM_also_analyse": None,  # List of Pan Numbers indicating which BAM files to download
	"mokawes": False,
	"joint_variant_calling": False,
	"mokaamp": False,
	"capture_type": "Hybridisation",  # "Amplicon" or "Hybridisation"
	"mokacan": False,
	"mokasnp": False,
	"mokapipe": False,
	"mokapipe_haplotype_caller_padding": 0,
	"FH": False,
	"FH_PRS_bedfile": FH_PRS_bedfile_name,
	"mokaamp_varscan_strandfilter": True,
	"iva_upload": False,
	"congenica_upload": True,
	"STG": False,
	"oncology": False,
	"destination_command":None,
	"congenica_credentials": "Viapath", # "Viapath" OR "STG"
	"congenica_IR_template": "priority", # 'priority' or 'non-priority'
	"clinical_coverage_depth": None,  # Only found in mokamp command
	"multiqc_coverage_level": 30,
	"hsmetrics_bedfile": None, # Only used when BED file name differs from Pan number
	"variant_calling_bedfile": None, # Only used when BED file differs from Pan number
	"sambamba_bedfile": None, # Only used when BED file differs from Pan number
	"mokaamp_bed_PE_input": None, # Only used when BED file differs from Pan number
	"mokaamp_variant_calling_bed": None, # Only used when BED file differs from Pan number
	"congenica_project": None,
	"peddy": False,
	"archerdx": False,
	"TSO500": False,
	"TSO500_high_throughput": False,
	"drylab_dnanexus_id": None,
	"masked_reference":False
}

# Override default panel settings
panel_settings = {
	"Pan2835": {  # TWIST WES at GSTT
		"mokawes": True,
		"multiqc_coverage_level": 20,
		"hsmetrics_bedfile": "Twist_Exome_RefSeq_CCDS_v1.2_targets.bed",
		"sambamba_bedfile": "Pan493dataSambamba.bed",
		"peddy": True
	},
	"Pan4940": {  # TWIST WES for EB lab
		"mokawes": True,
		"multiqc_coverage_level": 20,
		"hsmetrics_bedfile": "Twist_Exome_RefSeq_CCDS_v1.2_targets.bed",
		"sambamba_bedfile": "Pan493dataSambamba.bed",
		"peddy": True,
		"congenica_project": "4697",
	},
	"Pan3174": {  # TWIST WES TRIO at GSTT
		"mokawes": True,
		"multiqc_coverage_level": 20,
		"hsmetrics_bedfile": "Twist_Exome_RefSeq_CCDS_v1.2_targets.bed",
		"sambamba_bedfile": "Pan493dataSambamba.bed",
		"peddy": True,
		"congenica_upload": True
	},
	"Pan4081": {  # EGFR SWIFT Panel
		"mokaamp": True,
		"oncology": True,
		"capture_type": "Amplicon",
		"clinical_coverage_depth": 600,  # Only found in mokamp command
		"multiqc_coverage_level": 100,
        "hsmetrics_bedfile": "Pan4081.bed",
		"sambamba_bedfile": "Pan4081Sambamba.bed",
	},
	"Pan4082": {  # 57G SWIFT panel
		"mokaamp": True,
		"oncology": True,
		"capture_type": "Amplicon",
		"clinical_coverage_depth": 600,  # Only found in mokamp command
		"multiqc_coverage_level": 100,
        "hsmetrics_bedfile": "Pan4082.bed",
		"sambamba_bedfile": "Pan4082Sambamba.bed",
	},
	"Pan4044": {  # VCP1 STG
		"mokapipe": True,
		"multiqc_coverage_level": 30,
		"RPKM_bedfile_pan_number": "Pan4399",
		"RPKM_also_analyse": vcp1_panel_list,
		"congenica_credentials": "STG",
		"congenica_IR_template":"non-priority",
		"congenica_project": "4203",
		"hsmetrics_bedfile": "Pan4397data.bed",
		"variant_calling_bedfile": "Pan4398data.bed",
		"sambamba_bedfile": "Pan4397dataSambamba.bed",
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
		"hsmetrics_bedfile": "Pan4949data.bed",
		"variant_calling_bedfile": "Pan4948data.bed",
		"sambamba_bedfile": "Pan4949dataSambamba.bed",
	},
	"Pan4009": {  # MokaSNP
		"mokasnp": True,
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
		"hsmetrics_bedfile": "Pan4949data.bed",
		"variant_calling_bedfile": "Pan4948data.bed",
		"sambamba_bedfile": "Pan4949dataSambamba.bed",
	},
	"Pan4043": {  # VCP3 STG
		"mokapipe": True,
		"multiqc_coverage_level": 30,
		"RPKM_bedfile_pan_number": "Pan3974",
		"RPKM_also_analyse": vcp3_panel_list,
		"congenica_credentials": "STG",
		"congenica_IR_template":"non-priority",
		"congenica_project": "4201",
		"hsmetrics_bedfile": "Pan4535data.bed",
		"variant_calling_bedfile": "Pan4535data.bed",
		"sambamba_bedfile": "Pan4535dataSambamba.bed",
	},
	"Pan4119": {  # VCP1 R134_Familial hypercholesterolaemia-Familial hypercholesterolaemia Small panel (Viapath)
	    "mokapipe": True,
	    "multiqc_coverage_level": 30,
	    "RPKM_bedfile_pan_number": "Pan4399",
	    "congenica_project": "4664",
	    "RPKM_also_analyse": vcp1_panel_list,
	    "hsmetrics_bedfile": "Pan4397data.bed",
	    "sambamba_bedfile": "Pan4397dataSambamba.bed",
	    "variant_calling_bedfile": "Pan4398data.bed",
	    "FH": True,
	},
	"Pan4121": {  # VCP1 R184 CF (Viapath)
	    "mokapipe": True,
	    "multiqc_coverage_level": 30,
	    "RPKM_bedfile_pan_number": "Pan4399",
	    "congenica_project": "4862",
	    "RPKM_also_analyse": vcp1_panel_list,
	    "hsmetrics_bedfile": "Pan4397data.bed",
	    "sambamba_bedfile": "Pan4397dataSambamba.bed",
	    "variant_calling_bedfile": "Pan4398data.bed",
	},
	"Pan4122": {  # VCP1 R25 FGFR Viapath
	    "mokapipe": True,
	    "multiqc_coverage_level": 30,
	    "RPKM_bedfile_pan_number": "Pan4399",
	    "congenica_project": "5291",
	    "RPKM_also_analyse": vcp1_panel_list,
	    "hsmetrics_bedfile": "Pan4397data.bed",
	    "sambamba_bedfile": "Pan4397dataSambamba.bed",
	    "variant_calling_bedfile": "Pan4398data.bed",
	},
	"Pan4125": {  # VCP1 R73 DMD (Viapath)
	    "mokapipe": True,
	    "multiqc_coverage_level": 30,
	    "RPKM_bedfile_pan_number": "Pan4399",
	    "congenica_project": "4861",
	    "RPKM_also_analyse": vcp1_panel_list,
	    "hsmetrics_bedfile": "Pan4397data.bed",
	    "sambamba_bedfile": "Pan4397dataSambamba.bed",
	    "variant_calling_bedfile": "Pan4398data.bed",
	},
	"Pan4126": {  # VCP1 R337_CADASIL Viapath
	    "mokapipe": True,
	    "multiqc_coverage_level": 30,
	    "RPKM_bedfile_pan_number": "Pan4399",
	    "congenica_project": "4865",
	    "RPKM_also_analyse": vcp1_panel_list,
	    "hsmetrics_bedfile": "Pan4397data.bed",
	    "sambamba_bedfile": "Pan4397dataSambamba.bed",
	    "variant_calling_bedfile": "Pan4398data.bed",
	},
	"Pan4974": {  # VCP1 Viapath (Molecular Haemostasis) R112
	    "mokapipe": True,
	    "multiqc_coverage_level": 30,
	    "RPKM_bedfile_pan_number": "Pan4399",
	    "congenica_project": "4699",
	    "RPKM_also_analyse": vcp1_panel_list,
	    "hsmetrics_bedfile": "Pan4397data.bed",
	    "sambamba_bedfile": "Pan4397dataSambamba.bed",
	    "variant_calling_bedfile": "Pan4398data.bed",
	},
	"Pan4975": {  # VCP1 Viapath (Molecular Haemostasis) R115
	    "mokapipe": True,
	    "multiqc_coverage_level": 30,
	    "RPKM_bedfile_pan_number": "Pan4399",
	    "congenica_project": "4699",
	    "RPKM_also_analyse": vcp1_panel_list,
	    "hsmetrics_bedfile": "Pan4397data.bed",
	    "sambamba_bedfile": "Pan4397dataSambamba.bed",
	    "variant_calling_bedfile": "Pan4398data.bed",
	},
	"Pan4976": {  # VCP1 Viapath (Molecular Haemostasis) R116
	    "mokapipe": True,
	    "multiqc_coverage_level": 30,
	    "RPKM_bedfile_pan_number": "Pan4399",
	    "congenica_project": "4699",
	    "RPKM_also_analyse": vcp1_panel_list,
	    "hsmetrics_bedfile": "Pan4397data.bed",
	    "sambamba_bedfile": "Pan4397dataSambamba.bed",
	    "variant_calling_bedfile": "Pan4398data.bed",
	},
	"Pan4977": {  # VCP1 Viapath (Molecular Haemostasis) R117
	    "mokapipe": True,
	    "multiqc_coverage_level": 30,
	    "RPKM_bedfile_pan_number": "Pan4399",
	    "congenica_project": "4699",
	    "RPKM_also_analyse": vcp1_panel_list,
	    "hsmetrics_bedfile": "Pan4397data.bed",
	    "sambamba_bedfile": "Pan4397dataSambamba.bed",
	    "variant_calling_bedfile": "Pan4398data.bed",
	},
	"Pan4978": {  # VCP1 Viapath (Molecular Haemostasis) R118
	    "mokapipe": True,
	    "multiqc_coverage_level": 30,
	    "RPKM_bedfile_pan_number": "Pan4399",
	    "congenica_project": "4699",
	    "RPKM_also_analyse": vcp1_panel_list,
	    "hsmetrics_bedfile": "Pan4397data.bed",
	    "sambamba_bedfile": "Pan4397dataSambamba.bed",
	    "variant_calling_bedfile": "Pan4398data.bed",
	},
	"Pan4979": {  # VCP1 Viapath (Molecular Haemostasis) R119
	    "mokapipe": True,
	    "multiqc_coverage_level": 30,
	    "RPKM_bedfile_pan_number": "Pan4399",
	    "congenica_project": "4699",
	    "RPKM_also_analyse": vcp1_panel_list,
	    "hsmetrics_bedfile": "Pan4397data.bed",
	    "sambamba_bedfile": "Pan4397dataSambamba.bed",
	    "variant_calling_bedfile": "Pan4398data.bed",
	},
	"Pan4980": {  # VCP1 Viapath (Molecular Haemostasis) R120
	    "mokapipe": True,
	    "multiqc_coverage_level": 30,
	    "RPKM_bedfile_pan_number": "Pan4399",
	    "congenica_project": "4699",
	    "RPKM_also_analyse": vcp1_panel_list,
	    "hsmetrics_bedfile": "Pan4397data.bed",
	    "sambamba_bedfile": "Pan4397dataSambamba.bed",
	    "variant_calling_bedfile": "Pan4398data.bed",
	},
	"Pan4981": {  # VCP1 Viapath (Molecular Haemostasis) R121
	    "mokapipe": True,
	    "multiqc_coverage_level": 30,
	    "RPKM_bedfile_pan_number": "Pan4399",
	    "congenica_project": "4699",
	    "RPKM_also_analyse": vcp1_panel_list,
	    "hsmetrics_bedfile": "Pan4397data.bed",
	    "sambamba_bedfile": "Pan4397dataSambamba.bed",
	    "variant_calling_bedfile": "Pan4398data.bed",
	},
	"Pan4982": {  # VCP1 Viapath (Molecular Haemostasis) R122
	    "mokapipe": True,
	    "multiqc_coverage_level": 30,
	    "RPKM_bedfile_pan_number": "Pan4399",
	    "congenica_project": "4699",
	    "RPKM_also_analyse": vcp1_panel_list,
	    "hsmetrics_bedfile": "Pan4397data.bed",
	    "sambamba_bedfile": "Pan4397dataSambamba.bed",
	    "variant_calling_bedfile": "Pan4398data.bed",
	},
	"Pan4983": {  # VCP1 Viapath (Molecular Haemostasis) R123
	    "mokapipe": True,
	    "multiqc_coverage_level": 30,
	    "RPKM_bedfile_pan_number": "Pan4399",
	    "congenica_project": "4699",
	    "RPKM_also_analyse": vcp1_panel_list,
	    "hsmetrics_bedfile": "Pan4397data.bed",
	    "sambamba_bedfile": "Pan4397dataSambamba.bed",
	    "variant_calling_bedfile": "Pan4398data.bed",
	},
	"Pan4984": {  # VCP1 Viapath (Molecular Haemostasis) R124
	    "mokapipe": True,
	    "multiqc_coverage_level": 30,
	    "RPKM_bedfile_pan_number": "Pan4399",
	    "congenica_project": "4699",
	    "RPKM_also_analyse": vcp1_panel_list,
	    "hsmetrics_bedfile": "Pan4397data.bed",
	    "sambamba_bedfile": "Pan4397dataSambamba.bed",
	    "variant_calling_bedfile": "Pan4398data.bed",
	},
	"Pan4149": {  # VCP2 BRCA (Viapath)
	    "mokapipe": True,
	    "multiqc_coverage_level": 30,
	    "RPKM_bedfile_pan_number": "Pan3614",
	    "congenica_project": "4665",
	    "RPKM_also_analyse": vcp2_panel_list,
	    "hsmetrics_bedfile": "Pan4949data.bed",
	    "sambamba_bedfile": "Pan4949dataSambamba.bed",
	    "variant_calling_bedfile": "Pan4948data.bed",
	},
	"Pan4964": {  # VCP2 R259 nijmegen breakage (Viapath)
	    "mokapipe": True,
	    "multiqc_coverage_level": 30,
	    "RPKM_bedfile_pan_number": "Pan3614",
	    "congenica_project": "9118",
	    "RPKM_also_analyse": vcp2_panel_list,
	    "hsmetrics_bedfile": "Pan4949data.bed",
	    "sambamba_bedfile": "Pan4949dataSambamba.bed",
	    "variant_calling_bedfile": "Pan4948data.bed",
	},
	"Pan4150": {  # VCP2 R207 ovarian cancer (Viapath)
	    "mokapipe": True,
	    "multiqc_coverage_level": 30,
	    "RPKM_bedfile_pan_number": "Pan3614",
	    "congenica_project": "4864",
	    "RPKM_also_analyse": vcp2_panel_list,
	    "hsmetrics_bedfile": "Pan4949data.bed",
	    "sambamba_bedfile": "Pan4949dataSambamba.bed",
	    "variant_calling_bedfile": "Pan4948data.bed",
	},
	"Pan4127": {  # VCP2 R209 colorectal cancer (Viapath)
	    "mokapipe": True,
	    "multiqc_coverage_level": 30,
	    "RPKM_bedfile_pan_number": "Pan3614",
	    "congenica_project": "5093",
	    "RPKM_also_analyse": vcp2_panel_list,
	    "hsmetrics_bedfile": "Pan4949data.bed",
	    "sambamba_bedfile": "Pan4949dataSambamba.bed",
	    "variant_calling_bedfile": "Pan4948data.bed",
	},
	"Pan4129": {  # VCP2 R210 Lynch syndrome (Viapath)
	    "mokapipe": True,
	    "multiqc_coverage_level": 30,
	    "RPKM_bedfile_pan_number": "Pan3614",
	    "congenica_project": "5094",
	    "RPKM_also_analyse": vcp2_panel_list,
	    "hsmetrics_bedfile": "Pan4949data.bed",
	    "sambamba_bedfile": "Pan4949dataSambamba.bed",
	    "variant_calling_bedfile": "Pan4948data.bed",
	},
	"Pan4130": {  # VCP2 R211 polyposis (Viapath)
	    "mokapipe": True,
	    "multiqc_coverage_level": 30,
	    "RPKM_bedfile_pan_number": "Pan3614",
	    "congenica_project": "5095",
	    "RPKM_also_analyse": vcp2_panel_list,
	    "hsmetrics_bedfile": "Pan4949data.bed",
	    "sambamba_bedfile": "Pan4949dataSambamba.bed",
	    "variant_calling_bedfile": "Pan4948data.bed",
	},
	"Pan4132": {  # VCP3 R56 (Viapath)
		"mokapipe": True,
		"multiqc_coverage_level": 30,
		"RPKM_bedfile_pan_number": "Pan4362",
		"congenica_project": "5092",
		"RPKM_also_analyse": vcp3_panel_list,
		"hsmetrics_bedfile": "Pan4535data.bed",
		"sambamba_bedfile": "Pan4535dataSambamba.bed",
		"variant_calling_bedfile": "Pan4535data.bed",
	},
	"Pan4134": {  # VCP3 R57 (Viapath)
		"mokapipe": True,
		"multiqc_coverage_level": 30,
		"RPKM_bedfile_pan_number": "Pan4362",
		"congenica_project": "5092",
		"RPKM_also_analyse": vcp3_panel_list,
		"hsmetrics_bedfile": "Pan4535data.bed",
		"sambamba_bedfile": "Pan4535dataSambamba.bed",
		"variant_calling_bedfile": "Pan4535data.bed"
	},
	"Pan4136": {  # VCP3 R58 (Viapath)
		"mokapipe": True,
		"multiqc_coverage_level": 30,
		"RPKM_bedfile_pan_number": "Pan4362",
		"congenica_project": "5092",
		"RPKM_also_analyse": vcp3_panel_list,
		"hsmetrics_bedfile": "Pan4535data.bed",
		"sambamba_bedfile": "Pan4535dataSambamba.bed",
		"variant_calling_bedfile": "Pan4535data.bed",
	},
	"Pan4137": {  # VCP3 R60 (Viapath)
		"mokapipe": True,
		"multiqc_coverage_level": 30,
		"RPKM_bedfile_pan_number": "Pan4362",
		"congenica_project": "5092",
		"RPKM_also_analyse": vcp3_panel_list,
		"hsmetrics_bedfile": "Pan4535data.bed",
		"sambamba_bedfile": "Pan4535dataSambamba.bed",
		"variant_calling_bedfile": "Pan4535data.bed",
	},
	"Pan4138": {  # VCP3 R62 (Viapath)
		"mokapipe": True,
		"multiqc_coverage_level": 30,
		"RPKM_bedfile_pan_number": "Pan4362",
		"congenica_project": "5092",
		"RPKM_also_analyse": vcp3_panel_list,
		"hsmetrics_bedfile": "Pan4535data.bed",
		"sambamba_bedfile": "Pan4535dataSambamba.bed",
		"variant_calling_bedfile": "Pan4535data.bed",
	},
	"Pan4143": {  #VCP3 R66 (Viapath)
		"mokapipe": True,
		"multiqc_coverage_level": 30,
		"RPKM_bedfile_pan_number": "Pan4362",
		"congenica_project": "5092",
		"RPKM_also_analyse": vcp3_panel_list,
		"hsmetrics_bedfile": "Pan4535data.bed",
		"sambamba_bedfile": "Pan4535dataSambamba.bed",
		"variant_calling_bedfile": "Pan4535data.bed",
	},
	"Pan4144": {  # VCP3 R78 (Viapath)
		"mokapipe": True,
		"multiqc_coverage_level": 30,
		"RPKM_bedfile_pan_number": "Pan4362",
		"congenica_project": "5092",
		"RPKM_also_analyse": vcp3_panel_list,
		"hsmetrics_bedfile": "Pan4535data.bed",
		"sambamba_bedfile": "Pan4535dataSambamba.bed",
		"variant_calling_bedfile": "Pan4535data.bed",
	},
	"Pan4145": {  # VCP3 R79 - CMD (Viapath)
		"mokapipe": True,
		"multiqc_coverage_level": 30,
		"RPKM_bedfile_pan_number": "Pan4362",
		"congenica_project": "4666",
		"RPKM_also_analyse": vcp3_panel_list,
		"hsmetrics_bedfile": "Pan4535data.bed",
		"sambamba_bedfile": "Pan4535dataSambamba.bed",
		"variant_calling_bedfile": "Pan4535data.bed",
	},
	"Pan4146": {  # VCP3 R81 CM (Viapath)
		"mokapipe": True,
		"multiqc_coverage_level": 30,
		"RPKM_bedfile_pan_number": "Pan4362",
		"congenica_project": "4666",
		"RPKM_also_analyse": vcp3_panel_list,
		"hsmetrics_bedfile": "Pan4535data.bed",
		"sambamba_bedfile": "Pan4535dataSambamba.bed",
		"variant_calling_bedfile": "Pan4535data.bed",
	},
	"Pan4151": {  # VCP3 R82 limb girdle (Viapath)
		"mokapipe": True,
		"multiqc_coverage_level": 30,
		"RPKM_bedfile_pan_number": "Pan4362",
		"congenica_project": "5092",
		"RPKM_also_analyse": vcp3_panel_list,
		"hsmetrics_bedfile": "Pan4535data.bed",
		"sambamba_bedfile": "Pan4535dataSambamba.bed",
		"variant_calling_bedfile": "Pan4535data.bed",
	},
	"Pan4351": { # VCP3 R227 (Viapath)
		"mokapipe": True,
		"multiqc_coverage_level": 30,
		"RPKM_bedfile_pan_number": "Pan4362",
		"congenica_project": "5522",
		"RPKM_also_analyse": vcp3_panel_list,
		"hsmetrics_bedfile": "Pan4535data.bed",
		"sambamba_bedfile": "Pan4535dataSambamba.bed",
		"variant_calling_bedfile": "Pan4535data.bed",
	},
	"Pan4387": { # VCP3 R90 Bleeding and platelet disorders (Viapath)
		"mokapipe": True,
		"multiqc_coverage_level": 30,
		"RPKM_bedfile_pan_number": "Pan4362",
		"congenica_project": "4699",
		"RPKM_also_analyse": vcp3_panel_list,
		"hsmetrics_bedfile": "Pan4535data.bed",
		"sambamba_bedfile": "Pan4535dataSambamba.bed",
		"variant_calling_bedfile": "Pan4535data.bed",
	},
	"Pan4390": { # VCP3 R97 Thrombophilia with a likely monogenic cause (Viapath)
		"mokapipe": True,
		"multiqc_coverage_level": 30,
		"RPKM_bedfile_pan_number": "Pan4362",
		"congenica_project": "4699",
		"RPKM_also_analyse": vcp3_panel_list,
		"hsmetrics_bedfile": "Pan4535data.bed",
		"sambamba_bedfile": "Pan4535dataSambamba.bed",
		"variant_calling_bedfile": "Pan4535data.bed",
	},
	"Pan4314": { # VCP3 R229 (Viapath)
		"mokapipe": True,
		"multiqc_coverage_level": 30,
		"RPKM_bedfile_pan_number": "Pan4362",
		"congenica_project": "5290",
		"RPKM_also_analyse": vcp3_panel_list,
		"hsmetrics_bedfile": "Pan4535data.bed",
		"sambamba_bedfile": "Pan4535dataSambamba.bed",
		"variant_calling_bedfile": "Pan4535data.bed",
	},
	"Pan4396": { # ArcherDx
		"archerdx": True,
		"congenica_upload": False,
	},
	"Pan4574" :{ # Somatic VCP2 M1.2
		"mokacan": True,
		"congenica_upload": False,
		"variant_calling_bedfile": "Pan4577data.bed",
		"hsmetrics_bedfile": "Pan4949data.bed",
		"clinical_coverage_depth" : 200,
	},
	"Pan4579" :{ # Somatic VCP2 M1.1
		"mokacan": True,
		"congenica_upload": False,
		"variant_calling_bedfile": "Pan4578data.bed",
		"hsmetrics_bedfile": "Pan4949data.bed",
		"clinical_coverage_depth" : 200,
	},
	"Pan4969" : { # TSO500 no UTRs. TERT promotor
		# NOTE - TSO500 output parser settings are taken from the first pan number listed in tso500_panel_list
		"TSO500": True,
		"sambamba_bedfile": "Pan4969dataSambamba.bed",
		"clinical_coverage_depth" : 100,
		"multiqc_coverage_level": 100,
		"coverage_min_basecall_qual":25,
		"coverage_min_mapping_qual":30,
	},
	"Pan5085" : { # TSO500 High throughput Synnovis. no UTRs. TERT promotor
		# NOTE - TSO500 output parser settings are taken from the first pan number listed in tso500_panel_list
		"TSO500": True,
		"TSO500_high_throughput": True,
		"sambamba_bedfile": "Pan4969dataSambamba.bed",
		"clinical_coverage_depth" : 100,
		"multiqc_coverage_level": 100,
		"coverage_min_basecall_qual":25,
		"coverage_min_mapping_qual":30,
	},
	"Pan5086" : { # TSO500 High throughput BSPS. no UTRs. TERT promotor
		# NOTE - TSO500 output parser settings are taken from the first pan number listed in tso500_panel_list
		"TSO500": True,
		"TSO500_high_throughput": True,
		"sambamba_bedfile": "Pan4969dataSambamba.bed",
		"clinical_coverage_depth" : 100,
		"multiqc_coverage_level": 100,
		"coverage_min_basecall_qual":25,
		"coverage_min_mapping_qual":30,
		"drylab_dnanexus_id": None # can state this when we know it.
	},
	"Pan4821": {  # VCP1 STG R134_FH
		"mokapipe": True,
		"multiqc_coverage_level": 30,
		"RPKM_bedfile_pan_number": "Pan4399",
		"RPKM_also_analyse": vcp1_panel_list,
		"congenica_credentials": "STG",
		"congenica_IR_template":"non-priority",
		"congenica_project": "4203",
		"hsmetrics_bedfile": "Pan4397data.bed",
		"variant_calling_bedfile": "Pan4398data.bed",
		"sambamba_bedfile": "Pan4397dataSambamba.bed",
		"STG": True,
		"FH": True,
	},
	"Pan4822": {  # VCP1 STG R184_CF
		"mokapipe": True,
		"multiqc_coverage_level": 30,
		"RPKM_bedfile_pan_number": "Pan4399",
		"RPKM_also_analyse": vcp1_panel_list,
		"congenica_credentials": "STG",
		"congenica_IR_template":"non-priority",
		"congenica_project": "4203",
		"hsmetrics_bedfile": "Pan4397data.bed",
		"variant_calling_bedfile": "Pan4398data.bed",
		"sambamba_bedfile": "Pan4397dataSambamba.bed",
		"STG": True,
	},
	"Pan4823": {  # VCP1 STG R25_FGFR
		"mokapipe": True,
		"multiqc_coverage_level": 30,
		"RPKM_bedfile_pan_number": "Pan4399",
		"RPKM_also_analyse": vcp1_panel_list,
		"congenica_credentials": "STG",
		"congenica_IR_template":"non-priority",
		"congenica_project": "4203",
		"hsmetrics_bedfile": "Pan4397data.bed",
		"variant_calling_bedfile": "Pan4398data.bed",
		"sambamba_bedfile": "Pan4397dataSambamba.bed",
		"STG": True,
	},
	"Pan4824": {  # VCP1 STG R73_DMD
		"mokapipe": True,
		"multiqc_coverage_level": 30,
		"RPKM_bedfile_pan_number": "Pan4399",
		"RPKM_also_analyse": vcp1_panel_list,
		"congenica_credentials": "STG",
		"congenica_IR_template":"non-priority",
		"congenica_project": "4203",
		"hsmetrics_bedfile": "Pan4397data.bed",
		"variant_calling_bedfile": "Pan4398data.bed",
		"sambamba_bedfile": "Pan4397dataSambamba.bed",
		"STG": True,
	},
	"Pan4825": {  # VCP1 STG R337_cadasil
		"mokapipe": True,
		"multiqc_coverage_level": 30,
		"RPKM_bedfile_pan_number": "Pan4399",
		"RPKM_also_analyse": vcp1_panel_list,
		"congenica_credentials": "STG",
		"congenica_IR_template":"non-priority",
		"congenica_project": "4203",
		"hsmetrics_bedfile": "Pan4397data.bed",
		"variant_calling_bedfile": "Pan4398data.bed",
		"sambamba_bedfile": "Pan4397dataSambamba.bed",
		"STG": True,
	},
	"Pan4826": {  # VCP3 STG R56
		"mokapipe": True,
		"multiqc_coverage_level": 30,
		"RPKM_bedfile_pan_number": "Pan3974",
		"RPKM_also_analyse": vcp3_panel_list,
		"congenica_credentials": "STG",
		"congenica_IR_template":"non-priority",
		"congenica_project": "4201",
		"hsmetrics_bedfile": "Pan4535data.bed",
		"variant_calling_bedfile": "Pan4535data.bed",
		"sambamba_bedfile": "Pan4535dataSambamba.bed",
	},
	"Pan4827": {  # VCP3 STG R57
		"mokapipe": True,
		"multiqc_coverage_level": 30,
		"RPKM_bedfile_pan_number": "Pan3974",
		"RPKM_also_analyse": vcp3_panel_list,
		"congenica_credentials": "STG",
		"congenica_IR_template":"non-priority",
		"congenica_project": "4201",
		"hsmetrics_bedfile": "Pan4535data.bed",
		"variant_calling_bedfile": "Pan4535data.bed",
		"sambamba_bedfile": "Pan4535dataSambamba.bed",
	},
	"Pan4828": {  # VCP3 STG R58
		"mokapipe": True,
		"multiqc_coverage_level": 30,
		"RPKM_bedfile_pan_number": "Pan3974",
		"RPKM_also_analyse": vcp3_panel_list,
		"congenica_credentials": "STG",
		"congenica_IR_template":"non-priority",
		"congenica_project": "4201",
		"hsmetrics_bedfile": "Pan4535data.bed",
		"variant_calling_bedfile": "Pan4535data.bed",
		"sambamba_bedfile": "Pan4535dataSambamba.bed",
	},
	"Pan4829": {  # VCP3 STG R60
		"mokapipe": True,
		"multiqc_coverage_level": 30,
		"RPKM_bedfile_pan_number": "Pan3974",
		"RPKM_also_analyse": vcp3_panel_list,
		"congenica_credentials": "STG",
		"congenica_IR_template":"non-priority",
		"congenica_project": "4201",
		"hsmetrics_bedfile": "Pan4535data.bed",
		"variant_calling_bedfile": "Pan4535data.bed",
		"sambamba_bedfile": "Pan4535dataSambamba.bed",
	},
	"Pan4830": {  # VCP3 STG R62
		"mokapipe": True,
		"multiqc_coverage_level": 30,
		"RPKM_bedfile_pan_number": "Pan3974",
		"RPKM_also_analyse": vcp3_panel_list,
		"congenica_credentials": "STG",
		"congenica_IR_template":"non-priority",
		"congenica_project": "4201",
		"hsmetrics_bedfile": "Pan4535data.bed",
		"variant_calling_bedfile": "Pan4535data.bed",
		"sambamba_bedfile": "Pan4535dataSambamba.bed",
	},
	"Pan4831": {  # VCP3 STG R66
		"mokapipe": True,
		"multiqc_coverage_level": 30,
		"RPKM_bedfile_pan_number": "Pan3974",
		"RPKM_also_analyse": vcp3_panel_list,
		"congenica_credentials": "STG",
		"congenica_IR_template":"non-priority",
		"congenica_project": "4201",
		"hsmetrics_bedfile": "Pan4535data.bed",
		"variant_calling_bedfile": "Pan4535data.bed",
		"sambamba_bedfile": "Pan4535dataSambamba.bed",
	},
	"Pan4832": {  # VCP3 STG R78
		"mokapipe": True,
		"multiqc_coverage_level": 30,
		"RPKM_bedfile_pan_number": "Pan3974",
		"RPKM_also_analyse": vcp3_panel_list,
		"congenica_credentials": "STG",
		"congenica_IR_template":"non-priority",
		"congenica_project": "4201",
		"hsmetrics_bedfile": "Pan4535data.bed",
		"variant_calling_bedfile": "Pan4535data.bed",
		"sambamba_bedfile": "Pan4535dataSambamba.bed",
	},
	"Pan4833": {  # VCP3 STG R79
		"mokapipe": True,
		"multiqc_coverage_level": 30,
		"RPKM_bedfile_pan_number": "Pan3974",
		"RPKM_also_analyse": vcp3_panel_list,
		"congenica_credentials": "STG",
		"congenica_IR_template":"non-priority",
		"congenica_project": "4201",
		"hsmetrics_bedfile": "Pan4535data.bed",
		"variant_calling_bedfile": "Pan4535data.bed",
		"sambamba_bedfile": "Pan4535dataSambamba.bed",
	},
	"Pan4834": {  # VCP3 STG R81
		"mokapipe": True,
		"multiqc_coverage_level": 30,
		"RPKM_bedfile_pan_number": "Pan3974",
		"RPKM_also_analyse": vcp3_panel_list,
		"congenica_credentials": "STG",
		"congenica_IR_template":"non-priority",
		"congenica_project": "4201",
		"hsmetrics_bedfile": "Pan4535data.bed",
		"variant_calling_bedfile": "Pan4535data.bed",
		"sambamba_bedfile": "Pan4535dataSambamba.bed",
	},
	"Pan4835": {  # VCP3 STG R82
		"mokapipe": True,
		"multiqc_coverage_level": 30,
		"RPKM_bedfile_pan_number": "Pan3974",
		"RPKM_also_analyse": vcp3_panel_list,
		"congenica_credentials": "STG",
		"congenica_IR_template":"non-priority",
		"congenica_project": "4201",
		"hsmetrics_bedfile": "Pan4535data.bed",
		"variant_calling_bedfile": "Pan4535data.bed",
		"sambamba_bedfile": "Pan4535dataSambamba.bed",
	},
	"Pan4836": {  # VCP3 STG R229
		"mokapipe": True,
		"multiqc_coverage_level": 30,
		"RPKM_bedfile_pan_number": "Pan3974",
		"RPKM_also_analyse": vcp3_panel_list,
		"congenica_credentials": "STG",
		"congenica_IR_template":"non-priority",
		"congenica_project": "4201",
		"hsmetrics_bedfile": "Pan4535data.bed",
		"variant_calling_bedfile": "Pan4535data.bed",
		"sambamba_bedfile": "Pan4535dataSambamba.bed",
	},
	"Pan4818": {  # VCP2 STG R209
		"mokapipe": True,
		"multiqc_coverage_level": 30,
		"RPKM_bedfile_pan_number": "Pan3614",
		"RPKM_also_analyse": vcp2_panel_list,
		"congenica_credentials": "STG",
		"congenica_IR_template":"non-priority",
		"congenica_project": "4202",
		"hsmetrics_bedfile": "Pan4949data.bed",
		"variant_calling_bedfile": "Pan4948data.bed",
		"sambamba_bedfile": "Pan4949dataSambamba.bed",
	},
	"Pan4819": {  # VCP2 STG R210
		"mokapipe": True,
		"multiqc_coverage_level": 30,
		"RPKM_bedfile_pan_number": "Pan3614",
		"RPKM_also_analyse": vcp2_panel_list,
		"congenica_credentials": "STG",
		"congenica_IR_template":"non-priority",
		"congenica_project": "4202",
		"hsmetrics_bedfile": "Pan4949data.bed",
		"variant_calling_bedfile": "Pan4948data.bed",
		"sambamba_bedfile": "Pan4949dataSambamba.bed",
	},
	"Pan4820": {  # VCP2 STG R211
		"mokapipe": True,
		"multiqc_coverage_level": 30,
		"RPKM_bedfile_pan_number": "Pan3614",
		"RPKM_also_analyse": vcp2_panel_list,
		"congenica_credentials": "STG",
		"congenica_IR_template":"non-priority",
		"congenica_project": "4202",
		"hsmetrics_bedfile": "Pan4949data.bed",
		"variant_calling_bedfile": "Pan4948data.bed",
		"sambamba_bedfile": "Pan4949dataSambamba.bed",
	},
	"Pan4816": {  # VCP2 STG R208
		"mokapipe": True,
		"multiqc_coverage_level": 30,
		"RPKM_bedfile_pan_number": "Pan3614",
		"RPKM_also_analyse": vcp2_panel_list,
		"congenica_credentials": "STG",
		"congenica_IR_template":"non-priority",
		"congenica_project": "1099",
		"hsmetrics_bedfile": "Pan4949data.bed",
		"variant_calling_bedfile": "Pan4948data.bed",
		"sambamba_bedfile": "Pan4949dataSambamba.bed",
	},
	"Pan4817": {  # VCP2 STG R207
		"mokapipe": True,
		"multiqc_coverage_level": 30,
		"RPKM_bedfile_pan_number": "Pan3614",
		"RPKM_also_analyse": vcp2_panel_list,
		"congenica_credentials": "STG",
		"congenica_IR_template":"non-priority",
		"congenica_project": "1099",
		"hsmetrics_bedfile": "Pan4949data.bed",
		"variant_calling_bedfile": "Pan4948data.bed",
		"sambamba_bedfile": "Pan4949dataSambamba.bed",
	},
	"Pan5007": {  # LRPCR Via R207 PMS2
		"mokapipe": True,
		"multiqc_coverage_level": 30,
		"capture_type": "Amplicon",
		"congenica_IR_template":"priority",
		"congenica_project": "9986",
		"hsmetrics_bedfile": "Pan4967_reference.bed", # LRPCR amplicon BED file
		"variant_calling_bedfile": "Pan4767data.bed",
		"sambamba_bedfile": "Pan5018dataSambamba.bed",
		"masked_reference":
			"project-ByfFPz00jy1fk6PjpZ95F27J:file-GF84GF00QfBfzV35Gf8Qg53q" # hs37d5_Pan4967.bwa-index.tar.gz
	},
	"Pan5008": {  # LRPCR STG R207 PMS2
		"mokapipe": True,
		"multiqc_coverage_level": 30,
		"capture_type": "Amplicon",
		"congenica_IR_template":"non-priority",
		"congenica_project": "10010",
		"congenica_credentials": "STG",
		"hsmetrics_bedfile": "Pan4967_reference.bed", # LRPCR amplicon BED file
		"variant_calling_bedfile": "Pan4767data.bed",
		"sambamba_bedfile": "Pan5018dataSambamba.bed",
		"masked_reference":
			"project-ByfFPz00jy1fk6PjpZ95F27J:file-GF84GF00QfBfzV35Gf8Qg53q" # hs37d5_Pan4967.bwa-index.tar.gz
	},
	"Pan5011": {  # LRPCR Via R210 PMS2
		"mokapipe": True,
		"multiqc_coverage_level": 30,
		"capture_type": "Amplicon",
		"congenica_IR_template":"priority",
		"congenica_project": "9981",
		"hsmetrics_bedfile": "Pan4967_reference.bed", # LRPCR amplicon BED file
		"variant_calling_bedfile": "Pan4767data.bed",
		"sambamba_bedfile": "Pan5018dataSambamba.bed",
		"masked_reference": "project-ByfFPz00jy1fk6PjpZ95F27J:file-GF84GF00QfBfzV35Gf8Qg53q" # hs37d5_Pan4967.bwa-index.tar.gz
	},
	"Pan5012": {  # LRPCR STG R210 PMS2
		"mokapipe": True,
		"multiqc_coverage_level": 30,
		"capture_type": "Amplicon",
		"congenica_IR_template":"non-priority",
		"congenica_project": "10042",
		"congenica_credentials": "STG",
		"hsmetrics_bedfile": "Pan4967_reference.bed", # LRPCR amplicon BED file
		"variant_calling_bedfile": "Pan4767data.bed",
		"sambamba_bedfile": "Pan5018dataSambamba.bed",
		"masked_reference":
			"project-ByfFPz00jy1fk6PjpZ95F27J:file-GF84GF00QfBfzV35Gf8Qg53q" # hs37d5_Pan4967.bwa-index.tar.gz
	},
	"Pan5013": {  # LRPCR Via R211 PMS2
		"mokapipe": True,
		"multiqc_coverage_level": 30,
		"capture_type": "Amplicon",
		"congenica_IR_template":"priority",
		"congenica_project": "9982",
		"hsmetrics_bedfile": "Pan4967_reference.bed", # LRPCR amplicon BED file
		"variant_calling_bedfile": "Pan4767data.bed",
		"sambamba_bedfile": "Pan5018dataSambamba.bed",
		"masked_reference":
			"project-ByfFPz00jy1fk6PjpZ95F27J:file-GF84GF00QfBfzV35Gf8Qg53q" # hs37d5_Pan4967.bwa-index.tar.gz
	},
	"Pan5014": {  # LRPCR STG R211 PMS2
		"mokapipe": True,
		"multiqc_coverage_level": 30,
		"capture_type": "Amplicon",
		"congenica_IR_template":"non-priority",
		"congenica_project": "10042",
		"congenica_credentials": "STG",
		"hsmetrics_bedfile": "Pan4967_reference.bed", # LRPCR amplicon BED file
		"variant_calling_bedfile": "Pan4767data.bed",
		"sambamba_bedfile": "Pan5018dataSambamba.bed",
		"masked_reference":
			"project-ByfFPz00jy1fk6PjpZ95F27J:file-GF84GF00QfBfzV35Gf8Qg53q" # hs37d5_Pan4967.bwa-index.tar.gz
	},
	"Pan5009": {  # LRPCR Via R208 CHEK2
		"mokapipe": True,
		"multiqc_coverage_level": 30,
		"capture_type": "Amplicon",
		"congenica_IR_template":"priority",
		"congenica_project": "9984",
		"hsmetrics_bedfile": "Pan4967_reference.bed", # LRPCR amplicon BED file
		"variant_calling_bedfile": "Pan4767data.bed",
		"sambamba_bedfile": "Pan5018dataSambamba.bed",
		"masked_reference":
			"project-ByfFPz00jy1fk6PjpZ95F27J:file-GF84GF00QfBfzV35Gf8Qg53q" # hs37d5_Pan4967.bwa-index.tar.gz
	},
	"Pan5010": {  # LRPCR STG R208 CHEK2
		"mokapipe": True,
		"multiqc_coverage_level": 30,
		"capture_type": "Amplicon",
		"congenica_IR_template":"non-priority",
		"congenica_project": "10009",
		"congenica_credentials": "STG",
		"hsmetrics_bedfile": "Pan4967_reference.bed", # LRPCR amplicon BED file
		"variant_calling_bedfile": "Pan4766data.bed",
		"sambamba_bedfile": "Pan5018dataSambamba.bed",
		"masked_reference":
			"project-ByfFPz00jy1fk6PjpZ95F27J:file-GF84GF00QfBfzV35Gf8Qg53q" # hs37d5_Pan4967.bwa-index.tar.gz
	},
	"Pan5015": {  # LRPCR Via R71 SMN1
		"mokapipe": True,
		"multiqc_coverage_level": 30,
		"capture_type": "Amplicon",
		"congenica_IR_template":"non-priority", # TODO
		"congenica_project": "9547", # TODO
		"hsmetrics_bedfile": "Pan4967_reference.bed", # LRPCR amplicon BED file
		"variant_calling_bedfile": "Pan4971data.bed",
		"sambamba_bedfile": "Pan5018dataSambamba.bed",
		"masked_reference":
			"project-ByfFPz00jy1fk6PjpZ95F27J:file-GF84GF00QfBfzV35Gf8Qg53q" # hs37d5_Pan4967.bwa-index.tar.gz
	},
	"Pan5016": {  # LRPCR Via R239 IKBKG
		"mokapipe": True,
		"multiqc_coverage_level": 30,
		"capture_type": "Amplicon",
		"congenica_IR_template":"priority",
		"congenica_project": "9985",
		"hsmetrics_bedfile": "Pan4967_reference.bed", # LRPCR amplicon BED file
		"variant_calling_bedfile": "Pan4768data.bed",
		"sambamba_bedfile": "Pan5018dataSambamba.bed",
		"masked_reference":
			"project-ByfFPz00jy1fk6PjpZ95F27J:file-GF84GF00QfBfzV35Gf8Qg53q" # hs37d5_Pan4967.bwa-index.tar.gz
	},
}


# ================ TURNAROUND TIME =======================================================================

allowed_time_for_tasks = 4 # If a task takes more than this amount of time it is out of TAT


# ================= EMAIL SERVER SETTINGS ==============================================================

username_file_path = "{document_root}/.amazon_email_username".format(document_root=document_root)
pw_file = "{document_root}/.amazon_email_pw".format(document_root=document_root)

host = "email-smtp.eu-west-1.amazonaws.com"
port = 587
me = "moka.alerts@gstt.nhs.uk"
you = mokaguys_email
oncology_you = oncology_ops_email
smtp_do_tls = True

if testing:
	test_email_header = "AUTOMATED SCRIPTS ARE BEING RUN IN TEST MODE. PLEASE IGNORE THIS EMAIL\n\n"
else:
	test_email_header = ""

with open(username_file_path, "r") as username_file:
	user = username_file.readline().rstrip()

with open(pw_file, "r") as email_password_file:
	pw = email_password_file.readline().rstrip()

