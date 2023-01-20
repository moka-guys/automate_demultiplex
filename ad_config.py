# coding=utf-8
"""
Automate demultiplex configuration.

The variables defined in this module are required by scripts in the automate_demultiplex repository
(https://github.com/moka-guys/automate_demultiplex)

The config file is split into sections. Those settings that are used across scripts and those that
are specific to a script.
"""

import os

# ================ GENERAL =========================================================================
# Settings used across multiple scripts

testing = True  # Set testing mode

# Root of folder containing apps, automate_demultiplexing_logfiles and development_area scripts
# (2 levels up from this file)
document_root = "/".join(os.path.dirname(os.path.realpath(__file__)).split("/")[:-2])

ad_logfiles = os.path.join(document_root, "automate_demultiplexing_logfiles")

novaseq_id = "A01229"

# ----- Runfolders ---------------------------------------------------------------------------------

runfolder_pattern = "^[0-9]{6}.*$"  # Runfolders start with 6 digits
ignore_dirs = ["samplesheets"]  # Directories to be ignored when looping through runfolders

# Path to run folders - use testing flag to determine folders
if not testing:
    runfolders = "/media/data3/share"

else:
    runfolders = "/media/data3/share/testing"


# ----- Logfiles -----------------------------------------------------------------------------------

bcl2fastqlog_filename = "bcl2fastq2_output.log"
demultiplexing_logfile_tso500_msg = "TSO500 run. Does not need demultiplexing locally"
demultiplex_success_regex = r".*Processing completed with 0 errors and 0 warnings.$"

# Test-dependent settings
if testing:
    logging_formatter = "%(asctime)s - TEST MODE - %(name)s - %(flag)s - %(levelname)s - %(message)s"
    log_flags = {'info': 'demultiplextest_info', 'fail': 'demultiplextest_fail',
                 'success': 'demultiplextest_success', 'ss_warning': 'testsamplesheet_warning'}
    # Folder containing demultiplex logs
    demultiplex_logpath = os.path.join(runfolders, "Demultiplexing_log_files/")
else:
    logging_formatter = "%(asctime)s - %(name)s - %(flag)s - %(levelname)s - %(message)s"
    log_flags = {'info': 'demultiplex_info', 'fail': 'demultiplex_fail',
                 'success': 'demultiplex_success', 'ss_warning': 'samplesheet_warning'}
    # Folder containing demultiplex logs
    demultiplex_logpath = os.path.join(ad_logfiles, "Demultiplexing_log_files/")

# Subdirectories
samplesheet_dir = os.path.join(runfolders, "samplesheets")  # Samplesheet folder
fastq_dir = "/Data/Intensities/BaseCalls"  # Path to fastq files

# ---- Filepaths -----------------------------------------------------------------------------------

# Path to log file which records the output of the upload agent
upload_script_logpath = os.path.join(ad_logfiles, "upload_agent_script_logfiles/")

# Name of log file which records the output of the upload agent
upload_started_filename = "DNANexus_upload_started.txt"

# Log folder containing project creation logs
dnanexus_projectcreation_logfolder = os.path.join(ad_logfiles, "nexus_project_creation_scripts",
                                                  "create_nexus_project_")

# Backup runfolder folder
backup_runfolder_logfile = os.path.join(ad_logfiles, "backup_runfolder_logfiles")

# ----- DNAnexus -----------------------------------------------------------------------------------

# DNAnexus authentication token
nexus_apikey_file = os.path.join(document_root, ".dnanexus_auth_token")
with open(nexus_apikey_file, "r", encoding="utf-8") as nexus_api:
    nexus_apikey = nexus_api.readline().rstrip()

sdk_source_cmd = "/etc/profile.d/dnanexus.environment.sh"

# DNAnexus settings used across multiple scripts
mokapipe_filter_vcf_with_bedfile_stage = "stage-G5Kpgv80zB02Q64zFf94G05F"
mokapipe_gatk_human_exome_stage = "stage-F28y4qQ0jy1fkqfy5v2b8byx"
sentieon_stage_id = "stage-Ff0P73j0GYKX41VkF3j62F9j"

