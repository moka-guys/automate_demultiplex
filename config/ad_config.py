# coding=utf-8
"""
Automate demultiplex configuration.

The variables defined in this module are required by scripts in the automate_
demultiplex repository (https://github.com/moka-guys/automate_demultiplex)

The config file is split into sections. Those settings that are used across
scripts and those that are specific to a script.
"""
# TODO move log file paths back to production locations when testing done
import os

# ================ GENERAL ====================================================
# Settings used across multiple scripts

TESTING = True  # Set testing mode

DOCUMENT_DIR = "/".join((os.path.dirname(os.path.realpath(__file__)).split("/")[:-1]))
# Root of folder containing apps, automate_demultiplexing_logfiles and
# development_area scripts (2 levels up from this file)
DOCUMENT_ROOT = "/".join(DOCUMENT_DIR.split("/")[:-2])

# TSO500 runfolder is used for testing both demultiplexing and usw script
DEMULTIPLEX_TEST_RUNFOLDERS = [
    "999999_NB552085_0496_DEMUXINTEG",
    "999999_M02353_0496_000000000-DEMUX",
    "999999_A01229_0182_AHM2TSO500",
]

# Path to run folders - use testing flag to determine folders
if not TESTING:
    JOB_NAME_STR = "--name "
    RUNFOLDERS = "/media/data3/share"
    AD_LOGDIR = os.path.join(DOCUMENT_ROOT, "automate_demultiplexing_logfiles")
    LOGGING_FORMATTER = (
        "%(asctime)s - %(name)s - %(flag)s - %(levelname)s - %(message)s"
    )
    EMAIL_HEADER = ""
else:
    # This must be @-separated to be picked up by the gmail filter which
    # determines which slack channel to send the alert to
    JOB_NAME_STR = "--name TEST@"
    RUNFOLDERS = "/media/data3/share/testing"
    AD_LOGDIR = os.path.join(RUNFOLDERS, "automate_demultiplexing_logfiles")
    LOGGING_FORMATTER = (
        "%(asctime)s - TEST MODE - %(name)s - %(flag)s - %(levelname)s - %(message)s"
    )
    EMAIL_HEADER = (
        "AUTOMATED SCRIPTS ARE BEING RUN IN TEST MODE. PLEASE IGNORE THIS EMAIL\n\n"
    )

DIRS = {
    "fastqs": "Data/Intensities/BaseCalls",  # Path to fastq files
    "tso_fastqs": "analysis_folder/Logs_Intermediates/CollapsedReads/",
    "bcl2fastq_stats": "Data/Intensities/BaseCalls/Stats",
}

SAMPLESHEET_NAME = "%s_SampleSheet.csv"
SAMPLESHEET_PATH = os.path.join(RUNFOLDERS, "samplesheets", SAMPLESHEET_NAME)

# Folders containing logfiles
LOGDIRS = {
    "demultiplex": os.path.join(AD_LOGDIR, "Demultiplexing_log_files/"),
    "dx_run_cmds": os.path.join(AD_LOGDIR, "dx_run_commands"),
    "backup_runfolder": os.path.join(AD_LOGDIR, "backup_runfolder_logfiles"),
    "upload_script": os.path.join(AD_LOGDIR, "upload_agent_script_logfiles"),
    "nexus_project_creation_scripts": (
        os.path.join(AD_LOGDIR, "nexus_project_creation_scripts")
    ),
}

