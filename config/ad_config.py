"""
Automate demultiplex configuration. Contains general settings, and the following
classes collating the settings required per module:

- AdEmailConfig
- AdLoggerConfig
- DemultiplexConfig
- SWConfig
- ToolboxConfig
- URConfig
"""

import os
import sys
import datetime
from pygit2 import Repository
from pathlib import Path
from .log_msgs_config import LOG_MSGS
from .panel_config import TOOLS_PROJECT, MASKED_REFERENCE, PanelConfig


# =========== GENERAL SETTINGS USED ACROSS MODULES ====================================

REPO_NAME = "automated_scripts"
# Timestamp used for naming log files with datetime
TIMESTAMP = str(f"{datetime.datetime.now():%Y%m%d_%H%M%S}")
PROJECT_DIR = str(Path(__file__).absolute().parent.parent)  # Project working directory
# Root of folder containing apps, automate_demultiplexing_logfiles and
# development_area scripts (2 levels up from this file)
DOCUMENT_ROOT = "/".join(PROJECT_DIR.split("/")[:-2])
BRANCH = Repository(PROJECT_DIR).head.shorthand
MAIL_SETTINGS = {
    "host": "email-smtp.eu-west-2.amazonaws.com",
    "port": 587,
    "binfx_email": "gsttbioinformatics@synnovis.co.uk",
    "alerts_email": "no_reply@kingspm.uk",
}

if BRANCH == "main" and "pytest" not in sys.modules:  # Prod branch
    TESTING = False  # Set testing mode
    SCRIPT_MODE = "PROD_MODE"
    JOB_NAME_STR = "--name "
    RUNFOLDERS = "/media/data1/share"
    AVITI01_RUNFOLDER = "/media/data1/share/AV241501"
    AVITI02_RUNFOLDER = "/media/data1/share/AV250605"
    AVITI_SAMPLESHEET = "/media/data1/share/samplesheets"
    AD_LOGDIR = os.path.join(DOCUMENT_ROOT, "automate_demultiplexing_logfiles")
    MAIL_SETTINGS = MAIL_SETTINGS | {  # Add prod mail recipients
        "pipeline_started_subj": f"{SCRIPT_MODE}. ALERT: Started pipeline for %s",
        "binfx_recipient": MAIL_SETTINGS["binfx_email"],
        # Oncology email address for email alerts
        "oncology_ops_email": "synnovis.seglh-ods@nhs.net",
        "wes_samplename_emaillist": [
            "gst-tr.ViapathGeneticsAdmin@nhs.net",
            "lu.liu@viapath.co.uk",
            "Suzanne.lillis@viapath.co.uk",
            "eblab@gstt.nhs.uk",
            MAIL_SETTINGS["binfx_email"],
        ],
    }
else:  # Testing branch
    TESTING = True
    SCRIPT_MODE = "TEST_MODE"
    # JOB_NAME_STR must be @-separated to be picked up by the gmail filter which
    # determines which slack channel to send the alert to
    JOB_NAME_STR = "--name TEST_MODE@"
    RUNFOLDERS = "/media/data1/share/testing"
    AVITI01_RUNFOLDER = "/media/data1/share/testing/AV241501"
    AVITI02_RUNFOLDER = "/media/data1/share/testing/AV250605"
    AVITI_SAMPLESHEET = "/media/data1/share/AV241501/testing/samplesheets"
    AD_LOGDIR = os.path.join(RUNFOLDERS, "automate_demultiplexing_logfiles")
    MAIL_SETTINGS = MAIL_SETTINGS | {  # Add test mail recipients
        "pipeline_started_subj": f"{SCRIPT_MODE}. ALERT: Started pipeline for %s",
        "binfx_recipient": MAIL_SETTINGS["binfx_email"],
        # Oncology email address for email alerts
        "oncology_ops_email": MAIL_SETTINGS["binfx_email"],
        "wes_samplename_emaillist": MAIL_SETTINGS["binfx_email"],
    }

CREDENTIALS = {
    "email_user": os.path.join(DOCUMENT_ROOT, ".amazon_email_username"),
    "email_pw": os.path.join(DOCUMENT_ROOT, ".amazon_email_pw"),
    "dnanexus_authtoken": os.path.join(DOCUMENT_ROOT, ".dnanexus_auth_token"),
    "adx_authtoken": ".archer_authentication_mokaguys.txt",
    "aws_s3_profile": os.path.join(DOCUMENT_ROOT, ".aws_s3_profile"), # AWS CLI profile name for S3 uploads
}
NOVASEQ_ID = "A01229"  # Novaseq sequencer ID
AVITI01_ID = "AV241501" # Aviti sequencer ID
AVITI02_ID = "AV250605" # Second Aviti Sequencer ID
AVITI_IDS = ["AV241501","AV250605"]
# TO DO write if loop for fastq file locations based on sequencer
RUNFOLDER_PATTERN = "^[0-9]{6}.*$"  # Runfolders start with 6 digits
FASTQ_DIRS = {
    "illumina_fastqs": "Data/Intensities/BaseCalls",  # Path to fastq files
    "tso_fastqs": "${PROJECT_ID}:/analysis_folder/Logs_Intermediates/CollapsedReads/",
    "aviti_fastqs": "Fastq/Samples", # Path to AVITI fastq files
}
SDK_SOURCE = f"source {DOCUMENT_ROOT}/apps/dx-toolkit/environment"  # dxtoolkit path

# DNAnexus upload agent path
UPLOAD_AGENT_EXE = f"{DOCUMENT_ROOT}/apps/dnanexus-upload-agent-1.5.17-linux/ua"
BCLCONVERT_DOCKER = "seglh/bcl-convert:4.3.6"
BASES2FASTQ_DOCKER = "seglh/bases2fastq:2.3.0"
GATK_DOCKER = (
    "broadinstitute/gatk:4.1.8.1"  # TODO this image should have a hash added in future
)
ARCHER_DOCKER = (
    "seglh/archer_api_upload_py:6ff3ff0"
)