# ----- Email settings -----------------------------------------------------------------------------

username_filepath = os.path.join(document_root, ".amazon_email_username")
pw_file = os.path.join(document_root, ".amazon_email_pw")

with open(username_filepath, "r", encoding="utf-8") as username_file:  # Get email username
    user = username_file.readline().rstrip()

with open(pw_file, "r", encoding="utf-8") as email_password_file:  # Get email password
    pw = email_password_file.readline().rstrip()


host = "email-smtp.eu-west-1.amazonaws.com"
port = 587
smtp_do_tls = True


mokaguys_email = "gst-tr.mokaguys@nhs.net"
mokalerts_email = "moka.alerts@gstt.nhs.uk"


# Test settings
if testing:
    test_email_header = "AUTOMATED SCRIPTS ARE BEING RUN IN TEST MODE. PLEASE IGNORE THIS EMAIL\n\n"
    mokaguys_recipient = "mokaguys@gmail.com"
    # Oncology email address for email alerts
    oncology_ops_email = mokaguys_email
    wes_samplename_email_list = [mokaguys_email]

# Production settings
else:
    test_email_header = ""
    mokaguys_recipient = mokaguys_email
    # Oncology email address for email alerts
    oncology_ops_email = "m.neat@nhs.net"
    wes_samplename_email_list = ["gst-tr.ViapathGeneticsAdmin@nhs.net", "lu.liu@viapath.co.uk",
                                 "Suzanne.lillis@viapath.co.uk", "eblab@gstt.nhs.uk",
                                 mokaguys_email]


email_logmsgs = {'email_sending': "Sending an email. Recipient: %s. Subject: %s. Body: %s",
                 'email_pass': "Email sent without error",
                 'email_fail': "Error when sending email. Email not sent. Exception: %s"}

# ================ DEMULTIPLEXING (demultiplex.py) =================================================
# Settings unique to the demultiplex script

# Sequencer / run identifiers
sequencer_ids = ["NB551068", "NB552085", "M02353", "M02631", "A01229"]
runtype_list = ["NGS", "ADX", "ONC", "SNP", "TSO", "LRPCR"]

# Integrity check
md5checksum_filename = "md5checksum.txt"  # File holding checksum results
checksum_complete_msg = "Checksum result reported"  # Checksum complete statement
checksum_match_msg = "Checksums match"  # Statement to write when checksums match
# Sequencers requiring md5 checksums from integrity check to be assessed
sequencers_with_integrity_check = ["NB551068", "NB552085", novaseq_id]
icfail_emailsubj = "DEMULTIPLEX ALERT: INTEGRITY CHECK FAILED"
icfail_emailmsg = "Run:\t{}\nPlease follow the protocol for when integrity checks fail"

# Sequencing complete file
rtacomplete_filename = "RTAComplete.txt"

# Bcl2fastq2
bcl2fastq_path = "/usr/local/bcl2fastq2-v2.20.0.422/bin/bcl2fastq"  # Path to bcl2fastq
bcl2fastq_stats_filename = "Stats.json"
bcl2fastq_stats_path = os.path.join(fastq_dir, "Stats")