# Paths to logfiles
LOGFILES = {
    # Records output of demultiplex script
    "demultiplex_script_logfile": os.path.join(
        LOGDIRS["demultiplex"], "%s_demultiplex_script_log.log"
    ),
    # Records output of upload and setoff workflow script
    "upload_script": os.path.join(
        LOGDIRS["upload_script"], "%s_upload_and_setoff_workflow.log"
    ),
    "backup_runfolder": os.path.join(
        LOGDIRS["backup_runfolder"], "%s_backup_runfolder.log"
    ),
    "dx_run_script": os.path.join(LOGDIRS["dx_run_cmds"], "%s_dx_run_commands.sh"),
    # DNAnexus run command script
    "congenica_upload_script": os.path.join(LOGDIRS["dx_run_cmds"], "%s_congenica.sh"),
    # Script containing dnanexus project creation command
    "proj_creation_script": os.path.join(
        LOGDIRS["nexus_project_creation_scripts"], "create_nexus_project_%s.sh"
    ),
}

SCRIPTS = {
    "sdk_source": "/usr/local/src/mokaguys/apps/dx-toolkit/environment",
    "dsptool_input_script": os.path.join(
        DOCUMENT_DIR, "decision_support_tool_inputs.py"
    ),
}

# TODO move these back to their own variables
EXECUTABLES = {
    "bcl2fastq": "/usr/local/bcl2fastq2-v2.20.0.422/bin/bcl2fastq",
    "upload_agent": os.path.join(
        DOCUMENT_ROOT, "apps/dnanexus-upload-agent-1.5.17-linux/ua"
    ),
}

CREDENTIALS = {
    "email_user": os.path.join(DOCUMENT_ROOT, ".amazon_email_username"),
    "email_pw": os.path.join(DOCUMENT_ROOT, ".amazon_email_pw"),
    "dnanexus_authtoken": os.path.join(DOCUMENT_ROOT, ".dnanexus_auth_token"),
}