LANE_METRICS_SUFFIX = ".illumina_lane_metrics"
DEMUX_NOT_REQUIRED_MSG = "%s run. Does not need demultiplexing locally"
ILLUMINA_DEMULTIPLEX_SUCCESS = "thread 1 Conversion Complete."
AVITI_DEMULTIPLEX_SUCCESS = "Output stored in /output"

# -------------- S3-SPECIFIC ------------------------------------------------------------------

# For S3 uploads
S3_PIPELINES = ["msk", "archerdx"]
# S3 buckets
S3_BUCKETS = {
    "msk": "msk-access-archive",
    "archerdx": "archer-ngs-archive",
}
# AWS CLI upload commands for S3:
#   %s = local path, %s = s3 destination URI, %s = AWS CLI profile name
# Per-file copy (used for individual files e.g. logfiles)
S3_CP_CMD = "aws s3 cp %s %s --profile %s --storage-class DEEP_ARCHIVE"
# Directory sync (used for whole-runfolder uploads)
S3_SYNC_CMD = "aws s3 sync %s %s --profile %s --storage-class DEEP_ARCHIVE"

# -------------- DNANEXUS-SPECIFIC --------------------------------------------------------------

NEXUS_IDS = {
    # Paths / IDs for data items in 001_Tools
    "FILES": {
        "hs37d5_bwa_index": f"{TOOLS_PROJECT}:file-J34V9gXKJqkj5P31fYkJvFG3",  # hs37d5.bwa-index.tar.gz
        "hs37d5_ref_with_index": f"{TOOLS_PROJECT}:file-J341GzpK9yGY6B1XzGP8yKGV",  # hs37d5.fasta-index.tar.gz
        "hs37d5_ref_no_index": f"{TOOLS_PROJECT}:file-J341J2XK9yGXx01zgP9FYy8x",  # hs37d5.fa.gz
        "masked_reference": MASKED_REFERENCE,  # hs37d5_Pan4967.bwa-index.tar.gz
        "ed_vcp1_readcount_normals_NOVASEQ": f"{TOOLS_PROJECT}:file-J340xFpK9yGzpJ0Yj8ZfGY54",  # Pan5208_normals_v1.0.0.RData
        #"ed_CP2_readcount_normals_NOVASEQ": f"{TOOLS_PROJECT}:file-J44y28pK9yGq9b9y2K42KjYz",  # Pan5279_normals_v1.1.0.RData #no cp205 PON for novaseq
        "ed_CP2_readcount_normals_AVITI": f"{TOOLS_PROJECT}:file-J7vv0ZXK9yGxvFF3XxVK2yJ7", # Pan5356_AVITI_normals_v1.0.0.RData

        "sompy_truth_vcf": f"{TOOLS_PROJECT}:file-J34YbB2K9yGp9Z29gg26Z1pj",  # HD200_expectedsorted.vcf
    },
    "APPS": {
        "congenica_upload": f"{TOOLS_PROJECT}:applet-J3Px8vpK9yGVF55Fy3kvFb0f",  # congenica_upload_v1.3.3
        "oncodeep_upload": f"{TOOLS_PROJECT}:applet-J3PxV8BK9yGzPK2vV9921Jpx",  # oncodeep_upload v1.0.1
        "multiqc": f"{TOOLS_PROJECT}:applet-J84gV4XK9yGzqYfqQ0Yj7f05",  # multiqc_v1.18.2
        "sambamba_vcp1": f"{TOOLS_PROJECT}:applet-J3XPXyBK9yGpfyjPb2KYg82g",  # chanjo_sambamba_coverage_v1.13.1
        "sambamba_cp2": f"{TOOLS_PROJECT}:applet-J3XKp62K9yGpjP2yvP93Z68K",  # sambamba_coverage_v2.0.1
        "fastqc": f"{TOOLS_PROJECT}:applet-J3PxBkXK9yGZ071FgGb11QKk",  # fastqc_v1.4.1
        "gatk": f"{TOOLS_PROJECT}:applet-J3PxJx2K9yGZZ2j2BKV86Jgj",  # gatk3_human_exome_pipeline_v1.5.1
        "sentieon": f"{TOOLS_PROJECT}:app-Gy4j5z00PPyQ5qv5FBXy0ZZp",  # Sentieon germline FASTQ to VCF v5.1.0
        #"peddy": f"{TOOLS_PROJECT}:applet-Fjvfk280jy1fVg8Q3b1bF6Y1",  # peddy_v1.5
        "ed_readcount": f"{TOOLS_PROJECT}:applet-J7BQy2XK9yGfZ4GYfYZJgfX5",  # ED_readcount_analysis_v1.6.1
        "ed_cnvcalling": f"{TOOLS_PROJECT}:applet-J7BQyvXK9yGfqpgq4BYpXvPx",  # ED_cnv_calling_v1.7.1
        "rpkm": f"{TOOLS_PROJECT}:applet-J84zJ4BK9yGfPf1BVjg2bfVf",  # RPKM_using_conifer_v1.6.2
        "duty_csv": f"{TOOLS_PROJECT}:applet-J84xJZXK9yGfXVZyyzZBYFBG",  # duty_csv_v1.5.3
    },
    "WORKFLOWS": {
        "gatk_pipe": f"{TOOLS_PROJECT}:workflow-J3XPgzXK9yGbgg33xp68kXGx",  # GATK3.5_v2.20
        "seglh_pipe": f"{TOOLS_PROJECT}:workflow-J3Pyjk2K9yGzPqKz0XGzqq6Z",  # SEGLH_RD_v1.5
    
    },
    "STAGES": {
        "gatk_pipe": {
            "filter_vcf": "stage-J3XPv9XK9yGfg29yQQ8kkg5P",
            "gatk": "stage-J3XPpypK9yGX7Yq8f6z9v522",
            "fastqc": "stage-J3XPjQ2K9yGYGVf6x2zjPgP6",
            "bwa": "stage-J3XPjkBK9yGVQYBf32jkV12K",
            "picard": "stage-J3XPp62K9yGX7Yq8f6z9v50y",
            "happy": "stage-J3XPx1XK9yGp8BZf0v3fB26F",
            "sambamba": "stage-J3XPy6BK9yGfB6J3BB5xpG1B",
            "fhprs": "stage-J3XPvfpK9yGy87ZYP3kzFfqq",
            "polyedge": "stage-J3XQ032K9yGQ2x8Fpf34002p",
        },
        "seglh_pipe": {
            "filter_vcf": "stage-J3Pyp9pK9yGfzFQ7yvzfv933",
            "sentieon": "stage-J3Pykz2K9yGjy5YGf70QYqyF",
            "fastqc": "stage-J3Pyk6pK9yGQq4B1XFQJZY8v",
            "picard": "stage-J3PypzBK9yGX7Yq8f6z8yg5f",
            "happy": "stage-J3PyxGXK9yGYX5F20BGfkZPY",
            "sambamba": "stage-J3ZQjvBK9yGbyyxKYfj0yX2j",
            "fhprs": "stage-J3Pyv7pK9yGYQ354qBB6Z62G",
            "bcftools_stats": "stage-J3PyqfpK9yGx93XxkB02j5g9",
            "verifybam": "stage-J3Pyy4pK9yGYfyqJ19g3fXyf",
            "polyedge": "stage-J3PyvyXK9yGQ5BjX7jbYPbkg",          
        },
    },
}
NEXUS_IDS["WORKFLOWS"]["archerdx"] = NEXUS_IDS["APPS"]["fastqc"]
NEXUS_IDS["WORKFLOWS"]["oncodeep"] = NEXUS_IDS["APPS"]["fastqc"]