demux_logmsgs = {
    'demux_script_start': "Automate demultiplex release %s: Demultiplex.py started on workstation",
    'demux_script_end':
        "Automate demultiplex release %s: Demultiplex.py complete. %s runfolder(s) processed",
    'rename_demuxlog_success':
        'Demultiplex logfile successfully renamed with runfolder names. New name: %s',
    'rename_demuxlog_fail': 'Demultiplex logfile rename failed for file %s',
    'demux_runfolder_start': "Automate_demultiplex release: %s -------------- Assessing %s",
    'ic_fail': "Integrity check fail. Checksums do not match for %s see %s",
    'bcl2fastq_start': "Demultiplexing started for run %s using bcl2fastq command: %s",
    'bcl2fastq_complete': "bcl2fastq subprocess complete for run %s",
    'bcl2fastq_failed': "bcl2fastq subprocess failed for run %s",
    'demux_already_complete':
        "Demultiplexing already completed - bcl2fastq log found @ %s --- STOP ---",
    'demux_not_complete':
        "Demultiplexing not yet completed - no demultiplex log found @ %s --- CONTINUE ---",
    'sschecks_not_passed': "Samplesheet did not pass checks %s: %s",
    'sschecks_passed': "Samplesheet passed all checks %s",
    'run_finished': "Run finished - RTAComplete.txt found @ %s",
    'run_incomplete': "Sequencing not yet complete (RTAComplete.txt file absent) --- STOP ---",
    'bcl2fastq_test_fail': "BCL2FastQ installation test failed",
    'bcl2fastq_test_pass': "BCL2FastQ installation test passed",
    'ssfail_haltdemux': "Demultiplexing halted due to samplesheet errors %s: %s",
    'ic_required': "This run was sequenced on a sequencer that requires integrity checking",
    'ic_notrequired': "Integrity check not required",
    'csumfile_present':
        "Checksums file present - checksums have been generated by integrity check scripts",
    'csumfile_absent': "Demultiplexing halted: Integrity check not yet performed on sequencer (checksum file absent)",
    'checksums_checked': "Checksums already checked for this run",
    'ic_start': "Data integrity checks starting...",
    'ic_pass': "Integrity check for runfolder %s passed",
    'create_bcl2fastqlog_pass': "Created bcl2fastq logfile for run %s",
    'create_bcl2fastqlog_fail': "Failed to create bcl2fastq logfile for run %s. Exception: %s",
    'create_tsobcl2fastqlog_pass': "bcl2fastq2_output.log file created for TSO run: %s",
    'create_tsobcl2fastqlog_fail':
        "Failed to create bcl2fastq2_output.log file for TSO run: %s. Exception: %s",
    'demux_complete': "Demultiplexing complete without error for run %s",
    'demux_error': "ERROR - DEMULTIPLEXING UNSUCCESSFUL (BCL2FastQ2 ERROR) "
                   "- Demultiplexing failed for run %s. Please see logfile %s",
    'bcl2fastqlog_empty': "ERROR - BCL2FASTQ2 logfile is empty for run %s. Please see logfile %s",
    'bcl2fastqlog_absent':
        "ERROR - BCL2FASTQ2 logfile does not exist for run %s. Please see logfile ",
}


# ===== DECISION SUPPORT SCRIPT (decision_support_tool_inputs.py) ==================================
# Settings unique to the decision support script

decision_support_tool_input_script = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                                  "decision_support_tool_inputs.py")
mokawes_sentieon_bam_output_name = "mappings_bam"
mokawes_sentieon_bai_output_name = "mappings_bam_bai"
mokawes_sentieon_vcf_output_name = "variants_vcf"
congenica_vcf_inputname = " -ivcf="
congenica_bam_inputname = " -ibam="
congenica_samplename = " -ianalysis_name="
mokapipe_vcf_output_name = "filtered_vcf"
mokapipe_bam_output_name = "bam"


# ================ UPLOAD AND SETOFF WORKFLOWS =====================================================
# Settings unique to the upload and setoff workflows script

reference_sample_ids = ["NA12878", "136819"]  # NA12878 identifiers to exclude from congenica upload

# ---- Filepaths -----------------------------------------------------------------------------------
upload_agent_path = os.path.join("apps/dnanexus-upload-agent-1.5.17-linux/ua")
backup_runfolder_script = os.path.join("apps/workstation_housekeeping/backup_runfolder.py")

# ---- Commands and strings ------------------------------------------------------------------------
upload_agent_test_cmd = " --version"
ua_error = "Error Message: 'Could not resolve: api.dnanexus.com"
dx_sdk_test = f"source {sdk_source_cmd};dx --version"  # Command to test dx toolkit# GENERAL
backup_runfolder_success = "backup_runfolder INFO - END"
backup_runfolder_error = "backup_runfolder.UAcaller ERROR"
dx_sdk_test_expected_stdout = "dx v0.2"  # Expected result from testing
upload_agent_expected_stdout = "Upload Agent Version:"  # Upload agent test response

