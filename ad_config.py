# coding=utf-8
"""
Automate demultiplex configuration.

The variables defined in this module are required by scripts in the automate_
demultiplex repository (https://github.com/moka-guys/automate_demultiplex)

The config file is split into sections. Those settings that are used across
scripts and those that are specific to a script.
"""

import os

# ================ GENERAL ====================================================
# Settings used across multiple scripts

TESTING = True  # Set testing mode

DOCUMENT_DIR = os.path.dirname(os.path.realpath(__file__))
# Root of folder containing apps, automate_demultiplexing_logfiles and
# development_area scripts (2 levels up from this file)
DOCUMENT_ROOT = "/".join(DOCUMENT_DIR.split("/")[:-2])

AD_LOGDIR = os.path.join(DOCUMENT_ROOT, "automate_demultiplexing_logfiles")


# TSO500 runfolder is used for testing both demultiplexing and usw script
DEMULTIPLEX_TEST_RUNFOLDERS = [
    "999999_A01229_0496_DEMUXINTEG",
    "999999_M02353_0496_000000000-DEMUX",
    "999999_A01229_0049_AHMKTSO500",
]

# Path to run folders - use testing flag to determine folders
if not TESTING:
    RUNFOLDERS = "/media/data3/share"
    # Folder containing demultiplex logs
    DEMULTIPLEX_LOGPATH = os.path.join(RUNFOLDERS, "Demultiplexing_log_files/")
    LOGGING_FORMATTER = (
        "%(asctime)s - %(name)s - %(flag)s - %(levelname)s - %(message)s"
    )
    LOG_FLAGS = {
        "info": "demultiplex_info",
        "fail": "demultiplex_fail",
        "success": "demultiplex_success",
        "ss_warning": "samplesheet_warning",
    }
    EMAIL_HEADER = ""
else:
    RUNFOLDERS = "/media/data3/share/testing"
    # Folder containing demultiplex logs
    DEMULTIPLEX_LOGPATH = os.path.join(AD_LOGDIR, "Demultiplexing_log_files/")

    LOGGING_FORMATTER = (
        "%(asctime)s - TEST MODE - %(name)s - %(flag)s - "
        "%(levelname)s - %(message)s"
    )
    LOG_FLAGS = {
        "info": "demultiplextest_info",
        "fail": "demultiplextest_fail",
        "success": "demultiplextest_success",
        "ss_warning": "testsamplesheet_warning",
    }
    EMAIL_HEADER = (
        "AUTOMATED SCRIPTS ARE BEING RUN IN TEST MODE. "
        "PLEASE IGNORE THIS EMAIL\n\n"
    )


DIRS = {
    "dx_run_cmds": os.path.join(AD_LOGDIR, "dx_run_commands"),
    "fastqs": "/Data/Intensities/BaseCalls",  # Path to fastq files
    "bcl2fastq_stats": "/Data/Intensities/BaseCalls/Stats",
    "backup_runfolderlogs": os.path.join(
        AD_LOGDIR, "backup_runfolder_logfiles"
    ),
}

SAMPLESHEET_NAME = os.path.join(
    RUNFOLDERS, "samplesheets", "%s_SampleSheet.csv"
)
SAMPLESHEET_PATH = os.path.join(
    RUNFOLDERS, "samplesheets", "%s_SampleSheet.csv"
)
BACKUP_RUNFOLDER_LOGFILE = os.path.join(
    DIRS["backup_runfolderlogs"], "%s_backup_runfolder.log"
)
DXRUN_SCRIPT = os.path.join(DIRS["dx_run_cmds"], "%s_dx_run_commands.sh")
# Script containing dnanexus project creation command
PROJ_CREATION_SCRIPT = os.path.join(
    AD_LOGDIR, "nexus_project_creation_scripts", "create_nexus_project_%s.sh"
)
# Path to log file which records the output of the upload agent
UPLOAD_SCRIPT_LOGFILE = os.path.join(
    AD_LOGDIR,
    "upload_agent_script_logfiles",
    "%s_upload_and_setoff_workflow.log",
)
BCL2FASTQ = "/usr/local/bcl2fastq2-v2.20.0.422/bin/bcl2fastq"
#  N.B. n--no-lane-splitting creates a single fastq for a sample,
# not into one fastq per lane)
BCL2FASTQ_CMD = f"{BCL2FASTQ} -R %s --sample-sheet %s --no-lane-splitting"
# Shell command to run cluster density calculation
CD_CMD = (
    "sudo docker run --rm -v %s:/input_run broadinstitute/gatk:4.1.8.1 "
    "./gatk CollectIlluminaLaneMetrics --RUN_DIRECTORY /input_run "
    "--OUTPUT_DIRECTORY /input_run --OUTPUT_PREFIX %s"
)