APP_INPUTS = {  # Inputs for apps run outside of DNAnexus workflows

    "sambamba": {  # Used for TSO samples only as standalone app
        "bam": "-ibamfile=${PROJECT_ID}:/analysis_folder/Logs_Intermediates/StitchedRealigned/",
        "bai": "-ibam_index=${PROJECT_ID}:/analysis_folder/Logs_Intermediates/StitchedRealigned/",
        "coverage_level": "-icoverage_level=",
        "sambamba_bed": "-isambamba_bed=",
        "cov_cmds": (
            "-imerge_overlapping_mate_reads=true -iexclude_failed_quality_control=true "
            "-iexclude_duplicate_reads=true -imin_base_qual=%s -imin_mapping_qual=%s"
        ),
    },
    "fastqc": {
        "reads": "-ireads=",
    },
    "peddy": {"project_name": "-iproject_for_peddy=${PROJECT_NAME}"},
    "sompy": {
        "truth_vcf": f"-itruthVCF={NEXUS_IDS['FILES']['sompy_truth_vcf']}",
        "query_vcf": "-iqueryVCF=${PROJECT_ID}:/analysis_folder/Results/",
        "tso": "-iTSO=true",
        "skip": "-iskip=false",
    },
    "ed_readcount": {
        "ref_genome": "-ireference_genome=",
        "bed": "-ibedfile=",
        "normals_rdata": "-inormals_RData=",
        "proj": "-iproject_name=${PROJECT_NAME}",
        "bam_str": "-ibam_str=",
        "excluded_samples": "-iexcluded_samples=",
        "pannos": "-ibamfile_pannumbers=",
    },
    "ed_cnvcalling": {
        "readcount": "-ireadcount_file=${ED_READCOUNT_JOB_ID}:RData",
        "bed": "-isubpanel_bed=",
        "proj": "-iproject_name=${PROJECT_NAME}",
        "bam_str": "-ibam_str=",
        "samplename_str": "-isamplename_str=",
        "ref_genome": "-ireference_genome=",
        "pannos": "-ibamfile_pannumbers=",
    },
    "rpkm": {
        "bed": "-ibedfile=",
        "proj": "-iproject_name=${PROJECT_NAME}",
        "pannos": "-ibamfile_pannumbers=",
    },
    "multiqc": {
        "project_name": "-iproject_for_multiqc=${PROJECT_NAME}",
        "coverage_level": "-icoverage_level=",
    },
    "upload_multiqc": {
        "lane_metrics": (
            "-imultiqc_data_input=${PROJECT_ID}:/QC/${RUNFOLDER_NAME}"
            f"{LANE_METRICS_SUFFIX}"
        ),
        "multiqc_output": "-imultiqc_data_input=${JOB_ID}:multiqc",
        "multiqc_html": "-imultiqc_html=${JOB_ID}:multiqc_report",
    },
    "congenica_upload": {
        "samplename": "-ianalysis_name=",
        "congenica_project": "-icongenica_project=",
        "credentials": "-icredentials=",
        "ir_template": "-iIR_template=",
        "vcf": "-ivcf=${PROJECT_ID}:/output/",
        "bam": "-ibam=${PROJECT_ID}:/output/",
    },
    "qiagen_upload": {
        "sample_name": "-isample_name=",
        "sample_zip_folder": "-isample_zip_folder=${PROJECT_ID}:/results/",
    },
    "oncodeep_upload": {
        "run_identifier": "-irun_identifier=",
        "file_to_upload": "-ifile_to_upload=",
        "account_type": "-iaccount_type=Production",
    },
    "duty_csv": {
        "project_name": "-iproject_name=${PROJECT_NAME}",
        "tso_pannumbers": "-itso_pannumbers=",
        "stg_pannumbers": "-istg_pannumbers=",
        "cp_capture_pannos": "-icp_capture_pannos=",
    },
}
UPLOAD_ARGS = {
    "dest": "--dest=${PROJECT_ID}",
    "proj": "--project=${PROJECT_NAME}",
    "token": "--brief --auth ${AUTH})",
    "depends": "${DEPENDS_LIST}",
    "depends_pipeline": "${DEPENDS_LIST_PIPELINE}",
    # Arguments to capture jobids. Job IDS are built into a string that can be passed to
    # downstream apps to ensure the jobs don't start until those job ids have completed successfully
    "depends_list": 'DEPENDS_LIST="${DEPENDS_LIST} -d ${JOB_ID} "',
    "depends_list_pipeline": 'DEPENDS_LIST_PIPELINE="${DEPENDS_LIST_PIPELINE} -d ${JOB_ID} "',
    "depends_list_pipeline_recombined": 'DEPENDS_LIST="${DEPENDS_LIST} ${DEPENDS_LIST_PIPELINE} "',
    "depends_list_edreadcount": 'DEPENDS_LIST_EDREADCOUNT="${DEPENDS_LIST_EDREADCOUNT} -d ${ED_READCOUNT_JOB_ID} "',
    "depends_list_cnvcalling": 'DEPENDS_LIST_CNVCALLING="${DEPENDS_LIST_CNVCALLING} -d ${CNVCALLING_JOB_ID} "',
    "depends_list_cnv_recombined": (
        'DEPENDS_LIST="${DEPENDS_LIST} ${DEPENDS_LIST_EDREADCOUNT} ${DEPENDS_LIST_CNVCALLING}"'
    ),
}