CMDS = {
    # N.B. n--no-lane-splitting creates a single fastq for a sample,
    # not into one fastq per lane)
    "bcl2fastq": (
        f"{EXECUTABLES['bcl2fastq']} -R %s --sample-sheet %s " "--no-lane-splitting"
    ),
    # Shell command to run cluster density calculation
    "cluster_density": (
        "sudo docker run --rm -v %s:/input_run broadinstitute/gatk:4.1.8.1 "
        "./gatk CollectIlluminaLaneMetrics --RUN_DIRECTORY /input_run "
        "--OUTPUT_DIRECTORY /input_run --OUTPUT_PREFIX %s"
    ),
    "sdk_source": f"#!/bin/bash\n. {SCRIPTS['sdk_source']}\n",
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

MAIL_SETTINGS = {
    "host": "email-smtp.eu-west-1.amazonaws.com",
    "port": 587,
    "binfx_email": "gst-tr.mokaguys@nhs.net",
    "alerts_email": "moka.alerts@gstt.nhs.uk",
    "pipeline_started_subj": f"{EMAIL_HEADER}  ALERT: Started pipeline for %s",
    "sql_email_msg": "%s being processed using workflow(s) %s\n\n%s\n%s\n",
    "email_msg": False,
    "binfx_recipient": "mokaguys@gmail.com",
    # Oncology email address for email alerts
    "oncology_ops_email": "mokaguys@gmail.com",
    "wes_samplename_emaillist": "mokaguys@gmail.com",
}

if not TESTING:  # Overwrite test settings with prod settings
    MAIL_SETTINGS = MAIL_SETTINGS | {
        "sql_email_msg": (
            "%s being processed using workflow(s) %s\n\nPlease update Moka "
            "using the below queries and ensure that %s records are "
            "updated:\n\n\n%s\n"
        ),
        "email_msg": (
            "%s being processed using workflow(s) %s\n\nThe following samples "
            "are being processed:\n\n%s\n"
        ),
        "binfx_recipient": MAIL_SETTINGS["binfx_email"],
        # Oncology email address for email alerts
        "oncology_ops_email": "m.neat@nhs.net",
        "wes_samplename_emaillist": [
            "gst-tr.ViapathGeneticsAdmin@nhs.net",
            "lu.liu@viapath.co.uk",
            "Suzanne.lillis@viapath.co.uk",
            "eblab@gstt.nhs.uk",
            MAIL_SETTINGS["binfx_email"],
        ],
    }

# ================ UPLOAD AND SETOFF WORKFLOWS ================================
# Settings unique to the upload and setoff workflows script

REF_SAMPLE_IDS = [
    "NA12878",
    "136819",
]  # NA12878 identifiers to exclude from congenica upload

# ---- Commands and strings ---------------------------------------------------
UPLOAD_AGENT_TEST_CMD = " --version"
# Tests dx toolkit
DX_SDK_TEST = f"source {SCRIPTS['sdk_source']}; dx --version"
BACKUP_RUNFOLDER_SUCCESS = "backup_runfolder INFO - END"
BACKUP_RUNFOLDER_ERROR = "backup_runfolder.UAcaller ERROR"
DX_SDK_TEST_EXPECTED_STDOUT = "dx v0.347.0"  # Expected result from testing
UPLOAD_AGENT_EXPECTED_STDOUT = "Upload Agent Version:"  # Upload agent test response

STRINGS = {
    "cd_success": "picard.illumina.CollectIlluminaLaneMetrics done",
    "cd_err": "Exception",
}

DEMULTIPLEXLOG_TSO500MSG = "TSO500 run. Does not need demultiplexing locally"
DEMULTIPLEX_SUCCESS = "Processing completed with 0 errors and 0 warnings."
DEMULTIPLEX_SUCCESS_REGEX = rf".*{DEMULTIPLEX_SUCCESS}$"

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
CHECKSUM_COMPLETE_MSG = "Checksum result reported"  # Checksum complete statement
CHECKSUM_MATCH_MSG = "Checksums match"  # Statement to write when checksums match

WES_SENTIEON_BAM_OUTPUT_NAME = "mappings_bam"
WES_SENTIEON_BAI_OUTPUT_NAME = "mappings_bam_bai"
WES_SENTIEON_VCF_OUTPUT_NAME = "variants_vcf"
PIPE_VCF_OUTPUT_NAME = "filtered_vcf"
PIPE_BAM_OUTPUT_NAME = "bam"

#  ================  DNAnexus  ================================================

# General
DNANEXUS_PROJECT_PREFIX = "002_"  # Project to upload run folder into
PROJECT_SUCCESS = 'Created new project called "%s"'  # Success statement
PROD_ORGANISATION = "org-viapath_prod"  # Prod org for billing

if TESTING:
    DNANEXUS_USERS = {  # User access level
        "viewers": [],
        "admins": [PROD_ORGANISATION],
    }
else:
    DNANEXUS_USERS = {  # User access level
        "viewers": [PROD_ORGANISATION, "InterpretationRequest"],
        "admins": ["mokaguys"],
    }

# Paths / IDs for apps in 001_Tools
TOOLS_PROJECT = "project-ByfFPz00jy1fk6PjpZ95F27J"  # 001_ToolsReferenceData
BEDFILE_FOLDER = f"{TOOLS_PROJECT}:/Data/BED/"

NEXUS_IDS = {
    "FILES": {
        "tso500_docker": f"{TOOLS_PROJECT}:file-Fz9Zyx00b5j8xKVkKv4fZ6JB",
        "hs37d5_bwa_index": f"{TOOLS_PROJECT}:file-B6ZY4942J35xX095VZyQBk0v",
        "hs37d5_ref_with_index": (f"{TOOLS_PROJECT}:file-ByYgX700b80gf4ZY1GxvF3Jv"),
        "hs37d5_ref_no_index": (f"{TOOLS_PROJECT}:file-B6ZY7VG2J35Vfvpkj8y0KZ01"),
        "masked_reference": f"{TOOLS_PROJECT}:file-GF84GF00QfBfzV35Gf8Qg53q",
    },
    "APPS": {
        "TSO500": f"{TOOLS_PROJECT}:applet-GPgkz0j0jy1Yf4XxkXjVgKfv",
        "congenica_app": f"{TOOLS_PROJECT}:applet-G8QGBK80jy1zJK6g9yVP7P8V",
        "congenica_sftp": f"{TOOLS_PROJECT}:applet-GFfJpj80jy1x1Bz1P1Bk3vQf",
        "upload_multiqc": f"{TOOLS_PROJECT}:applet-G2XY8QQ0p7kzvPZBJGFygP6f",
        "multiqc": f"{TOOLS_PROJECT}:applet-GPgbyk00jy1kpgvggbp12Vfg",
        "sompy": f"{TOOLS_PROJECT}:applet-G9yPb780jy1p660k6yBvQg07",
        "sambamba": f"{TOOLS_PROJECT}:applet-G6vyyf00jy1kPkX9PJ1YkxB1",
        "fastqc": f"{TOOLS_PROJECT}:applet-GKXqZV80jy1QxF4yKYB4Y3Kz",
        "gatk": f"{TOOLS_PROJECT}:applet-FYZ097j0jy1ZZPx30GykP63J",
        "peddy": f"{TOOLS_PROJECT}:applet-Fjvfk280jy1fVg8Q3b1bF6Y1",
        "rpkm": f"{TOOLS_PROJECT}:applet-FxJj0F00jy1ZVXp36PBz2p1j",
        "duty_csv": f"{TOOLS_PROJECT}:applet-GQG5kvQ0jy1YxB6Bq4KggVq5",
    },
    "WORKFLOWS": {
        "pipe": f"{TOOLS_PROJECT}:workflow-GPq04280jy1k1yVkQP0fXqBg",
        "wes": f"{TOOLS_PROJECT}:workflow-FjjbQ5Q0jy1ZgyjQ3g1zgx9k",
        "amp": f"{TOOLS_PROJECT}:workflow-G6F70180jy1gGK38FYXk618g",
        "snp": f"{TOOLS_PROJECT}:workflow-GB3kyJj0jy1j06704fxX9J7j",
    },
    "STAGES": {
        "pipe": {
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
        "wes": {
            "fastqc1": "stage-Ff0P5Jj0GYKY717pKX3vX8Z3",
            "fastqc2": "stage-Ff0P5V00GYKyJfpX5bqX69Yg",
            "picard": "stage-Ff0P5pQ0GYKVBB0g1FG27BV8",
            "sambamba": "stage-Ff0P82Q0GYKQ4j8b4gXzjqxX",
            "sentieon": "stage-Ff0P73j0GYKX41VkF3j62F9j",
        },
        "snp": {
            "fastqc1": "stage-FgPp4V00YkVJVjKF4kYkBF8v",
            "fastqc2": "stage-FgPp4V00YkVJVjKF4kYkBF90",
            "sentieon": "stage-FgPp4XQ0YkV48jZG4Py6F55k",
        },
        "amp": {
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
    "sambamba": {
        "bam": " -ibamfile=",
        "bai": " -ibam_index=",
        "coverage_level": " -icoverage_level=",
        "sambamba_bed": " -isambamba_bed=",
        "cov_cmds": (
            " -icoverage_commands='-imerge_overlapping_mate_reads=true "
            "-iexclude_failed_quality_control=true "
            "-iexclude_duplicate_reads=true "
            "-imin_base_qual=%s -imin_mapping_qual=%s'"
        ),
    },
    "peddy": {
        "project_name": " -iproject_for_peddy=",
    },
    "sompy": {
        "truth_vcf": (
            " -itruthVCF=project-ByfFPz00jy1fk6PjpZ95F27J:"
            "file-G7g9Pfj0jy1f87k1J1qqX83X"
        ),
        "query_vcf": " -iqueryVCF=",
        "tso": " -iTSO=true",
        "skip": " -iskip=false",
    },
    "rpkm": {
        "bed": " -ibedfile=",
        "proj": " -iproject_name=",
        "pannos": " -ibamfile_pannumbers=",
    },
    "multiqc": {
        "project_name": " -iproject_for_multiqc=",
        "coverage_level": " -icoverage_level=",
    },
    "upload_multiqc": {
        "data_input": " -imultiqc_data_input=",
        "multiqc_html": " -imultiqc_html=$jobid:multiqc_report",
    },
    "congenica_upload": {
        "vcf": " -ivcf=",
        "bam": " -ibam=",
        "samplename": " -ianalysis_name=",
    },
    "duty_csv": {
        "project_name": " -iproject_name=",
        "tso_pannumbers": "-itso_pannumbers=",
        "stg_pannumbers": "-istg_pannumbers=",
        "cp_capture_pannos": "-icp_capture_pannos=",
    },
}

UPLOAD_ARGS = {
    "dest": " --dest=",
    "proj": " --project=",
    "token": " --brief --auth-token %s)",
    "depends": " $depends_list",
    "depends_gatk": " $depends_list_gatk",
    # Arguments to capture jobids
    "depends_list": 'depends_list="${depends_list} -d ${jobid} "',
    "depends_list_gatk": ('depends_list_gatk="${depends_list_gatk} -d ${jobid} "'),
    "depends_list_recombined": ('depends_list="${depends_list} ${depends_list_gatk} "'),
    # Argument to define depends_list only if the job ID exists
    "if_jobid_exists_depends": 'if ! [ -z "${jobid}" ]; then %s; fi',
    # Command to restart upload agent part 1
    "restart_ua_1": "ua_status=1; while [ $ua_status -ne 0 ]; do ",
    "restart_ua_2": (
        "; ua_status=$?; if [[ $ua_status -ne 0 ]]; then echo "
        '"temporary issue when uploading file"; fi ; done'
    ),
}

# Set 6 hour timeout policy for gatk app and jobtimeoutexceeded
# reason to auto restart list
# TODO move this to the DXAPP.JSON file for FH app
PIPE_FH_GATK_TIMEOUT_ARGS = (
    ' --extra-args \'{"timeoutPolicyByExecutable": {"'
    f'{NEXUS_IDS["APPS"]["gatk"].split(":")[1]}'
    '": {"*":{"hours": 12}}}, "executionPolicy": {"restartOn": '
    '{"JobTimeoutExceeded":1, "JMInternalError":'
    ' 1, "UnresponsiveWorker": 2, "ExecutionError":1}}}\''
)

STAGE_INPUTS = {
    "pipe": {
        "fastqc_reads": (f" -i{NEXUS_IDS['STAGES']['pipe']['fastqc']}.reads="),
        "bwa_reads1": (f" -i{NEXUS_IDS['STAGES']['pipe']['bwa']}.reads_fastqgz="),
        "bwa_reads2": (f" -i{NEXUS_IDS['STAGES']['pipe']['bwa']}.reads2_fastqgz="),
        "bwa_rg_sample": (
            f" -i{NEXUS_IDS['STAGES']['pipe']['bwa']}.read_group_sample="
        ),
        "bwa_ref": (f" -i{NEXUS_IDS['STAGES']['pipe']['bwa']}.genomeindex_targz="),
        # HSMetrics Bedfile
        "picard_bed": (
            f" -i{NEXUS_IDS['STAGES']['pipe']['picard']}" f".vendor_exome_bedfile="
        ),
        "picard_capturetype": (
            f" -i{NEXUS_IDS['STAGES']['pipe']['picard']}.Capture_panel="
        ),
        "gatk_padding": (f" -i{NEXUS_IDS['STAGES']['pipe']['gatk']}.padding="),
        "gatk_vcf_format": (
            f" -i{NEXUS_IDS['STAGES']['pipe']['gatk']}.output_format=both"
        ),
        "filter_vcf_bed": (f" -i{NEXUS_IDS['STAGES']['pipe']['filter_vcf']}.bedfile="),
        "happy_skip": (f" -i{NEXUS_IDS['STAGES']['pipe']['happy']}.skip="),
        "happy_prefix": (f" -i{NEXUS_IDS['STAGES']['pipe']['happy']}.prefix="),
        "sambamba_bed": (f" -i{NEXUS_IDS['STAGES']['pipe']['sambamba']}.sambamba_bed="),
        "sambamba_min_base_qual": (
            f" -i{NEXUS_IDS['STAGES']['pipe']['sambamba']}" f".min_base_qual="
        ),
        "sambamba_min_mapping_qual": (
            f" -i{NEXUS_IDS['STAGES']['pipe']['sambamba']}" f".min_mapping_qual="
        ),
        "sambamba_cov_level": (
            f" -i{NEXUS_IDS['STAGES']['pipe']['sambamba']}" f".coverage_level="
        ),
        "sambamba_filter_cmds": (
            f" -i{NEXUS_IDS['STAGES']['pipe']['sambamba']}"
            ".additional_filter_commands="
            "'not (unmapped or secondary_alignment)'"
        ),
        "sambamba_excl_dups": (
            f" -i{NEXUS_IDS['STAGES']['pipe']['sambamba']}"
            ".exclude_duplicate_reads=true"
        ),
        "sambamba_excl_failed_qual": (
            f" -i{NEXUS_IDS['STAGES']['pipe']['sambamba']}"
            ".exclude_failed_quality_control=true"
        ),
        "sambamba_count_overl_mates": (
            f" -i{NEXUS_IDS['STAGES']['pipe']['sambamba']}"
            ".merge_overlapping_mate_reads=true"
        ),
        "fhprs_skip": (f" -i{NEXUS_IDS['STAGES']['pipe']['fhprs']}.skip=false"),
        "fhprs_bed": (f" -i{NEXUS_IDS['STAGES']['pipe']['fhprs']}.BEDfile="),
        "fhprs_instance": "mem3_ssd1_v2_x8",  # Required when creating gVCFs
        "polyedge_gene": (f" -i{NEXUS_IDS['STAGES']['pipe']['polyedge']}.gene="),
        "polyedge_chrom": (f" -i{NEXUS_IDS['STAGES']['pipe']['polyedge']}.chrom="),
        "polyedge_poly_start": (
            f" -i{NEXUS_IDS['STAGES']['pipe']['polyedge']}.poly_start="
        ),
        "polyedge_poly_end": (
            f" -i{NEXUS_IDS['STAGES']['pipe']['polyedge']}.poly_end="
        ),
        "polyedge_skip": (f" -i{NEXUS_IDS['STAGES']['pipe']['polyedge']}.skip=false"),
    },
    "wes": {
        "fastqc1_reads": (f" -i{NEXUS_IDS['STAGES']['wes']['fastqc1']}.reads="),
        "fastqc2_reads": (f" -i{NEXUS_IDS['STAGES']['wes']['fastqc2']}.reads="),
        # HSmetrics bedfile
        "picard_bed": (
            f" -i{NEXUS_IDS['STAGES']['wes']['picard']}" f".vendor_exome_bedfile="
        ),
        "sambamba_bed": (f" -i{NEXUS_IDS['STAGES']['wes']['sambamba']}.sambamba_bed="),
        # Prevents incorrect parsing from fastq filename
        "sentieon_samplename": (f" -i{NEXUS_IDS['STAGES']['wes']['sentieon']}.sample="),
        "sentieon_bed": (f" -i{NEXUS_IDS['STAGES']['wes']['sentieon']}.targets_bed="),
    },
    "snp": {
        "fastqc1_reads": (f" -i{NEXUS_IDS['STAGES']['snp']['fastqc1']}.reads="),
        "fastqc2_reads": (f" -i{NEXUS_IDS['STAGES']['snp']['fastqc2']}.reads="),
        "sentieon_bed": (f" -i{NEXUS_IDS['STAGES']['snp']['sentieon']}.targets_bed="),
        # Prevents incorrect parsing from fastq filename
        "sentieon_samplename": (f" -i{NEXUS_IDS['STAGES']['snp']['sentieon']}.sample="),
    },
    "amp": {
        "fastqc1_reads": (f" -i{NEXUS_IDS['STAGES']['amp']['fastqc1']}.reads_fastqgz="),
        "fastqc2_reads": (
            f" -i{NEXUS_IDS['STAGES']['amp']['fastqc1']}.reads2_fastqgz="
        ),
        "bwa_rg_sample": (f" -i{NEXUS_IDS['STAGES']['amp']['bwa']}.read_group_sample="),
        "bwa_ref": (
            f" -i{NEXUS_IDS['STAGES']['amp']['bwa']}"
            f".genomeindex_targz={NEXUS_IDS['FILES']['hs37d5_bwa_index']}"
        ),
        "picard_bed": (
            f" -i{NEXUS_IDS['STAGES']['amp']['picard']}" f".vendor_exome_bedfile="
        ),
        "picard_capturetype": (
            f" -i{NEXUS_IDS['STAGES']['amp']['picard']}.Capture_panel="
        ),
        "picard_ref": (
            f" -i{NEXUS_IDS['STAGES']['amp']['picard']}."
            f"fasta_index={NEXUS_IDS['FILES']['hs37d5_ref_with_index']}"
        ),
        "ampliconfilt_bed": (
            f" -i{NEXUS_IDS['STAGES']['amp']['ampliconfilt']}.PE_BED="
        ),
        "sambamba_cov_level": (
            f" -i{NEXUS_IDS['STAGES']['amp']['sambamba']}.coverage_level="
        ),
        "sambamba_bed": (f" -i{NEXUS_IDS['STAGES']['amp']['sambamba']}.sambamba_bed="),
        "vardict_ref": (
            f" -i{NEXUS_IDS['STAGES']['amp']['vardict']}."
            f"ref_genome={NEXUS_IDS['FILES']['hs37d5_ref_with_index']}"
        ),
        "vardict_bed": (f" -i{NEXUS_IDS['STAGES']['amp']['vardict']}.bedfile="),
        "vardict_samplename": (
            f" -i{NEXUS_IDS['STAGES']['amp']['vardict']}" f".sample_name=vardict_"
        ),
        "varscan_ref": (
            f" -i{NEXUS_IDS['STAGES']['amp']['varscan']}."
            f"ref_genome={NEXUS_IDS['FILES']['hs37d5_ref_with_index']}"
        ),
        "varscan_bed": (f" -i{NEXUS_IDS['STAGES']['amp']['varscan']}.bed_file="),
        "varscan_samplename": (
            f" -i{NEXUS_IDS['STAGES']['amp']['varscan']}" f".samplename=varscan_"
        ),
        "varscan_strandfilter": (
            f" -i{NEXUS_IDS['STAGES']['amp']['varscan']}.strand_filter="
        ),
        "mpileup_covlevel": (
            f" -i{NEXUS_IDS['STAGES']['amp']['mpileup']}.min_coverage="
        ),
    },
}

# Command strings
EMPTY_DEPENDS = "depends_list=''\n"
EMPTY_GATK_DEPENDS = "depends_list_gatk=''\n"

DX_RUN_CMDS = {
    "create_proj": str(
        'project_id="$(dx new project --bill-to %s "%s" --brief ' '--auth-token %s)"\n'
    ),
    "pipe": str(
        f"jobid=$(dx run {NEXUS_IDS['WORKFLOWS']['pipe']}"
        f" --priority high -y {JOB_NAME_STR}"
    ),
    "wes": str(
        f"jobid=$(dx run {NEXUS_IDS['WORKFLOWS']['wes']}"
        f" --priority high -y {JOB_NAME_STR}"
    ),
    "snp": str(
        f"jobid=$(dx run {NEXUS_IDS['WORKFLOWS']['snp']}"
        f" -y --priority high {JOB_NAME_STR}"
    ),
    "amp": str(
        f"jobid=$(dx run {NEXUS_IDS['WORKFLOWS']['amp']}"
        f" --priority high -y {JOB_NAME_STR}"
    ),
    "tso500": (
        f"jobid=$(dx run {NEXUS_IDS['APPS']['TSO500']}"
        f" --priority high -y {JOB_NAME_STR}"
    ),
    "fastqc": (
        f"jobid=$(dx run {NEXUS_IDS['APPS']['fastqc']} "
        f"--priority high -y {JOB_NAME_STR}"
    ),
    "peddy": (
        f"jobid=$(dx run {NEXUS_IDS['APPS']['peddy']} "
        f"--priority high -y --instance-type mem1_ssd1_v2_x2 {JOB_NAME_STR}"
    ),
    "multiqc": (
        f"jobid=$(dx run {NEXUS_IDS['APPS']['multiqc']} "
        f"--priority high -y --instance-type mem1_ssd1_v2_x4 {JOB_NAME_STR}"
    ),
    "upload_multiqc": (
        f"jobid=$(dx run {NEXUS_IDS['APPS']['upload_multiqc']} "
        f"--priority high -y --instance-type mem1_ssd1_v2_x2 {JOB_NAME_STR}"
    ),
    "rpkm": (
        f"jobid=$(dx run {NEXUS_IDS['APPS']['rpkm']}"
        f" --priority high -y --instance-type mem1_ssd1_v2_x8 {JOB_NAME_STR}"
    ),
    "decision_support_prep": (
        f"analysisid=$(python {SCRIPTS['dsptool_input_script']} -a"
    ),
    "congenica_sftp": (
        f"echo 'dx run {NEXUS_IDS['APPS']['congenica_sftp']} "
        f"--priority high -y ' $analysisid ' {JOB_NAME_STR}"
    ),
    "congenica_app": (
        f"echo 'dx run {NEXUS_IDS['APPS']['congenica_app']} "
        "--priority high -y --instance-type mem1_ssd1_v2_x2 ' $analysisid ' "
        f"{JOB_NAME_STR}"
    ),
    "sompy": (
        f"jobid=$(dx run {NEXUS_IDS['APPS']['sompy']} "
        f"--priority high -y {JOB_NAME_STR}"
    ),
    "sambamba": (
        f"jobid=$(dx run {NEXUS_IDS['APPS']['sambamba']} "
        f"--priority high -y {JOB_NAME_STR}"
    ),
    "duty_csv": (
        f"jobid=$(dx run {NEXUS_IDS['APPS']['duty_csv']} --priority high -y "
        f"{JOB_NAME_STR}"
    ),
}

# ---- Moka settings ----------------------------------------------------------

# Moka IDs for generating SQLs to update the Mokadatabase (audit trail)
SQL_IDS = {
    "WORKFLOWS": {
        "pipe": 5229,
        "wes": 5078,
        "amp": 4851,
        "archerdx": 5238,
        "snp": 5091,
        "tso500": 5237,
    },
    "WES_TEST_STATUS": {
        "nextseq_sequencing": 1202218804,  # Test Status = NextSEQ sequencing
        "data_processing": 1202218805,  # Test Status = Data Processing
    },
}

QUERIES = {
    "customrun": (
        "insert into NGSCustomRuns(DNAnumber,PipelineVersion, " "RunID) values (%s)"
    ),
    "wes": (
        "update NGSTest set PipelineVersion = %s, StatusID = %s where "
        "dna in ('%s') and StatusID = %s"
    ),
    "oncology": (
        "insert into "
        "NGSOncologyAudit(SampleID1,SampleID2,RunID,PipelineVersion,"
        "ngspanelid) values (%s)"
    ),
}