# TODO move these back to their own variables
PATHS = {
    # DNAnexus run command script
    "congenica_upload_script": os.path.join(
        DIRS["dx_run_cmds"], "%s_congenica.sh"
    ),
    "upload_agent": os.path.join(
        DOCUMENT_ROOT, "apps/dnanexus-upload-agent-1.5.17-linux/ua"
    ),
    "backup_runfolder_script": os.path.join(
        DOCUMENT_ROOT, "apps/workstation_housekeeping/backup_runfolder.py"
    ),
    "dsptool_input_script": os.path.join(
        DOCUMENT_DIR, "decision_support_tool_inputs.py"
    ),
    "email_user": os.path.join(DOCUMENT_ROOT, ".amazon_email_username"),
    "email_pw": os.path.join(DOCUMENT_ROOT, ".amazon_email_pw"),
    "sdk_source": "/etc/profile.d/dnanexus.environment.sh",
    "dnanexus_authtoken": os.path.join(DOCUMENT_ROOT, ".dnanexus_auth_token"),
}

FILENAMES = {
    "rtacomplete": "RTAComplete.txt",  # Sequencing complete file
    "md5checksum": "md5checksum.txt",  # File holding checksum results
    "bcl2fastqlog": "bcl2fastq2_output.log",
    "upload_started": "DNANexus_upload_started.txt",  # Holds UA output
    "bcl2fastq_stats": "Stats.json",
}

RUNFOLDER_PATTERN = "^[0-9]{6}.*$"  # Runfolders start with 6 digits

# ================ AD_EMAIL ===================================================

with open(
    PATHS["email_user"], "r", encoding="utf-8"
) as EMAIL_USER_FILE:  # Get email username
    EMAIL_USER = EMAIL_USER_FILE.readline().rstrip()

with open(
    PATHS["email_pw"], "r", encoding="utf-8"
) as EMAIL_PW_FILE:  # Get email password
    EMAIL_PW = EMAIL_PW_FILE.readline().rstrip()


HOST = "email-smtp.eu-west-1.amazonaws.com"
PORT = 587
SMTP_DO_TLS = True


MOKAGUYS_EMAIL = "gst-tr.mokaguys@nhs.net"
MOKA_ALERTS_EMAIL = "moka.alerts@gstt.nhs.uk"

# Test settings
if TESTING:
    SQL_EMAIL_SUBJ = "SQL ALERT: TESTING - PLEASE IGNORE THIS EMAIL"
    SQL_EMAIL_MSG = "%s being processed using workflow(s) %s\n\n%s\n%s\n"
    MOKAGUYS_RECIPIENT = "mokaguys@gmail.com"
    # Oncology email address for email alerts
    ONCOLOGY_OPS_EMAIL = MOKAGUYS_EMAIL
    WES_SAMPLENAME_EMAILLIST = [MOKAGUYS_EMAIL]

# Production settings
else:
    SQL_EMAIL_SUBJ = "SQL ALERT: Started pipeline for %s"
    SQL_EMAIL_MSG = (
        "%s being processed using workflow(s) %s\n\nPlease update Moka using "
        "the below queries and ensure that %s records are updated:\n\n\n%s\n"
    )
    EMAIL_MSG = (
        "%s being processed using workflow(s) %s\n\nThe following samples are "
        "being processed:\n\n%s\n"
    )

    MOKAGUYS_RECIPIENT = MOKAGUYS_EMAIL
    # Oncology email address for email alerts
    ONCOLOGY_OPS_EMAIL = "m.neat@nhs.net"
    WES_SAMPLENAME_EMAILLIST = [
        "gst-tr.ViapathGeneticsAdmin@nhs.net",
        "lu.liu@viapath.co.uk",
        "Suzanne.lillis@viapath.co.uk",
        "eblab@gstt.nhs.uk",
        MOKAGUYS_EMAIL,
    ]

# ================ UPLOAD AND SETOFF WORKFLOWS ================================
# Settings unique to the upload and setoff workflows script

REF_SAMPLE_IDS = [
    "NA12878",
    "136819",
]  # NA12878 identifiers to exclude from congenica upload

# ---- Filepaths --------------------------------------------------------------


# ---- Commands and strings ---------------------------------------------------
UPLOAD_AGENT_TEST_CMD = " --version"
DX_SDK_TEST = f"source {PATHS['sdk_source']};dx --version"  # Tests dx toolkit
BACKUP_RUNFOLDER_SUCCESS = "backup_runfolder INFO - END"
BACKUP_RUNFOLDER_ERROR = "backup_runfolder.UAcaller ERROR"
DX_SDK_TEST_EXPECTED_STDOUT = "dx v0.2"  # Expected result from testing
UPLOAD_AGENT_EXPECTED_STDOUT = (
    "Upload Agent Version:"  # Upload agent test response
)

STRINGS = {
    "cd_success": "picard.illumina.CollectIlluminaLaneMetrics done",
    "cd_err": "Exception",
}

DEMULTIPLEXLOG_TSO500MSG = "TSO500 run. Does not need demultiplexing locally"
DEMULTIPLEX_SUCCESS_REGEX = (
    r".*Processing completed with 0 errors and 0 warnings.$"
)

CLUSTER_DENSITY_FILE_SUFFIX = ".illumina_lane_metrics"
PHASING_METRICS_FILE_SUFFIX = ".illumina_phasing_metrics"