DX_CMDS = {
    "create_proj": 'PROJECT_ID="$(dx new project --bill-to %s "%s" --region ${DNANEXUS_REGION} --brief --auth ${AUTH})"',
    "find_proj_name": (
        f"{SDK_SOURCE}; dx find projects --name *%s* "
        "--auth %s | awk '{print $3}'"
    ),
    "proj_name_from_id": f"{SDK_SOURCE}; dx describe %s --auth %s --json | jq -r .name",
    "find_proj_id": f"{SDK_SOURCE}; dx describe %s --auth %s --json | jq -r .id",
    "find_execution_id": (
        f"{SDK_SOURCE}; dx describe %s --json --auth %s | jq -r '.stages[] | "
        'select( .id == "%s") | .execution.id\''
    ),
    "find_data": (
        f"{SDK_SOURCE}; dx find data --project=%s --tag as_upload --auth %s | "
        "grep -v 'automated_scripts_logfiles' | wc -l"
    ),
    "invite_user": "USER_INVITE_OUT=$(dx invite %s ${PROJECT_ID} %s --no-email --auth ${AUTH})",
    "file_upload_cmd": (
        f"{UPLOAD_AGENT_EXE} --auth %s --project %s --folder '%s' --do-not-compress "
        "--upload-threads 10 %s --tag as_upload"
    ),
    "gatk_pipe": f"JOB_ID=$(dx run {NEXUS_IDS['WORKFLOWS']['gatk_pipe']} --priority high -y {JOB_NAME_STR}",
    "seglh_pipe": f"JOB_ID=$(dx run {NEXUS_IDS['WORKFLOWS']['seglh_pipe']} --priority high -y {JOB_NAME_STR}",
    "fastqc": f"JOB_ID=$(dx run {NEXUS_IDS['APPS']['fastqc']} --priority high -y {JOB_NAME_STR}",
    #"peddy": (  # TODO move instance type into app itself
        #f"JOB_ID=$(dx run {NEXUS_IDS['APPS']['peddy']} --priority high "
        #f"-y --instance-type mem1_ssd1_v2_x2 {JOB_NAME_STR}"
    #),
    "multiqc": f"JOB_ID=$(dx run {NEXUS_IDS['APPS']['multiqc']} --priority high -y {JOB_NAME_STR}",
    "ed_readcount": (
        f"ED_READCOUNT_JOB_ID=$(dx run {NEXUS_IDS['APPS']['ed_readcount']} "
        f"--priority high -y --instance-type mem1_ssd1_v2_x8 {JOB_NAME_STR}"
    ),
    "ed_cnvcalling": (
        f"CNVCALLING_JOB_ID=$(dx run {NEXUS_IDS['APPS']['ed_cnvcalling']} --priority high -y {JOB_NAME_STR}"
    ),
    "rpkm": (  # TODO soon to be removed
        f"CNVCALLING_JOB_ID=$(dx run {NEXUS_IDS['APPS']['rpkm']} "
        f"--priority high -y --instance-type mem1_ssd1_v2_x8 {JOB_NAME_STR}"
    ),
    "congenica_upload": (  # TODO move instance type into app itself
        f"sleep 3; JOB_ID=$(dx run {NEXUS_IDS['APPS']['congenica_upload']} --priority high -y "
        f"--instance-type mem1_ssd1_v2_x2 {JOB_NAME_STR}"
    ),
    "oncodeep_upload": (
        f"JOB_ID=$(dx run {NEXUS_IDS['APPS']['oncodeep_upload']} --priority high -y "
        f"{JOB_NAME_STR}"
    ),
    "sambamba": f"JOB_ID=$(dx run {NEXUS_IDS['APPS']['sambamba_cp2']} --priority high -y {JOB_NAME_STR}",
    "duty_csv": f"JOB_ID=$(dx run {NEXUS_IDS['APPS']['duty_csv']} --priority high -y {JOB_NAME_STR}",
}