# ---- Cluster density strings ---------------------------------------------------------------------
cluster_density_success_statement = "picard.illumina.CollectIlluminaLaneMetrics done"
cluster_density_error_statement = "PicardException"
cluster_density_file_suffix = ".illumina_lane_metrics"
phasing_metrics_file_suffix = ".illumina_phasing_metrics"

# ---- DNAnexus ------------------------------------------------------------------------------------

# Path to DNAnexus run command log file
dnanexus_workflow_logfolder = os.path.join(ad_logfiles, "/dx_run_commands/")

# General
bedfile_folder = "Data/BED/"
dnanexus_project_prefix = "002_"  # Project to upload run folder into
project_success = 'Created new project called "%s"'  # Success statement when creating project
prod_organisation = "org-viapath_prod"  # DNAnexus organisation to create the project within
tools_project = "project-ByfFPz00jy1fk6PjpZ95F27J:/"  # 001_ToolsReferenceData
view_users = ["org-viapath_prod", "InterpretationRequest"]  # DNAnexus users with view access
admin_users = ["mokaguys"]  # DNAnexus users with admin access

# Paths / IDs for workflows in 001_Tools
mokapipe_path = "Workflows/GATK3.5_v2.16"
mokawes_path = "Workflows/MokaWES_v1.8"
mokaamp_path = "Workflows/MokaAMP_v2.2"
mokacan_path = "Workflows/MokaCAN_v1.0"
mokasnp_path = "Workflows/MokaSNP_v1.2.0"
tso500_app = "applet-GBKvYFQ0jy1Vx4zJ126gX4xp"
tso500_app_name = "TSO500_v1.4.0"  # Input for tso500_output_parser_app

# Paths / IDs for apps in 001_Tools
fastqc_app = "Apps/fastqc_v1.3"
peddy_path = "Apps/peddy_v1.5"
rpkm_path = "Apps/RPKM_using_conifer_v1.6"
multiqc_path = "Apps/multiqc_v1.15.0"
upload_multiqc_path = "Apps/upload_multiqc_v1.4.0"
congenica_app_path = "Apps/congenica_upload_v1.3.2"
congenica_SFTP_upload_app = "applet-GFfJpj80jy1x1Bz1P1Bk3vQf"
tso500_output_parser_app = "applet-GBKvX5j0jy1kK8jj9F7jjVY7"
# Inputs for tso500_output_parser_app
upload_multiqc_app_id = "project-ByfFPz00jy1fk6PjpZ95F27J:applet-G2XY8QQ0p7kzvPZBJGFygP6f"
multiqc_app_id = "project-ByfFPz00jy1fk6PjpZ95F27J:applet-G7QB6zj0jy1z1ZV1P5VZBj9p"
sompy_app_id = "project-ByfFPz00jy1fk6PjpZ95F27J:applet-G9yPb780jy1p660k6yBvQg07"
coverage_app_id = "project-ByfFPz00jy1fk6PjpZ95F27J:applet-G6vyyf00jy1kPkX9PJ1YkxB1"
fastqc_app_id = "project-ByfFPz00jy1fk6PjpZ95F27J:applet-FBPFfkj0jy1Q114YGQ0yQX8Y"

# Paths / IDs for docker images
tso500_docker_image = "project-ByfFPz00jy1fk6PjpZ95F27J:file-Fz9Zyx00b5j8xKVkKv4fZ6JB"

# Inputs shared across workflows
peddy_project_input = " -iproject_for_peddy="
multiqc_project_input = " -iproject_for_multiqc="
multiqc_coverage_level_input = " -icoverage_level="