# ================ DEMULTIPLEXING (demultiplex.py) ============================
# Settings unique to the demultiplex script

# Sequencer / run identifiers
NOVASEQ_ID = "A01229"
SEQUENCER_IDS = ["NB551068", "NB552085", "M02353", "M02631", NOVASEQ_ID]
RUNTYPE_LIST = ["NGS", "ADX", "ONC", "SNP", "TSO", "LRPCR"]
# Sequencers requiring md5 checksums from integrity check to be assessed
SEQUENCERS_WITH_INTEGRITY_CHECK = ["NB551068", "NB552085", NOVASEQ_ID]


# Integrity check
CHECKSUM_COMPLETE_MSG = (
    "Checksum result reported"  # Checksum complete statement
)
CHECKSUM_MATCH_MSG = (
    "Checksums match"  # Statement to write when checksums match
)


LOG_MSGS = {
    "email": {
        "email_sending": (
            "Sending an email. Recipient: %s. Subject: %s. Body: %s"
        ),
        "email_pass": "Email sent without error",
        "email_fail": (
            "Error when sending email. Email not sent. Exception: %s"
        ),
    },
    "demultiplex": {
        "demux_script_start": "Automate demultiplex release %s: "
        "Demultiplex.py started on workstation",
        "demux_script_end": (
            "Automate demultiplex release %s: Demultiplex.py complete"
        ),
        "runfolders_processed": "%s runfolder(s) processed",
        "rename_demuxlog_success": (
            "Demultiplex logfile successfully renamed with "
            "runfolder names. New name: %s"
        ),
        "rename_demuxlog_fail": (
            "Demultiplex logfile rename failed for file %s with exception: %s"
        ),
        "rename_demuxlog_pass": (
            "Demultiplex logfile rename passed for file %s. Now %s"
        ),
        "demux_runfolder_start": (
            "Automate_demultiplex release: %s -------------- Assessing %s"
        ),
        "ic_fail": (
            "Integrity check fail. Checksums do not match for %s see %s"
        ),
        "bcl2fastq_start": (
            "Demultiplexing started for run %s using bcl2fastq command: %s"
        ),
        "bcl2fastq_complete": "bcl2fastq subprocess complete for run %s",
        "bcl2fastq_failed": "bcl2fastq subprocess failed for run %s",
        "demux_already_complete": (
            "Demultiplexing already completed - "
            "bcl2fastq log found @ %s --- STOP ---"
        ),
        "demux_not_complete": (
            "Demultiplexing not yet completed - no demultiplex "
            "log found @ %s --- CONTINUE ---"
        ),
        "sschecks_not_passed": "Samplesheet did not pass checks %s: %s",
        "sschecks_passed": "Samplesheet passed all checks %s",
        "run_finished": "Run finished - RTAComplete.txt found @ %s",
        "run_incomplete": (
            "Sequencing not yet complete (RTAComplete.txt "
            "file absent) @ %s --- STOP ---"
        ),
        "bcl2fastq_test_fail": "BCL2FastQ installation test failed",
        "bcl2fastq_test_pass": "BCL2FastQ installation test passed",
        "ssfail_haltdemux": (
            "Demultiplexing halted due to samplesheet errors %s: %s"
        ),
        "ic_required": (
            "This run was sequenced on a sequencer that requires integrity "
            "checking"
        ),
        "ic_notrequired": "Integrity check not required",
        "csumfile_present": (
            "Checksums file present - checksums have been "
            "generated by integrity check scripts"
        ),
        "csumfile_absent": (
            "Demultiplexing halted: Integrity check not yet performed on "
            "sequencer (checksum file absent)"
        ),
        "checksums_checked": "Checksums already checked for this run",
        "checksums_notchecked": "Checksums not yet checked for this run",
        "ic_start": "Data integrity checks starting...",
        "ic_pass": "Integrity check for runfolder %s passed",
        "create_bcl2fastqlog_pass": "Created bcl2fastq logfile for run %s",
        "create_bcl2fastqlog_fail": (
            "Failed to create bcl2fastq logfile for run %s. Exception: %s"
        ),
        "TSO500_run": f"%s is a {DEMULTIPLEXLOG_TSO500MSG}",
        "write_TSO_msg_to_bcl2fastqlog": (
            "TSO500 message successfully written to "
            "bcl2fastq2_output.log file for TSO run: %s"
        ),
        "demux_complete": "Demultiplexing complete without error for run %s",
        "demux_error": (
            "ERROR - DEMULTIPLEXING UNSUCCESSFUL (BCL2FastQ2 ERROR) "
            "- Demultiplexing failed for run %s. Please see logfile %s"
        ),
        "bcl2fastqlog_empty": (
            "ERROR - BCL2FASTQ2 logfile is empty for run %s. "
            "Please see logfile %s"
        ),
        "bcl2fastqlog_absent": (
            "ERROR - BCL2FASTQ2 logfile does not exist for "
            "run %s. Please see logfile "
        ),
        "running_cd": (
            "Running the following command for cluster density calculation: %s"
        ),
        "cd_success": (
            "Cluster density calculation saved to "
            f"%s{CLUSTER_DENSITY_FILE_SUFFIX}"
        ),
        "cd_fail": ("Cluster density calculation failed for : %s. Error: %s"),
    },
}