# =========== Classes for config import by other modules settings ========================================


class AdEmailConfig:
    """
    Ad Email configuration
    """

    CREDENTIALS = CREDENTIALS
    MAIL_SETTINGS = MAIL_SETTINGS
    PROJECT_DIR = PROJECT_DIR
    TESTING = TESTING


class AdLoggerConfig:
    """
    Ad Logger configuration
    """

    REPO_NAME = REPO_NAME
    LOG_MSGS = LOG_MSGS
    SCRIPT_MODE = SCRIPT_MODE
    TIMESTAMP = TIMESTAMP


class DemultiplexConfig(PanelConfig):
    """
    Demultiplex configuration
    """

    NOVASEQ_ID = NOVASEQ_ID
    AVITI_IDS = AVITI_IDS
    AVITI01_RUNFOLDER = AVITI01_RUNFOLDER
    AVITI02_RUNFOLDER = AVITI02_RUNFOLDER
    RUNFOLDER_PATTERN = RUNFOLDER_PATTERN
    RUNFOLDERS = RUNFOLDERS
    BASES2FASTQ_CPU = 10
    IC_SCRIPT = "/usr/local/src/mokaguys/integrity_checking/integrity_check.py"
    STRINGS = {
        "demultiplex_not_required_msg": DEMUX_NOT_REQUIRED_MSG,
        "lane_metrics_suffix": LANE_METRICS_SUFFIX,
        "cd_success": "picard.illumina.CollectIlluminaLaneMetrics done",
        "ic_success": "SUCCESS",  # Success message written to filecheck.txt by integrity check script
        "ic_assessed": "Integrity check assessed by AS: %s",  # Written to filecheck.txt by AS to prevent repeated error logging
        "samplesheet_success": "Samplesheet check successful with no errors identified: %s",
        "samplesheet_fail": "Processing halted. SampleSheet contains SampleSheet errors: %s ",
        "upload_flag_umis": "Runfolder contains UMIs. Runfolder will not be uploaded and requires manual upload: %s",
    }
    TESTING = TESTING
    BCLCONVERT_CMD = (
        f"docker run --ulimit nofile=65535:65535 --rm --user %s:%s -v %s:/data/input -v %s:/data/output "
        f"-v %s:/var/log/bcl-convert "
        f"-v %s:/samplesheet_input {BCLCONVERT_DOCKER} "
        f"--force --bcl-input-directory /data/input "
        f"--output-directory /data/output "
        f"--sample-sheet /samplesheet_input/%s "
        f"--no-lane-splitting true --fastq-gzip-compression-level 4"
    )
    BASES2FASTQ_CMD = (
        f"docker run --rm --user %s:%s -v %s:/input -v %s:/output {BASES2FASTQ_DOCKER} "
        "bases2fastq /input /output -p %s --group-fastq --no-projects -r /input/%s"
    )
    CD_CMD = (
        f"docker run --rm --user %s:%s -v %s:/input_run {GATK_DOCKER} ./gatk CollectIlluminaLaneMetrics "
        "--RUN_DIRECTORY /input_run --OUTPUT_DIRECTORY /input_run --OUTPUT_PREFIX %s"
    )
    ADX_LOG = f"{AD_LOGDIR}/archer_api_upload_logfiles/"
    ADX_CMD = (
        f"docker run "
        f"-v {RUNFOLDERS}/${{run_folder_name}}/Data/Intensities/BaseCalls:/${{run_folder_name}} "
        f"-v {DOCUMENT_ROOT}:/auth_file "
        f"-v {ADX_LOG}:/log_dir "
        f"{ARCHER_DOCKER} --runfolder /${{run_folder_name}} "
        f"--cred_file /auth_file/{CREDENTIALS['adx_authtoken']} "
        f"--log_dir /log_dir "
        f"--job_name ${{job_name}}"
    )
    MSK_CMD = (
        f"python3 /usr/local/src/mokaguys/sophia_cli/sophia.py "
        f"{RUNFOLDERS}/${{run_folder_name}} --force"
    )
    DEMULTIPLEX_TEST_RUNFOLDERS = [
        "20251104_AV250605_NGS729AV2413pM",
        "999999_NB552085_0496_DEMUXINTEG",
        "999999_M02353_0496_000000000-DEMUX",
        "999999_A01229_0182_AHM2TSO500",  # Used for testing demultiplex and sw scripts
        "999999_M02631_0285_000000000-DEVOO",
        "999999_NB551068_0285_OODEVINTEG",
        "999999_M02631_0285_000000000-DVUMI",
        "999999_NB552085_0320_ONCODEEP00",  # Included as behaviour is slightly different to include copying the MasterFile
    ]
    SEQUENCER_IDS = {
        # Requires_ic denotes sequencers requiring md5 checksums from integrity check to be assessed
        "NB551068": {"requires_ic": True},
        "NB552085": {"requires_ic": True},
        "M02353": {"requires_ic": False},
        "M02631": {"requires_ic": False},
        NOVASEQ_ID: {"requires_ic": True},
        AVITI01_ID: {"requires_ic": False},
        AVITI02_ID: {"requires_ic": False},
    }
    SEQ_REQUIRE_IC = [k for k, v in SEQUENCER_IDS.items() if v["requires_ic"]]