# MokaPIPE workflow inputs
mokapipe_fastqc1 = " -istage-Bz3YpP80jy1Y1pZKbZ35Bp0x.reads="  # FastQC Read 1
mokapipe_fastqc2 = " -istage-Bz3YpP80jy1x7G5QfG3442gX.reads="  # FastQC Read 2
mokapipe_bwa_rg_sample = " -istage-Byz9BJ80jy1k2VB9xVXBp0Fg.read_group_sample="
mokapipe_bwa_ref_genome = " -istage-Byz9BJ80jy1k2VB9xVXBp0Fg.genomeindex_targz=%s"
# HSMetrics Bedfile
mokapipe_mokapicard_vendorbed_input = " -istage-F9GK4QQ0jy1qj14PPZxxq3VG.vendor_exome_bedfile="
mokapipe_mokapicard_capturetype_stage = " -istage-F9GK4QQ0jy1qj14PPZxxq3VG.Capture_panel=%s"
mokapipe_haplotype_padding_input = f" -i{mokapipe_gatk_human_exome_stage}.padding="
mokapipe_haplotype_vcf_output_format = f" -i{mokapipe_gatk_human_exome_stage}.output_format=both"
mokapipe_filter_vcf_with_bedfile_bed_input = f" -i{mokapipe_filter_vcf_with_bedfile_stage}.bedfile="

mokapipe_happy_skip = " -istage-G8V205j0fB6QGKXQ2gZ5pB1z.skip=%s"
mokapipe_happy_prefix = " -istage-G8V205j0fB6QGKXQ2gZ5pB1z.prefix=%s"
mokapipe_sambamba_bed_input = " -istage-F35zBKQ0jy1XpfzYPZY4bgX6.sambamba_bed="
mokapipe_sambamba_min_base_qual = " -istage-F35zBKQ0jy1XpfzYPZY4bgX6.min_base_qual=10"
mokapipe_sambamba_min_mapping_qual = " -istage-F35zBKQ0jy1XpfzYPZY4bgX6.min_mapping_qual=20"
mokapipe_sambamba_coverage_level = " -istage-F35zBKQ0jy1XpfzYPZY4bgX6.coverage_level=30"
mokapipe_sambamba_filter_cmds = " -istage-F35zBKQ0jy1XpfzYPZY4bgX6.additional_filter_commands=" \
                                "'not (unmapped or secondary_alignment)'"
mokapipe_sambamba_exclude_duplicates = " -istage-F35zBKQ0jy1XpfzYPZY4bgX6.exclude_duplicate_reads" \
                                       "=true"
mokapipe_sambamba_exclude_failed_qual = " -istage-F35zBKQ0jy1XpfzYPZY4bgX6." \
                                        "exclude_failed_quality_control=true"
mokapipe_sambamba_count_overlapping_mates = " -istage-F35zBKQ0jy1XpfzYPZY4bgX6." \
                                            "merge_overlapping_mate_reads=true"
mokapipe_fhprs_skip = " -istage-G9BfkZQ0fB6jZY7v1PfJ81F6.skip=false"
mokapipe_fhprs_bedfile_input = " -istage-G9BfkZQ0fB6jZY7v1PfJ81F6.BEDfile="
mokapipe_fh_humanexome_instance_type = "mem3_ssd1_v2_x8"  # Required when creating gVCFs
mokapipe_gatk_human_exome_appletid = "applet-FYZ097j0jy1ZZPx30GykP63J"
# Set 6 hour timeout policy for gatk app and jobtimeoutexceeded reason to auto restart list
# THIS SHOULD BE MOVED TO THE APP DXAPP.JSON FILE
mokapipe_fh_gatk_timeout_args = " --extra-args '{\"timeoutPolicyByExecutable\": {\"%s\": " \
                                "{\"*\":{\"hours\": 6}}}, \"executionPolicy\": {\"restartOn\": " \
                                "{\"JobTimeoutExceeded\":1, \"JMInternalError\":" \
                                " 1, \"UnresponsiveWorker\": 2, \"ExecutionError\":1}}}'" % \
                                mokapipe_gatk_human_exome_appletid
mokapipe_rpkm_bedfile_input = " -ibedfile="
mokapipe_rpkm_project_input = " -iproject_name="
mokapipe_rpkm_bamfiles_to_download_input = " -ibamfile_pannumbers="