MOKAWES_SENTIEON_BAM_OUTPUT_NAME = "mappings_bam"
MOKAWES_SENTIEON_BAI_OUTPUT_NAME = "mappings_bam_bai"
MOKAWES_SENTIEON_VCF_OUTPUT_NAME = "variants_vcf"
MOKAPIPE_VCF_OUTPUT_NAME = "filtered_vcf"
MOKAPIPE_BAM_OUTPUT_NAME = "bam"

#  ================  DNAnexus  ================================================

# General
with open(PATHS["dnanexus_authtoken"], "r", encoding="utf-8") as TOKEN_FILE:
    DNANEXUS_APIKEY = TOKEN_FILE.readline().rstrip()  # Auth token

BEDFILE_FOLDER = "Data/BED/"
DNANEXUS_PROJECT_PREFIX = "002_"  # Project to upload run folder into
PROJECT_SUCCESS = 'Created new project called "%s"'  # Success statement
PROD_ORGANISATION = "org-viapath_prod"  # Prod org for billing

DNANEXUS_USERS = {  # User access level
    "viewers": ['org-viapath_prod", "InterpretationRequest'],
    "admins": ["mokaguys"],
}

# Paths / IDs for apps in 001_Tools
TOOLS_PROJECT = "project-ByfFPz00jy1fk6PjpZ95F27J"  # 001_ToolsReferenceData

NEXUS_IDS = {
    "FILES": {
        "tso500_docker": f"{TOOLS_PROJECT}:file-Fz9Zyx00b5j8xKVkKv4fZ6JB",
        "hs37d5_bwa_index": f"{TOOLS_PROJECT}:file-B6ZY4942J35xX095VZyQBk0v",
        "hs37d5_ref": f"{TOOLS_PROJECT}:file-ByYgX700b80gf4ZY1GxvF3Jv",
    },
    "APPS": {
        "TSO500": f"{TOOLS_PROJECT}:applet-GPgkz0j0jy1Yf4XxkXjVgKfv",
        "TSO500_OP": f"{TOOLS_PROJECT}:applet-GP0YXB00jy1kYKYp33yJZJ5B",
        "congenica_SFTP": f"{TOOLS_PROJECT}:applet-GFfJpj80jy1x1Bz1P1Bk3vQf",
        "upload_multiqc": f"{TOOLS_PROJECT}:applet-G2XY8QQ0p7kzvPZBJGFygP6f",
        "multiqc": f"{TOOLS_PROJECT}:applet-GPgbyk00jy1kpgvggbp12Vfg",
        "sompy": f"{TOOLS_PROJECT}:applet-G9yPb780jy1p660k6yBvQg07",
        "sambamba": f"{TOOLS_PROJECT}:applet-G6vyyf00jy1kPkX9PJ1YkxB1",
        "fastqc": f"{TOOLS_PROJECT}:applet-FBPFfkj0jy1Q114YGQ0yQX8Y",
        "gatk": f"{TOOLS_PROJECT}:applet-FYZ097j0jy1ZZPx30GykP63J",
        "peddy": f"{TOOLS_PROJECT}:applet-Fjvfk280jy1fVg8Q3b1bF6Y1",
        "rpkm": f"{TOOLS_PROJECT}:applet-FxJj0F00jy1ZVXp36PBz2p1j",
    },
    "WORKFLOWS": {
        "mokapipe": f"{TOOLS_PROJECT}:workflow-GPq04280jy1k1yVkQP0fXqBg",
        "mokawes": f"{TOOLS_PROJECT}:workflow-FjjbQ5Q0jy1ZgyjQ3g1zgx9k",
        "mokaamp": f"{TOOLS_PROJECT}:workflow-G6F70180jy1gGK38FYXk618g",
        "mokacan": f"{TOOLS_PROJECT}:workflow-G3vYKQj0jy1jy4FzKGvjJZK9",
        "mokasnp": f"{TOOLS_PROJECT}:workflow-GB3kyJj0jy1j06704fxX9J7j",
    },
    "STAGES": {
        "mokapipe": {
            "filter_vcf": "stage-G5Kpgv80zB02Q64zFf94G05F",
            "gatk": "stage-F28y4qQ0jy1fkqfy5v2b8byx",
            "fastqc": "stage-Bz3YpP80jy1Y1pZKbZ35Bp0x",
            "bwa": "stage-Byz9BJ80jy1k2VB9xVXBp0Fg",
            "picard": "stage-F9GK4QQ0jy1qj14PPZxxq3VG",
            "happy": "stage-G8V205j0fB6QGKXQ2gZ5pB1z",
            "sambamba": "stage-F35zBKQ0jy1XpfzYPZY4bgX6",
            "fhprs": "stage-G9BfkZQ0fB6jZY7v1PfJ81F6",
            "polyedge": "stage-GK71VJ80VQgQkjvz0vyQ8YV1",
        },
        "mokawes": {
            "fastqc1": "stage-Ff0P5Jj0GYKY717pKX3vX8Z3",
            "fastqc2": "stage-Ff0P5V00GYKyJfpX5bqX69Yg",
            "picard": "stage-Ff0P5pQ0GYKVBB0g1FG27BV8",
            "sambamba": "stage-Ff0P82Q0GYKQ4j8b4gXzjqxX",
            "sentieon": "stage-Ff0P73j0GYKX41VkF3j62F9j",
        },
        "mokasnp": {
            "fastqc1": "stage-FgPp4V00YkVJVjKF4kYkBF8v",
            "fastqc2": "stage-FgPp4V00YkVJVjKF4kYkBF90",
            "sentieon": "stage-FgPp4XQ0YkV48jZG4Py6F55k",
        },
        "mokaamp": {
            "fastqc1": "stage-FPzGj780jy1g3p1F4F8z4J7V",
            "fastqc2": "stage-FPzGj780jy1g3p1F4F8z4J7V",
            "bwa": "stage-FPzGj780jy1g3p1F4F8z4J7V",
            "picard": "stage-FPzGjV80jy1x97jg607Fg22b",
            "ampliconfilt": "stage-FPzGjJQ0jy1fF6505zFP6zz9",
            "sambamba": "stage-FPzGjfQ0jy1y01vG60K22qG1",
            "vardict": "stage-G0vKZk80GfYkQx86PJGGjz9Y",
            "varscan": "stage-FPzGjp80jy1V3Jvb5z6xfpfZ",
            "mpileup": "stage-FxypXb807p1zj3g8Jv45Y54P",
        },
        "mokacan": {
            "fastqc1": "stage-FPzGj6Q0jy1fF6505zFP6zz5",
            "fastqc2": "stage-FPzGj5j0jy1x97jg607Fg229",
            "picard": "stage-FPzGjV80jy1x97jg607Fg22b",
            "sambamba": "stage-FPzGjfQ0jy1y01vG60K22qG1",
            "vardict": "stage-FPzGjgj0jy1Q2JJF2zYx5J5k",
            "sentieon": "stage-FgYgB2Q087fjzvxy9f4q1K8X",
            "varscan": "stage-FPzGjp80jy1V3Jvb5z6xfpfZ",
        },
    },
}