class SWConfig(PanelConfig):
    """
    Setoff Workflows configuration
    """

    APP_INPUTS = APP_INPUTS
    CREDENTIALS = CREDENTIALS
    DX_CMDS = DX_CMDS
    FASTQ_DIRS = FASTQ_DIRS
    MAIL_SETTINGS = MAIL_SETTINGS
    NEXUS_IDS = NEXUS_IDS
    NOVASEQ_ID = NOVASEQ_ID
    TIMESTAMP = TIMESTAMP
    PROJECT_DIR = PROJECT_DIR
    RUNFOLDER_PATTERN = RUNFOLDER_PATTERN
    SDK_SOURCE = SDK_SOURCE
    UPLOAD_ARGS = UPLOAD_ARGS
    RUNFOLDERS = RUNFOLDERS
    AVITI01_RUNFOLDER = AVITI01_RUNFOLDER
    AVITI02_RUNFOLDER = AVITI02_RUNFOLDER
    AVITI_IDS = AVITI_IDS
    PROD_ORGANISATION = "org-viapath_prod"  # Prod org for billing
    DNANEXUS_REGION = "aws:eu-west-2-g" # London AWS region code
    if BRANCH == "main":  # Prod branch

        BSPS_ID = "BSPS_MD"
        DNANEXUS_USERS = {  # User access level
            # TODO remove InterpretationRequest user once per-user accounts set up
            "viewers": [PROD_ORGANISATION, "InterpretationRequest", "org-seglh_read"],
            "admins": ["mokaguys"],
        }
        TSO_BATCH_SIZE = 16
    else:
        BSPS_ID = ""
        DNANEXUS_USERS = {  # User access level
            "viewers": [],
            "admins": [PROD_ORGANISATION],
        }
        TSO_BATCH_SIZE = 2
    S3_PIPELINES = S3_PIPELINES
    S3_BUCKETS = S3_BUCKETS
    S3_CP_CMD = S3_CP_CMD
    S3_SYNC_CMD = S3_SYNC_CMD
    RUNFOLDER_NAME = "${RUNFOLDER_NAME}"
    EMPTY_DEPENDS = "DEPENDS_LIST=''"
    EMPTY_CP_DEPENDS = [
        "DEPENDS_LIST_PIPELINE=''",
        "DEPENDS_LIST_CNVCALLING=''",
        "DEPENDS_LIST_EDREADCOUNT=''",
    ]
    STRINGS = {
        "demultiplex_not_required_msg": DEMUX_NOT_REQUIRED_MSG,
        "lane_metrics_suffix": LANE_METRICS_SUFFIX,
        "illumina_demultiplex_success": ILLUMINA_DEMULTIPLEX_SUCCESS,
        "aviti_demultiplex_success": AVITI_DEMULTIPLEX_SUCCESS,
    }
    PIPE_FH_GATK_TIMEOUT_ARGS = (  # This is specified for the GATK app in the Custom Panels pipeline for only FH samples
        # Set 6 hour timeout policy for gatk app and jobtimeoutexceeded
        # reason to auto restart list
        '--extra-args \'{"timeoutPolicyByExecutable": {"'
        f'{NEXUS_IDS["APPS"]["gatk"].split(":")[1]}'
        '": {"*":{"hours": 12}}}, "executionPolicy": {"restartOn": {"JobTimeoutExceeded":1, "JMInternalError":'
        ' 1, "UnresponsiveWorker": 2, "ExecutionError":1}}}\''
    )
    QUERIES = {
        # SQL queries for updating the Moka database (audit trail)
        "customrun": "insert into NGSCustomRuns(DNAnumber,PipelineVersion,RunID) values (%s)",
        "wes": "update NGSTest set PipelineVersion = %s, StatusID = %s where dna in ('%s') and StatusID = %s",
        "oncology": "insert into NGSOncologyAudit(SampleID1,SampleID2,RunID,PipelineVersion,ngspanelid) values (%s)",
    }
    SQL_IDS = {
        # Moka IDs for generating SQLs to update the Moka database (audit trail)
        "WORKFLOWS": {
            "gatk_pipe": 5304,
            "seglh_pipe": 5365,
            "wes": 5078,
            "archerdx": 5300,
            "msk": 5341,
            "snp": 5091,
            "tso500": 5301,
            "oncodeep": 5299,
        },
        "WES_TEST_STATUS": {
            "nextseq_sequencing": 1202218804,  # Test Status = NextSEQ sequencing
            "data_processing": 1202218805,  # Test Status = Data Processing
        },
    }
    STAGE_INPUTS = {
        "gatk_pipe": {
            "fastqc_reads": f"-i{NEXUS_IDS['STAGES']['gatk_pipe']['fastqc']}.reads=",
            "bwa_instance": f"--instance-type {NEXUS_IDS['STAGES']['gatk_pipe']['bwa']}=mem1_ssd1_v2_x8",
            "bwa_reads1": f"-i{NEXUS_IDS['STAGES']['gatk_pipe']['bwa']}.reads_fastqgz=",
            "bwa_reads2": f"-i{NEXUS_IDS['STAGES']['gatk_pipe']['bwa']}.reads2_fastqgz=",
            "bwa_rg_sample": f"-i{NEXUS_IDS['STAGES']['gatk_pipe']['bwa']}.read_group_sample=",
            "bwa_ref": f"-i{NEXUS_IDS['STAGES']['gatk_pipe']['bwa']}.genomeindex_targz=",
            "picard_instance": f"--instance-type {NEXUS_IDS['STAGES']['gatk_pipe']['picard']}=mem1_ssd1_v2_x4",
            "picard_bed": f"-i{NEXUS_IDS['STAGES']['gatk_pipe']['picard']}.vendor_exome_bedfile=",
            "picard_capturetype": f"-i{NEXUS_IDS['STAGES']['gatk_pipe']['picard']}.Capture_panel=",
            "gatk_instance": f"--instance-type {NEXUS_IDS['STAGES']['gatk_pipe']['gatk']}=",
            "gatk_padding": f"-i{NEXUS_IDS['STAGES']['gatk_pipe']['gatk']}.padding=0",
            "gatk_vcf_format": f"-i{NEXUS_IDS['STAGES']['gatk_pipe']['gatk']}.output_format=both",
            "filter_vcf_bed": f"-i{NEXUS_IDS['STAGES']['gatk_pipe']['filter_vcf']}.bedfile=",
            "filter_vcf_instance": f"--instance-type {NEXUS_IDS['STAGES']['gatk_pipe']['filter_vcf']}=mem1_ssd1_v2_x2",
            "happy_skip": f"-i{NEXUS_IDS['STAGES']['gatk_pipe']['happy']}.skip=",
            "happy_prefix": f"-i{NEXUS_IDS['STAGES']['gatk_pipe']['happy']}.prefix=",
            "sambamba_instance": f"--instance-type {NEXUS_IDS['STAGES']['gatk_pipe']['sambamba']}=mem1_ssd1_v2_x2",
            "sambamba_bed": f"-i{NEXUS_IDS['STAGES']['gatk_pipe']['sambamba']}.sambamba_bed=",
            "sambamba_min_base_qual": f"-i{NEXUS_IDS['STAGES']['gatk_pipe']['sambamba']}.min_base_qual=",
            "sambamba_min_mapping_qual": f"-i{NEXUS_IDS['STAGES']['gatk_pipe']['sambamba']}.min_mapping_qual=",
            "sambamba_cov_level": f"-i{NEXUS_IDS['STAGES']['gatk_pipe']['sambamba']}.coverage_level=",
            "sambamba_filter_cmds": (
                f"-i{NEXUS_IDS['STAGES']['gatk_pipe']['sambamba']}"
                ".additional_filter_commands='not (unmapped or secondary_alignment)'"
            ),
            "sambamba_excl_dups": f"-i{NEXUS_IDS['STAGES']['gatk_pipe']['sambamba']}.exclude_duplicate_reads=true",
            "sambamba_excl_failed_qual": (
                f"-i{NEXUS_IDS['STAGES']['gatk_pipe']['sambamba']}.exclude_failed_quality_control=true"
            ),
            "sambamba_count_overl_mates": (
                f"-i{NEXUS_IDS['STAGES']['gatk_pipe']['sambamba']}.merge_overlapping_mate_reads=true"
            ),
            "fhprs_skip": f"-i{NEXUS_IDS['STAGES']['gatk_pipe']['fhprs']}.skip=false",
            "fhprs_bed": f"-i{NEXUS_IDS['STAGES']['gatk_pipe']['fhprs']}.BEDfile=",
            "polyedge_gene": f"-i{NEXUS_IDS['STAGES']['gatk_pipe']['polyedge']}.gene=",
            "polyedge_chrom": f"-i{NEXUS_IDS['STAGES']['gatk_pipe']['polyedge']}.chrom=",
            "polyedge_poly_start": f"-i{NEXUS_IDS['STAGES']['gatk_pipe']['polyedge']}.poly_start=",
            "polyedge_poly_end": f"-i{NEXUS_IDS['STAGES']['gatk_pipe']['polyedge']}.poly_end=",
            "polyedge_skip": f"-i{NEXUS_IDS['STAGES']['gatk_pipe']['polyedge']}.skip=false",
        },
        "seglh_pipe": {
            "fastqc_reads": f"-i{NEXUS_IDS['STAGES']['seglh_pipe']['fastqc']}.reads=",
            "picard_instance": f"--instance-type {NEXUS_IDS['STAGES']['seglh_pipe']['picard']}=mem1_ssd1_v2_x4",
            "picard_bed": f"-i{NEXUS_IDS['STAGES']['seglh_pipe']['picard']}.vendor_exome_bedfile=",
            "picard_capturetype": f"-i{NEXUS_IDS['STAGES']['seglh_pipe']['picard']}.Capture_panel=",
            "sentieon_reads1": f"-i{NEXUS_IDS['STAGES']['seglh_pipe']['sentieon']}.reads_fastqgzs=",
            "sentieon_reads2": f"-i{NEXUS_IDS['STAGES']['seglh_pipe']['sentieon']}.reads2_fastqgzs=",
            "sentieon_sample": f"-i{NEXUS_IDS['STAGES']['seglh_pipe']['sentieon']}.sample=",
            "sentieon_gvcf_false": f"-i{NEXUS_IDS['STAGES']['seglh_pipe']['sentieon']}.output_gvcf=false",
            "sentieon_algo": f"-i{NEXUS_IDS['STAGES']['seglh_pipe']['sentieon']}.germline_algo=Haplotyper",
            "sentieon_instance": f"--instance-type {NEXUS_IDS['STAGES']['seglh_pipe']['sentieon']}=",
            "filter_vcf_bed": f"-i{NEXUS_IDS['STAGES']['seglh_pipe']['filter_vcf']}.bedfile=",
            "filter_vcf_instance": f"--instance-type {NEXUS_IDS['STAGES']['seglh_pipe']['filter_vcf']}=mem1_ssd1_v2_x2",
            "happy_skip": f"-i{NEXUS_IDS['STAGES']['seglh_pipe']['happy']}.skip=",
            "happy_prefix": f"-i{NEXUS_IDS['STAGES']['seglh_pipe']['happy']}.prefix=",
            "happy_bed": f"-i{NEXUS_IDS['STAGES']['seglh_pipe']['happy']}.panel_bed=",
            "sambamba_instance": f"--instance-type {NEXUS_IDS['STAGES']['seglh_pipe']['sambamba']}=mem1_ssd1_v2_x2",
            "sambamba_bed": f"-i{NEXUS_IDS['STAGES']['seglh_pipe']['sambamba']}.sambamba_bed=",
            "sambamba_min_base_qual": f"-i{NEXUS_IDS['STAGES']['seglh_pipe']['sambamba']}.min_base_qual=",
            "sambamba_min_mapping_qual": f"-i{NEXUS_IDS['STAGES']['seglh_pipe']['sambamba']}.min_mapping_qual=",
            "sambamba_cov_level": f"-i{NEXUS_IDS['STAGES']['seglh_pipe']['sambamba']}.coverage_level=",
            "sambamba_filter_cmds": (
                f"-i{NEXUS_IDS['STAGES']['seglh_pipe']['sambamba']}"
                ".additional_filter_commands='not (unmapped or secondary_alignment)'"
            ),
            "sambamba_excl_dups": f"-i{NEXUS_IDS['STAGES']['seglh_pipe']['sambamba']}.exclude_duplicate_reads=true",
            "sambamba_excl_failed_qual": (
                f"-i{NEXUS_IDS['STAGES']['seglh_pipe']['sambamba']}.exclude_failed_quality_control=true"
            ),
            "sambamba_count_overl_mates": (
                f"-i{NEXUS_IDS['STAGES']['seglh_pipe']['sambamba']}.merge_overlapping_mate_reads=true"
            ),
            "fhprs_skip": f"-i{NEXUS_IDS['STAGES']['seglh_pipe']['fhprs']}.skip=false",
            "fhprs_bed": f"-i{NEXUS_IDS['STAGES']['seglh_pipe']['fhprs']}.BEDfile=",
            "polyedge_gene": f"-i{NEXUS_IDS['STAGES']['seglh_pipe']['polyedge']}.gene=",
            "polyedge_chrom": f"-i{NEXUS_IDS['STAGES']['seglh_pipe']['polyedge']}.chrom=",
            "polyedge_poly_start": f"-i{NEXUS_IDS['STAGES']['seglh_pipe']['polyedge']}.poly_start=",
            "polyedge_poly_end": f"-i{NEXUS_IDS['STAGES']['seglh_pipe']['polyedge']}.poly_end=",
            "polyedge_skip": f"-i{NEXUS_IDS['STAGES']['seglh_pipe']['polyedge']}.skip=false",
        },

    }