# MokaWES workflow inputs
wes_fastqc1 = " -istage-Ff0P5Jj0GYKY717pKX3vX8Z3.reads="  # FastQC Read 1
wes_fastqc2 = " -istage-Ff0P5V00GYKyJfpX5bqX69Yg.reads="  # FastQC Read
wes_picard_bedfile = " -istage-Ff0P5pQ0GYKVBB0g1FG27BV8.vendor_exome_bedfile="  # HSmetrics bedfile
wes_sambamba_bedfile = " -istage-Ff0P82Q0GYKQ4j8b4gXzjqxX.sambamba_bed="
# Senteion app sample name - prevents sample being incorrectly parsed from fastq filename
wes_sentieon_samplename = f" -i{sentieon_stage_id}.sample="
wes_sentieon_targets_bed = f" -i{sentieon_stage_id}.targets_bed="

# MokaSNP workflow inputs
snp_fastqc1 = " -istage-FgPp4V00YkVJVjKF4kYkBF8v.reads="  # FastQC Read 1
snp_fastqc2 = " -istage-FgPp4V00YkVJVjKF4kYkBF90.reads="  # FastQC Read 2
snp_sentieon_stage_id = "stage-FgPp4XQ0YkV48jZG4Py6F55k"
snp_sentieon_targets_bed = f" -i{snp_sentieon_stage_id}.targets_bed="
# Senteion app sample name - prevents sample being incorrectly parsed from fastq filename
snp_sentieon_samplename = f" -i{snp_sentieon_stage_id}.sample="

# MokaAMP workflow inputs
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
mokaamp_bwa_ref_stage = " -istage-FPzGj780jy1g3p1F4F8z4J7V.genomeindex_targz=" \
                        "project-ByfFPz00jy1fk6PjpZ95F27J:file-B6ZY4942J35xX095VZyQBk0v"
mokaamp_mokapicard_ref_stage = " -istage-FPzGjV80jy1x97jg607Fg22b.fasta_index=" \
                               "project-ByfFPz00jy1fk6PjpZ95F27J:file-ByYgX700b80gf4ZY1GxvF3Jv"
mokaamp_vardict_ref_stage = " -istage-G0vKZk80GfYkQx86PJGGjz9Y.ref_genome=" \
                            "project-ByfFPz00jy1fk6PjpZ95F27J:file-ByYgX700b80gf4ZY1GxvF3Jv"
mokaamp_varscan_ref_stage = " -istage-FPzGjp80jy1V3Jvb5z6xfpfZ.ref_genome=" \
                            "project-ByfFPz00jy1fk6PjpZ95F27J:file-ByYgX700b80gf4ZY1GxvF3Jv"

# MokaCAN workflow inputs
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
mokacan_senteion_bwa_ref_stage = " -istage-FgYgB2Q087fjzvxy9f4q1K8X.genomebwaindex_targz=" \
                                 "project-ByfFPz00jy1fk6PjpZ95F27J:file-B6ZY4942J35xX095VZyQBk0v"
mokacan_senteion_ref_stage = " -istage-FgYgB2Q087fjzvxy9f4q1K8X.genome_fastagz=" \
                             "project-ByfFPz00jy1fk6PjpZ95F27J:file-B6ZY7VG2J35Vfvpkj8y0KZ01"
mokacan_picard_ref_stage = " -istage-FPzGjV80jy1x97jg607Fg22b.fasta_index=" \
                           "project-ByfFPz00jy1fk6PjpZ95F27J:file-ByYgX700b80gf4ZY1GxvF3Jv"
mokacan_vardict_ref_stage = " -istage-FPzGjgj0jy1Q2JJF2zYx5J5k.ref_genome=" \
                            "project-ByfFPz00jy1fk6PjpZ95F27J:file-ByYgX700b80gf4ZY1GxvF3Jv"
mokacan_varscan_ref_stage = " -istage-FPzGjp80jy1V3Jvb5z6xfpfZ.ref_genome=" \
                            "project-ByfFPz00jy1fk6PjpZ95F27J:file-ByYgX700b80gf4ZY1GxvF3Jv"

# TSO500 workflow inputs
tso500_docker_image_stage = " -iTSO500_ruo="
tso500_runfolder_tar_stage = " -irun_folder="
tso500_samplesheet_stage = " -isamplesheet="
tso500_analysis_options_stage = " -ianalysis_options="
tso500_analysis_instance_high_throughput = "mem1_ssd1_v2_x72"
tso500_analysis_instance_low_throughput = "mem1_ssd1_v2_x36"