# Inputs for apps run outside of workflows
APP_INPUTS = {
    "tso500": {
        "docker": " -iTSO500_ruo=",
        "samplesheet": " -isamplesheet=",
        "analysis_options": " -ianalysis_options=",
        "project_name": " -iproject_name=",
        "ht_instance": "mem1_ssd1_v2_x72",
        "lt_instance": "mem1_ssd1_v2_x36",
    },
    "tso500_op": {
        "project_name": " -iproject_name=",
        "project_id": " -iproject_id=",
        "tso500_jobid": " -itso500_jobid=",
        "sambamba_bed": " -icoverage_bedfile_id=",
        "sambamba_id": " -icoverage_app_id=",
        "fastqc_id": " -ifastqc_app_id=",
        "sompy_id": " -isompy_app_id=",
        "multiqc_id": " -imultiqc_app_id=",
        "upload_multiqc_id": " -iupload_multiqc_app_id=",
        "sambamba_cov_cmds": (
            " -icoverage_commands='-imerge_overlapping_mate_reads=true "
            "-iexclude_failed_quality_control=true "
            "-iexclude_duplicate_reads=true "
            "-imin_base_qual=%s -imin_mapping_qual=%s'"
        ),
        "sambamba_cov_level": " -icoverage_level=",
        "multiqc_cov_level": " -imultiqc_coverage_level=",
    },
    "peddy": {
        "project_name": " -iproject_for_peddy=",
    },
    "multiqc": {
        "project_name": " -iproject_for_multiqc=",
        "coverage_level": " -icoverage_level=",
    },
    "congenica_upload": {
        "vcf": " -ivcf=",
        "bam": " -ibam=",
        "samplename": " -ianalysis_name=",
    },
}

# Set 6 hour timeout policy for gatk app and jobtimeoutexceeded
# reason to auto restart list
# TODO move this to the DXAPP.JSON file for FH app
MOKAPIPE_FH_GATK_TIMEOUT_ARGS = (
    ' --extra-args \'{"timeoutPolicyByExecutable": {"'
    f'{NEXUS_IDS["APPS"]["gatk"]}'
    '": {"*":{"hours": 6}}}, "executionPolicy": {"restartOn": '
    '{"JobTimeoutExceeded":1, "JMInternalError":'
    ' 1, "UnresponsiveWorker": 2, "ExecutionError":1}}}\''
)

# Paths / IDs for workflows in 001_Tools
TSO500_APP_NAME = "TSO500_v1.5.1"