class ToolboxConfig(PanelConfig):
    """
    Toolbox configuration
    """

    if BRANCH == "main":
        DNANEXUS_PROJECT_PREFIX = "002_"  # Denotes production status of run
    else:
        DNANEXUS_PROJECT_PREFIX = "003_"  # Denotes development status of run
    DNANEXUS_PROJ_ID = "${PROJECT_ID}"
    AD_LOGDIR = AD_LOGDIR
    CREDENTIALS = CREDENTIALS
    FASTQ_DIRS = FASTQ_DIRS
    RUNFOLDERS = RUNFOLDERS
    AVITI01_ID = AVITI01_ID
    AVITI02_ID = AVITI02_ID
    AVITI_IDS = AVITI_IDS
    NOVASEQ_ID = NOVASEQ_ID
    
    AVITI_SAMPLESHEET = AVITI_SAMPLESHEET
    TIMESTAMP = TIMESTAMP
    PSCON_IDS = [
        "NA12878",
        "136819",  # NA12878
        "HD200",  # Seracare v4 tumour fusion reference material
    ]
    NTCON_IDS = ["00000", "NTCcon", "NTC000", "NC000"]
    STRINGS = {
        "phasing_metrics_suffix": ".illumina_phasing_metrics",
        "lane_metrics_suffix": LANE_METRICS_SUFFIX,
    }
    FLAG_FILES = {
        "upload_started": "DNANexus_upload_started.txt",  # Holds upload agent output
        "bclconvertlog": "bclconvert_output.log",  # Holds bclconvert logs
        "bases2fastqlog": "bases2fastq_output.log", # Holds bases2fastq logs
        "filecheck": "filecheck.txt",  # File holding integrity check results
        "initial_sscheck_flag": "initial_sscheck_flagfile.txt",  # Denotes initial SampleSheet has been checked
        "sscheck_flag": "sscheck_flagfile.txt",  # Denotes SampleSheet has been checked
        "illumina_seq_complete": "CopyComplete.txt",  # Illumina Sequencing complete file after network copy
        "aviti_seq_complete": "RunUploaded.json", # AVITI Sequencing complete file
    }
    TEST_PROGRAMS_DICT = {
        "dx_toolkit": {
            "executable": "dx",
            "test_cmd": f"{SDK_SOURCE}; dx --version",
        },
        "upload_agent": {
            "executable": UPLOAD_AGENT_EXE,
            "test_cmd": f"{UPLOAD_AGENT_EXE} --version",
        },
        "gatk_collect_lane_metrics": {
            "executable": "docker",
            "test_cmd": f"docker run --rm {GATK_DOCKER} ./gatk CollectIlluminaLaneMetrics --version",
        },
        "bclconvert": {
            "executable": "docker",
            "test_cmd": f"docker run --rm {BCLCONVERT_DOCKER} --version",
        },
        "bases2fastq" : {
            "executable": "docker",
            "test_cmd": f"docker run --rm {BASES2FASTQ_DOCKER} bases2fastq --version",
        },
    }


class URConfig:
    """
    Upload Runfolder configuration
    """

    CREDENTIALS = CREDENTIALS
    DX_CMDS = DX_CMDS
    TIMESTAMP = TIMESTAMP
    AVITI_IDS = AVITI_IDS
    STRINGS = {
        "upload_started": "Upload started",  # Statement to write to DNAnexus upload started file
    }


class RunfolderCleanupConfig(PanelConfig):
    """
    Runfolder Cleanup configuration
    """

    TIMESTAMP = TIMESTAMP
    RUNFOLDER_PATTERN = RUNFOLDER_PATTERN
    RUNFOLDERS = RUNFOLDERS
    CREDENTIALS = CREDENTIALS