tso500_output_parser_project_name_stage = " -iproject_name="
tso500_output_parser_project_id_stage = " -iproject_id="
tso500_output_parser_job_id_stage = " -itso500_jobid="
tso500_output_parser_coverage_bedfile_id_stage = " -icoverage_bedfile_id="
tso500_output_parser_coverage_app_id_stage = " -icoverage_app_id="
tso500_output_parser_fastqc_app_id_stage = " -ifastqc_app_id="
tso500_output_parser_sompy_app_id_stage = " -isompy_app_id="
tso500_output_parser_multiqc_app_id_stage = " -imultiqc_app_id="
tso500_output_parser_upload_multiqc_app_id_stage = " -iupload_multiqc_app_id="
tso500_output_parser_coverage_commands_stage = " -icoverage_commands="
tso500_output_parser_coverage_level_stage = " -icoverage_level="
tso500_output_parser_multiqc_coverage_level_stage = " -imultiqc_coverage_level="
tso500_output_parser_coverage_commands = "'-imerge_overlapping_mate_reads=true " \
                                         "-iexclude_failed_quality_control=true " \
                                         "-iexclude_duplicate_reads=true -imin_base_qual=%s " \
                                         "-imin_mapping_qual=%s'"

# Command strings
source_cmd = f"#!/bin/bash\n. {sdk_source_cmd}\ndepends_list=''"
create_project_cmd = 'project_id="$(dx new project --bill-to %s "%s" --brief --auth-token %s)"\n'
mokapipe_cmd = f"jobid=$(dx run {tools_project}{mokapipe_path} --priority high -y --name "
mokawes_cmd = f"jobid=$(dx run {tools_project}{mokawes_path} --priority high -y --name "
mokasnp_cmd = f"jobid=$(dx run {tools_project}{mokasnp_path} -y --priority high --name "
archerdx_cmd = f"jobid=$(dx run {tools_project}{fastqc_app} -y --priority high --name "
tso500_cmd = f"jobid=$(dx run {tools_project}{tso500_app} --priority high -y --name "
tso500_output_parser_cmd = f"jobid=$(dx run {tools_project}{tso500_output_parser_app} "\
                            "--priority high -y --name "
peddy_cmd = f"jobid=$(dx run {tools_project}{peddy_path}"
multiqc_cmd = f"jobid=$(dx run {tools_project}{multiqc_path}"
upload_multiqc_cmd = f"jobid=$(dx run {tools_project}{upload_multiqc_path} -y"
RPKM_cmd = f"dx run {tools_project}{rpkm_path} --priority high --instance-type mem1_ssd1_x8"
mokaamp_cmd = f"jobid=$(dx run {tools_project}{mokaamp_path} --priority high -y --name "
mokacan_cmd = f"jobid=$(dx run {tools_project}{mokacan_path} --priority high -y --name "
decision_support_preperation = f"analysisid=$(python {decision_support_tool_input_script} -a "
congenica_sftp_upload_cmd = f"echo 'dx run {tools_project}{congenica_SFTP_upload_app}%s -y"

# ---- Moka settings -------------------------------------------------------------------------------

# Moka IDs for generating SQLs to update the Mokadatabase (audit trail)
mokapipe_congenica_pipeline_id = "5137"  # Mokapipe & congenica ID
mokawes_pipeline_id = "5078"  # MokaWES ID
mokaamp_pipeline_id = "4851"  # MokaAMP ID
archerDx_pipeline_id = "4562"  # Archer ID
mokasnp_pipeline_id = "5091"  # MokaSNP ID
mokacan_pipeline_id = "4728"  # mokacan pipeline ID
tso_pipeline_id = "5095"  # TSO500 pipeline ID

# MokaWES test status
mokastatus_nextsq_id = "1202218804"  # Test Status = NextSEQ sequencing
mokastatus_dataproc_id = "1202218805"  # Test Status = Data Processing