STAGE_INPUTS = {
    "mokapipe": {
        "fastqc_reads": (
            f" -i{NEXUS_IDS['STAGES']['mokapipe']['fastqc']}.reads="
        ),
        "bwa_reads1": (
            f" -i{NEXUS_IDS['STAGES']['mokapipe']['bwa']}.reads_fastqgz="
        ),
        "bwa_reads2": (
            f" -i{NEXUS_IDS['STAGES']['mokapipe']['bwa']}.reads2_fastqgz="
        ),
        "bwa_rg_sample": (
            f" -i{NEXUS_IDS['STAGES']['mokapipe']['bwa']}.read_group_sample="
        ),
        "bwa_ref": (
            f" -i{NEXUS_IDS['STAGES']['mokapipe']['bwa']}.genomeindex_targz="
        ),
        # HSMetrics Bedfile
        "picard_bed": (
            f" -i{NEXUS_IDS['STAGES']['mokapipe']['picard']}"
            f".vendor_exome_bedfile="
        ),
        "picard_capturetype": (
            f" -i{NEXUS_IDS['STAGES']['mokapipe']['picard']}.Capture_panel="
        ),
        "gatk_padding": (
            f" -i{NEXUS_IDS['STAGES']['mokapipe']['gatk']}.padding="
        ),
        "gatk_vcf_format": (
            f" -i{NEXUS_IDS['STAGES']['mokapipe']['gatk']}.output_format=both"
        ),
        "filter_vcf_bed": (
            f" -i{NEXUS_IDS['STAGES']['mokapipe']['filter_vcf']}.bedfile="
        ),
        "happy_skip": f" -i{NEXUS_IDS['STAGES']['mokapipe']['happy']}.skip=",
        "happy_prefix": (
            f" -i{NEXUS_IDS['STAGES']['mokapipe']['happy']}.prefix="
        ),
        "sambamba_bed": (
            f" -i{NEXUS_IDS['STAGES']['mokapipe']['sambamba']}.sambamba_bed="
        ),
        "sambamba_min_base_qual": (
            f" -i{NEXUS_IDS['STAGES']['mokapipe']['sambamba']}"
            f".min_base_qual=10"
        ),
        "sambamba_min_mapping_qual": (
            f" -i{NEXUS_IDS['STAGES']['mokapipe']['sambamba']}"
            f".min_mapping_qual=20"
        ),
        "sambamba_cov_level": (
            f" -i{NEXUS_IDS['STAGES']['mokapipe']['sambamba']}"
            f".coverage_level=30"
        ),
        "sambamba_filter_cmds": (
            f" -i{NEXUS_IDS['STAGES']['mokapipe']['sambamba']}"
            ".additional_filter_commands="
            "'not (unmapped or secondary_alignment)'"
        ),
        "sambamba_excl_dups": (
            f" -i{NEXUS_IDS['STAGES']['mokapipe']['sambamba']}"
            ".exclude_duplicate_reads=true"
        ),
        "sambamba_excl_failed_qual": (
            f" -i{NEXUS_IDS['STAGES']['mokapipe']['sambamba']}"
            ".exclude_failed_quality_control=true"
        ),
        "sambamba_count_overl_mates": (
            f" -i{NEXUS_IDS['STAGES']['mokapipe']['sambamba']}"
            ".merge_overlapping_mate_reads=true"
        ),
        "fhprs_skip": (
            f" -i{NEXUS_IDS['STAGES']['mokapipe']['fhprs']}.skip=false"
        ),
        "fhprs_bed": (
            f" -i{NEXUS_IDS['STAGES']['mokapipe']['fhprs']}.BEDfile="
        ),
        "fhprs_instance": "mem3_ssd1_v2_x8",  # Required when creating gVCFs
        "polyedge_str": (
            " -i%(stage_str)s.gene={} -i%(stage_str)s.chrom={} "
            "-i%(stage_str)s.poly_start={} -i%(stage_str)s.poly_end={} "
            "-i%(stage_str)s.skip=false"
            % {"stage_str": NEXUS_IDS["STAGES"]["mokapipe"]["polyedge"]}
        ),
    },
    "rpkm": {
        "bed": " -ibedfile=",
        "proj": " -iproject_name=",
        "pannos": " -ibamfile_pannumbers=",
    },
    "mokawes": {
        "fastqc1_reads": (
            f" -i{NEXUS_IDS['STAGES']['mokawes']['fastqc1']}.reads="
        ),
        "fastqc2_reads": (
            f" -i{NEXUS_IDS['STAGES']['mokawes']['fastqc2']}.reads="
        ),
        # HSmetrics bedfile
        "picard_bed": (
            f" -i{NEXUS_IDS['STAGES']['mokawes']['picard']}"
            f".vendor_exome_bedfile="
        ),
        "sambamba_bed": (
            f" -i{NEXUS_IDS['STAGES']['mokawes']['sambamba']}.sambamba_bed="
        ),
        # Prevents incorrect parsing from fastq filename
        "sentieon_samplename": (
            f" -i{NEXUS_IDS['STAGES']['mokawes']['sentieon']}.sample="
        ),
        "sentieon_bed": (
            f" -i{NEXUS_IDS['STAGES']['mokawes']['sentieon']}.targets_bed="
        ),
    },
    "mokasnp": {
        "fastqc1_reads": (
            f" -i{NEXUS_IDS['STAGES']['mokasnp']['fastqc1']}.reads="
        ),
        "fastqc2_reads": (
            f" -i{NEXUS_IDS['STAGES']['mokasnp']['fastqc2']}.reads="
        ),
        "sentieon_bed": (
            f" -i{NEXUS_IDS['STAGES']['mokasnp']['sentieon']}.targets_bed="
        ),
        # Prevents incorrect parsing from fastq filename
        "sentieon_samplename": (
            f" -i{NEXUS_IDS['STAGES']['mokasnp']['sentieon']}.sample="
        ),
    },
    "mokaamp": {
        "fastqc1_reads": (
            f" -i{NEXUS_IDS['STAGES']['mokaamp']['fastqc1']}.reads_fastqgz="
        ),
        "fastqc2_reads": (
            f" -i{NEXUS_IDS['STAGES']['mokaamp']['fastqc1']}.reads2_fastqgz="
        ),
        "bwa_rg_sample": (
            f" -i{NEXUS_IDS['STAGES']['mokaamp']['bwa']}.read_group_sample="
        ),
        "bwa_ref": (
            f" -i{NEXUS_IDS['STAGES']['mokaamp']['bwa']}"
            f".genomeindex_targz={NEXUS_IDS['FILES']['hs37d5_bwa_index']}"
        ),
        "picard_bed": (
            f" -i{NEXUS_IDS['STAGES']['mokaamp']['picard']}"
            f".vendor_exome_bedfile="
        ),
        "picard_capturetype": (
            f" -i{NEXUS_IDS['STAGES']['mokaamp']['picard']}.Capture_panel="
        ),
        "picard_ref": (
            f" -i{NEXUS_IDS['STAGES']['mokaamp']['picard']}."
            f"fasta_index={NEXUS_IDS['FILES']['hs37d5_ref']}"
        ),
        "ampliconfilt_bed": (
            f" -i{NEXUS_IDS['STAGES']['mokaamp']['ampliconfilt']}.PE_BED="
        ),
        "sambamba_cov_level": (
            f" -i{NEXUS_IDS['STAGES']['mokaamp']['sambamba']}.coverage_level="
        ),
        "sambamba_bed": (
            f" -i{NEXUS_IDS['STAGES']['mokaamp']['sambamba']}.sambamba_bed="
        ),
        "vardict_ref": (
            f" -i{NEXUS_IDS['STAGES']['mokaamp']['vardict']}."
            f"ref_genome={NEXUS_IDS['FILES']['hs37d5_ref']}"
        ),
        "vardict_bed": (
            f" -i{NEXUS_IDS['STAGES']['mokaamp']['vardict']}.bedfile="
        ),
        "vardict_samplename": (
            f" -i{NEXUS_IDS['STAGES']['mokaamp']['vardict']}"
            f".sample_name=vardict_"
        ),
        "varscan_ref": (
            f" -i{NEXUS_IDS['STAGES']['mokaamp']['varscan']}."
            f"ref_genome={NEXUS_IDS['FILES']['hs37d5_ref']}"
        ),
        "varscan_bed": (
            f" -i{NEXUS_IDS['STAGES']['mokaamp']['varscan']}.bed_file="
        ),
        "varscan_samplename": (
            f" -i{NEXUS_IDS['STAGES']['mokaamp']['varscan']}"
            f".samplename=varscan_"
        ),
        "varscan_strandfilter": (
            f" -i{NEXUS_IDS['STAGES']['mokaamp']['varscan']}.strand_filter="
        ),
        "mpileup_covlevel": (
            f" -i{NEXUS_IDS['STAGES']['mokaamp']['mpileup']}.min_coverage="
        ),
    },
    "mokacan": {
        "fastqc1_reads": (
            f" -i{NEXUS_IDS['STAGES']['mokacan']['fastqc1']}.reads="
        ),
        "fastqc2_reads": (
            f" -i{NEXUS_IDS['STAGES']['mokacan']['fastqc2']}.reads="
        ),
        "picard_bed": (
            f" -i{NEXUS_IDS['STAGES']['mokacan']['picard']}"
            f".vendor_exome_bedfile="
        ),
        "picard_capturetype": (
            f" -i{NEXUS_IDS['STAGES']['mokacan']['picard']}.Capture_panel="
        ),
        "picard_ref": (
            f" -i{NEXUS_IDS['STAGES']['mokacan']['picard']}."
            f"fasta_index={NEXUS_IDS['FILES']['hs37d5_ref']}"
        ),
        "sambamba_bed": (
            f" -i{NEXUS_IDS['STAGES']['mokacan']['sambamba']}.sambamba_bed="
        ),
        "sambamba_cov_level": (
            f" -i{NEXUS_IDS['STAGES']['mokacan']['sambamba']}.coverage_level="
        ),
        "vardict_ref": (
            f" -i{NEXUS_IDS['STAGES']['mokacan']['vardict']}."
            f"ref_genome={NEXUS_IDS['FILES']['hs37d5_ref']}"
        ),
        "vardict_bed": (
            f" -i{NEXUS_IDS['STAGES']['mokacan']['vardict']}.bedfile="
        ),
        "vardict_samplename": (
            f" -i{NEXUS_IDS['STAGES']['mokacan']['vardict']}"
            f".sample_name=vardict_"
        ),
        "varscan_ref": (
            f" -i{NEXUS_IDS['STAGES']['mokacan']['varscan']}."
            f"ref_genome={NEXUS_IDS['FILES']['hs37d5_ref']}"
        ),
        "varscan_bed": (
            f" -i{NEXUS_IDS['STAGES']['mokacan']['varscan']}.bed_file="
        ),
        "sentieon_samplename": (
            f" -i{NEXUS_IDS['STAGES']['mokacan']['sentieon']}.sample="
        ),
        "sentieon_bwa_ref": (
            f" -i{NEXUS_IDS['STAGES']['mokacan']['sentieon']}"
            f".genomebwaindex_targz="
            f"{TOOLS_PROJECT}:{NEXUS_IDS['FILES']['hs37d5_bwa_index']}"
        ),
        "sentieon_ref": (
            f" -i{NEXUS_IDS['STAGES']['mokacan']['sentieon']}.genome_fastagz="
            f"{TOOLS_PROJECT}:file-B6ZY7VG2J35Vfvpkj8y0KZ01"
        ),
    },
}

# Command strings
SOURCE_CMD = f"#!/bin/bash\n. {PATHS['sdk_source']}\ndepends_list=''"

DX_RUN_CMDS = {
    "create_proj": (
        'project_id="$(dx new project --bill-to %s "%s" --brief '
        '--auth-token %s)"\n'
    ),
    "mokapipe": (
        f"jobid=$(dx run {NEXUS_IDS['WORKFLOWS']['mokapipe']}"
        " --priority high -y --name "
    ),
    "mokawes": (
        f"jobid=$(dx run {NEXUS_IDS['WORKFLOWS']['mokawes']}"
        " --priority high -y --name "
    ),
    "mokasnp": (
        f"jobid=$(dx run {NEXUS_IDS['WORKFLOWS']['mokasnp']}"
        " -y --priority high --name "
    ),
    "mokaamp": (
        f"jobid=$(dx run {NEXUS_IDS['WORKFLOWS']['mokaamp']}"
        " --priority high -y --name "
    ),
    "mokacan": (
        f"jobid=$(dx run {NEXUS_IDS['WORKFLOWS']['mokacan']}"
        " --priority high -y --name "
    ),
    "tso500": (
        f"jobid=$(dx run {NEXUS_IDS['APPS']['TSO500']}"
        " --priority high -y --name "
    ),
    "tso500_op": (
        f"jobid=$(dx run {NEXUS_IDS['APPS']['TSO500_OP']}"
        " --priority high -y --name "
    ),
    "fastqc": (
        f"jobid=$(dx run {NEXUS_IDS['APPS']['fastqc']} -y "
        "--priority high --name "
    ),
    "peddy": f"jobid=$(dx run {NEXUS_IDS['APPS']['peddy']}",
    "multiqc": f"jobid=$(dx run {NEXUS_IDS['APPS']['multiqc']}",
    "upload_multiqc": (
        f"jobid=$(dx run {NEXUS_IDS['APPS']['upload_multiqc']} -y"
    ),
    "rpkm": (
        f"dx run {NEXUS_IDS['APPS']['rpkm']}"
        " --priority high --instance-type mem1_ssd1_x8"
    ),
    "decision_support_prep": (
        f"analysisid=$(python {PATHS['dsptool_input_script']} -a "
    ),
    "congenica_sftp": (
        f"echo 'dx run {NEXUS_IDS['APPS']['congenica_SFTP']}%s -y"
    ),
}

USW_LOGMSGS = {
    "script_start": "automate_demultiplexing release:%s",
    "create_proj_success": (
        "DNA Nexus project %s created and shared (VIEW) to %s"
    ),
    "create_proj_fail": "UA_fail 'failed to create project in dna nexus'",
}
# ---- Moka settings ----------------------------------------------------------

# Moka IDs for generating SQLs to update the Mokadatabase (audit trail)
SQL_IDS = {
    "WORKFLOWS": {
        "mokapipe": 5229,
        "mokawes": 5078,
        "mokaamp": 4851,
        "archerdx": 4562,
        "mokasnp": 5091,
        "mokacan": 4728,
        "tso500": 5234,
    },
    "WES_TEST_STATUS": {
        "nextseq_sequencing": 1202218804,  # Test Status = NextSEQ sequencing
        "data_processing": 1202218805,  # Test Status = Data Processing
    },
}

POLYEDGE_INPUTS = {
    "MSH2": {
        "chrom": 2,
        "poly_start": 47641559,
        "poly_end": 47641586,
    }
}
