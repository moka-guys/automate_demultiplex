#!/usr/bin/python3
"""
Automate demultiplex configuration. Contains the following settings:
- General settings used across modules
- Demultiplexing script-specific settings
- Setoff workflows script-specific settings
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
    "host": "email-smtp.eu-west-1.amazonaws.com",
    "port": 587,
    "binfx_email": "gst-tr.mokaguys@nhs.net",
    "alerts_email": "moka.alerts@gstt.nhs.uk",
}

if BRANCH == "master" and "pytest" not in sys.modules:  # Prod branch
    TESTING = False  # Set testing mode
    SCRIPT_MODE = "PROD_MODE"
    JOB_NAME_STR = "--name "
    RUNFOLDERS = "/media/data3/share"
    AD_LOGDIR = os.path.join(DOCUMENT_ROOT, "automate_demultiplexing_logfiles")
    MAIL_SETTINGS = MAIL_SETTINGS | {  # Add prod mail recipients
        "pipeline_started_subj": f"{SCRIPT_MODE}. ALERT: Started pipeline for %s",
        "binfx_recipient": MAIL_SETTINGS["binfx_email"],
        # Oncology email address for email alerts
        "oncology_ops_email": "synnovis.OncologyDutyScientist@nhs.net",
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
    RUNFOLDERS = "/media/data3/share/testing"
    AD_LOGDIR = os.path.join(RUNFOLDERS, "automate_demultiplexing_logfiles")
    MAIL_SETTINGS = MAIL_SETTINGS | {  # Add test mail recipients
        "pipeline_started_subj": f"{SCRIPT_MODE}. ALERT: Started pipeline for %s",
        "binfx_recipient": "mokaguys@gmail.com",
        # Oncology email address for email alerts
        "oncology_ops_email": "mokaguys@gmail.com",
        "wes_samplename_emaillist": ["mokaguys@gmail.com"],
    }

CREDENTIALS = {
    "email_user": os.path.join(DOCUMENT_ROOT, ".amazon_email_username"),
    "email_pw": os.path.join(DOCUMENT_ROOT, ".amazon_email_pw"),
    "dnanexus_authtoken": os.path.join(DOCUMENT_ROOT, ".dnanexus_auth_token"),
}
NOVASEQ_ID = "A01229"  # Novaseq sequencer ID
RUNFOLDER_PATTERN = "^[0-9]{6}.*$"  # Runfolders start with 6 digits
FASTQ_DIRS = {
    "fastqs": "Data/Intensities/BaseCalls",  # Path to fastq files
    "tso_fastqs": "${PROJECT_ID}:/analysis_folder/Logs_Intermediates/CollapsedReads/",
}
SDK_SOURCE = "source /usr/local/src/mokaguys/apps/dx-toolkit/environment"  # dxtoolkit path

# DNAnexus upload agent path
UPLOAD_AGENT_EXE = "/usr/local/src/mokaguys/apps/dnanexus-upload-agent-1.5.17-linux/ua"
BCL2FASTQ_DOCKER = "seglh/bcl2fastq2:v2.20.0.422_60dbb5a"
GATK_DOCKER = "broadinstitute/gatk:4.1.8.1"  # TODO this image should have a hash added in future

LANE_METRICS_SUFFIX = ".illumina_lane_metrics"
DEMUX_NOT_REQUIRED_MSG = "Run does not need demultiplexing locally"
DEMULTIPLEX_SUCCESS = "Processing completed with 0 errors and 0 warnings."

# -------------- DNANEXUS-SPECIFIC --------------------------------------------------------------

NEXUS_IDS = {
    # Paths / IDs for data items in 001_Tools
    "FILES": {
        "tso500_docker": f"{TOOLS_PROJECT}:file-Fz9Zyx00b5j8xKVkKv4fZ6JB",  # trusight-oncology-500-ruo-2.2.0.zip
        "hs37d5_bwa_index": f"{TOOLS_PROJECT}:file-B6ZY4942J35xX095VZyQBk0v",  # hs37d5.bwa-index.tar.gz
        "hs37d5_ref_with_index": f"{TOOLS_PROJECT}:file-ByYgX700b80gf4ZY1GxvF3Jv",  # hs37d5.fasta-index.tar.gz
        "hs37d5_ref_no_index": f"{TOOLS_PROJECT}:file-B6ZY7VG2J35Vfvpkj8y0KZ01",  # hs37d5.fa.gz
        "masked_reference": MASKED_REFERENCE,  # hs37d5_Pan4967.bwa-index.tar.gz
        "ed_vcp1_readcount_normals": f"{TOOLS_PROJECT}:file-GgKKP4Q01jZ62QgF2bbPqz78",  # Pan5208_normals_v1.0.0.RData
        "ed_vcp2_readcount_normals": f"{TOOLS_PROJECT}:file-Gbkgyq00ZpxpFKx03zVPJ9GX",  # Pan5188_normals_v1.1.0.RData
        "ed_vcp3_readcount_normals": f"{TOOLS_PROJECT}:file-Gj62x5804G8j5Vq90q712FP9",  # Pan5217_normals_v1.0.0.RData
        "sompy_truth_vcf": f"{TOOLS_PROJECT}:file-G7g9Pfj0jy1f87k1J1qqX83X",  # HD200_expectedsorted.vcf
    },
    "APPS": {
        "tso500": f"{TOOLS_PROJECT}:applet-GZgv0Jj0jy1Yfbx3QvqyKjzp",  # TSO500_v1.6.0
        "congenica_upload": f"{TOOLS_PROJECT}:applet-G8QGBK80jy1zJK6g9yVP7P8V",  # congenica_upload_v1.3.2
        "congenica_sftp": f"{TOOLS_PROJECT}:applet-GFfJpj80jy1x1Bz1P1Bk3vQf",  # wes_congenica_sftp_upload_v1.0
        "qiagen_upload": f"{TOOLS_PROJECT}:applet-Gb6G4k00v09KXfq8f6BP7f23",  # qiagen_upload_v1.0.0
        "oncodeep_upload": f"{TOOLS_PROJECT}:applet-GkkGQ880jy1vXXFZBFG7232G",  # oncodeep_upload v1.0.0
        "upload_multiqc": f"{TOOLS_PROJECT}:applet-G2XY8QQ0p7kzvPZBJGFygP6f",  # upload_multiqc_v1.4.0
        "multiqc": f"{TOOLS_PROJECT}:applet-GXqBzg00jy1pXkQVkY027QqV",  # multiqc_v1.18.0
        "sompy": f"{TOOLS_PROJECT}:applet-G9yPb780jy1p660k6yBvQg07",  # sompy_v1.2
        "sambamba": f"{TOOLS_PROJECT}:applet-G6vyyf00jy1kPkX9PJ1YkxB1",  # chanjo_sambamba_coverage_v1.13
        "fastqc": f"{TOOLS_PROJECT}:applet-GKXqZV80jy1QxF4yKYB4Y3Kz",  # fastqc_v1.4.0
        "gatk": f"{TOOLS_PROJECT}:applet-FYZ097j0jy1ZZPx30GykP63J",  # gatk3_human_exome_pipeline_v1.5
        "peddy": f"{TOOLS_PROJECT}:applet-Fjvfk280jy1fVg8Q3b1bF6Y1",  # peddy_v1.5
        "ed_readcount": f"{TOOLS_PROJECT}:applet-GbkVzbQ0jy1zBZf5k6Xk6QP7",  # ED_readcount_analysis_v1.3.0
        "ed_cnvcalling": f"{TOOLS_PROJECT}:applet-GbkVyQ80jy1Xf1p6jpPK6p1x",  # ED_cnv_calling_v1.3.0
        "rpkm": f"{TOOLS_PROJECT}:applet-FxJj0F00jy1ZVXp36PBz2p1j",  # RPKM_using_conifer_v1.6
        "duty_csv": f"{TOOLS_PROJECT}:applet-Gb6QKf00v09JV7KBVJqFVxX6",  # duty_csv_v1.3.0
    },
    "WORKFLOWS": {
        "pipe": f"{TOOLS_PROJECT}:workflow-GPq04280jy1k1yVkQP0fXqBg",  # GATK3.5_v2.18
        "wes": f"{TOOLS_PROJECT}:workflow-FjjbQ5Q0jy1ZgyjQ3g1zgx9k",  # MokaWES_v1.8
        "snp": f"{TOOLS_PROJECT}:workflow-GB3kyJj0jy1j06704fxX9J7j",  # MokaSNP_v1.2.0
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
    },
}
NEXUS_IDS["WORKFLOWS"]["archerdx"] = NEXUS_IDS["APPS"]["fastqc"]
NEXUS_IDS["WORKFLOWS"]["oncodeep"] = NEXUS_IDS["APPS"]["fastqc"]


APP_INPUTS = {  # Inputs for apps run outside of DNAnexus workflows
    "tso500": {
        "docker": f"-iTSO500_ruo={NEXUS_IDS['FILES']['tso500_docker']}",
        "samplesheet": "-isamplesheet=${PROJECT_ID}:/${RUNFOLDER_NAME}/",
        "analysis_options": "-ianalysis_options=",
        "project_name": "-iproject_name=${PROJECT_NAME}",
        "runfolder_name": "-irunfolder_name=${RUNFOLDER_NAME}",
    },
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
        "pannos": "-ibamfile_pannumbers=",
    },
    "ed_cnvcalling": {
        "readcount": "-ireadcount_file=${ED_READCOUNT_JOB_ID}:RData",
        "bed": "-isubpanel_bed=",
        "proj": "-iproject_name=${PROJECT_NAME}",
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
        "file_to_upload": "-ifile_to_upload=${PROJECT_ID}:",        
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
    "depends_gatk": "${DEPENDS_LIST_GATK}",
    # Arguments to capture jobids. Job IDS are built into a string that can be passed to
    # downstream apps to ensure the jobs don't start until those job ids have completed successfully
    "depends_list": 'DEPENDS_LIST="${DEPENDS_LIST} -d ${JOB_ID} "',
    "depends_list_gatk": 'DEPENDS_LIST_GATK="${DEPENDS_LIST_GATK} -d ${JOB_ID} "',
    "depends_list_gatk_recombined": 'DEPENDS_LIST="${DEPENDS_LIST} ${DEPENDS_LIST_GATK} "',
    "depends_list_edreadcount": 'DEPENDS_LIST_EDREADCOUNT="${DEPENDS_LIST_EDREADCOUNT} -d ${ED_READCOUNT_JOB_ID} "',
    "depends_list_cnvcalling": 'DEPENDS_LIST_CNVCALLING="${DEPENDS_LIST_CNVCALLING} -d ${CNVCALLING_JOB_ID} "',
    "depends_list_cnv_recombined": (
        'DEPENDS_LIST="${DEPENDS_LIST} ${DEPENDS_LIST_EDREADCOUNT} ${DEPENDS_LIST_CNVCALLING}"'
    ),
}

DX_CMDS = {
    "create_proj": 'PROJECT_ID="$(dx new project --bill-to %s "%s" --brief --auth ${AUTH})"',
    "find_proj_name": f"{SDK_SOURCE}; dx find projects --name *%s* " "--auth %s | awk '{print $3}'",
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
    "pipe": f"JOB_ID=$(dx run {NEXUS_IDS['WORKFLOWS']['pipe']} --priority high -y {JOB_NAME_STR}",
    "wes": f"JOB_ID=$(dx run {NEXUS_IDS['WORKFLOWS']['wes']} --priority high -y {JOB_NAME_STR}",
    "snp": f"JOB_ID=$(dx run {NEXUS_IDS['WORKFLOWS']['snp']} --priority high -y {JOB_NAME_STR}",
    "tso500": (
        f"JOB_ID=$(dx run {NEXUS_IDS['APPS']['tso500']} --priority high -y {JOB_NAME_STR} "
        "--instance-type mem1_ssd1_v2_x72"
    ),
    "fastqc": f"JOB_ID=$(dx run {NEXUS_IDS['APPS']['fastqc']} --priority high -y {JOB_NAME_STR}",
    "peddy": (  # TODO move instance type into app itself
        f"JOB_ID=$(dx run {NEXUS_IDS['APPS']['peddy']} --priority high "
        f"-y --instance-type mem1_ssd1_v2_x2 {JOB_NAME_STR}"
    ),
    "multiqc": f"JOB_ID=$(dx run {NEXUS_IDS['APPS']['multiqc']} --priority high -y {JOB_NAME_STR}",
    "upload_multiqc": (  # TODO move instance type into app itself
        f"JOB_ID=$(dx run {NEXUS_IDS['APPS']['upload_multiqc']} "
        f"--priority high -y --instance-type mem1_ssd1_v2_x2 {JOB_NAME_STR}"
    ),
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
    "congenica_sftp": f"JOB_ID=$(dx run {NEXUS_IDS['APPS']['congenica_sftp']} --priority high -y {JOB_NAME_STR}",
    "congenica_upload": (  # TODO move instance type into app itself
        f"JOB_ID=$(dx run {NEXUS_IDS['APPS']['congenica_upload']} --priority high -y "
        f"--instance-type mem1_ssd1_v2_x2 {JOB_NAME_STR}"
    ),
    # Sleep command ensures the number of concurrent jobs does not surpass the QCII limit of 10
    "qiagen_upload": (
        f"sleep 1.2m; JOB_ID=$(dx run {NEXUS_IDS['APPS']['qiagen_upload']} --priority high -y {JOB_NAME_STR}"
    ),
    "oncodeep_upload": (
        f"JOB_ID=$(dx run {NEXUS_IDS['APPS']['oncodeep_upload']} --priority high -y "
        f"{JOB_NAME_STR} -iaccount_type=Production"
    ),
    "sompy": f"JOB_ID=$(dx run {NEXUS_IDS['APPS']['sompy']} --priority high -y {JOB_NAME_STR}",
    "sambamba": f"JOB_ID=$(dx run {NEXUS_IDS['APPS']['sambamba']} --priority high -y {JOB_NAME_STR}",
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
    RUNFOLDER_PATTERN = RUNFOLDER_PATTERN
    RUNFOLDERS = RUNFOLDERS
    STRINGS = {
        "demultiplex_not_required_msg": DEMUX_NOT_REQUIRED_MSG,
        "lane_metrics_suffix": LANE_METRICS_SUFFIX,
        "cd_success": "picard.illumina.CollectIlluminaLaneMetrics done",
    }
    TESTING = TESTING
    BCL2FASTQ2_CMD = (
        f"docker run --rm -v %s:/mnt/run -v %s:/mnt/run/%s {BCL2FASTQ_DOCKER} -R /mnt/run "
        "--sample-sheet /mnt/run/%s --no-lane-splitting"
    )
    CD_CMD = (
        f"docker run --rm -v %s:/input_run {GATK_DOCKER} ./gatk CollectIlluminaLaneMetrics "
        "--RUN_DIRECTORY /input_run --OUTPUT_DIRECTORY /input_run --OUTPUT_PREFIX %s"
    )

    CHECKSUMS_ALREADY_ASSESSED = (
        "Checksums already assessed by AS"  # Written to file by AS
    )
    CHECKSUM_MATCH_MSG = "Checksums match"  # Success message written to md5checksum file by integrity check scripts
    # Failure message written to md5checksum file by integrity check scripts
    CHECKSUM_DO_NOT_MATCH_MSG = "Checksums do not match"
    SAMPLESHEET_SUCCESS_MSG = "Samplesheet check successful with no errors identified"
    SAMPLESHEET_ERRORS_MSG = (
        "Processing halted. SampleSheet contains disallowed SampleSheet errors: %s"
    )
    DEMULTIPLEX_TEST_RUNFOLDERS = [
        "999999_NB552085_0496_DEMUXINTEG",
        "999999_M02353_0496_000000000-DEMUX",
        "999999_A01229_0182_AHM2TSO500",  # Used for testing demultiplex and sw scripts
        "999999_M02631_0285_000000000-DEVOO",
        "999999_NB551068_0285_OODEVINTEG",
        "999999_M02631_0285_000000000-DVUMI",
    ]
    SEQUENCER_IDS = {
        # Requires_ic denotes sequencers requiring md5 checksums from integrity check to be assessed
        "NB551068": {"requires_ic": True},
        "NB552085": {"requires_ic": True},
        "M02353": {"requires_ic": False},
        "M02631": {"requires_ic": False},
        NOVASEQ_ID: {"requires_ic": True},
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
    PROD_ORGANISATION = "org-viapath_prod"  # Prod org for billing
    if BRANCH == "master":  # Prod branch
        
        BSPS_ID = "BSPS_MD"
        DNANEXUS_USERS = {  # User access level
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
    RUNFOLDER_NAME = "${RUNFOLDER_NAME}"
    EMPTY_DEPENDS = "DEPENDS_LIST=''"
    EMPTY_CP_DEPENDS = [
        "DEPENDS_LIST_GATK=''",
        "DEPENDS_LIST_CNVCALLING=''",
        "DEPENDS_LIST_EDREADCOUNT=''",
    ]
    STRINGS = {
        "demultiplex_not_required_msg": DEMUX_NOT_REQUIRED_MSG,
        "lane_metrics_suffix": LANE_METRICS_SUFFIX,
        "demultiplex_success": DEMULTIPLEX_SUCCESS,
        "upload_started": "Upload started",  # Statement to write to DNAnexus upload started file
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
            "pipe": 5302,
            "wes": 5078,
            "archerdx": 5300,
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
        "pipe": {
            "fastqc_reads": f"-i{NEXUS_IDS['STAGES']['pipe']['fastqc']}.reads=",
            "bwa_instance": f"--instance-type {NEXUS_IDS['STAGES']['pipe']['bwa']}=mem1_ssd1_v2_x8",
            "bwa_reads1": f"-i{NEXUS_IDS['STAGES']['pipe']['bwa']}.reads_fastqgz=",
            "bwa_reads2": f"-i{NEXUS_IDS['STAGES']['pipe']['bwa']}.reads2_fastqgz=",
            "bwa_rg_sample": f"-i{NEXUS_IDS['STAGES']['pipe']['bwa']}.read_group_sample=",
            "bwa_ref": f"-i{NEXUS_IDS['STAGES']['pipe']['bwa']}.genomeindex_targz=",
            "picard_instance": f"--instance-type {NEXUS_IDS['STAGES']['pipe']['picard']}=mem1_ssd1_v2_x4",
            "picard_bed": f"-i{NEXUS_IDS['STAGES']['pipe']['picard']}.vendor_exome_bedfile=",
            "picard_capturetype": f"-i{NEXUS_IDS['STAGES']['pipe']['picard']}.Capture_panel=",
            "gatk_instance": f"--instance-type {NEXUS_IDS['STAGES']['pipe']['gatk']}=",
            "gatk_padding": f"-i{NEXUS_IDS['STAGES']['pipe']['gatk']}.padding=0",
            "gatk_vcf_format": f"-i{NEXUS_IDS['STAGES']['pipe']['gatk']}.output_format=both",
            "filter_vcf_bed": f"-i{NEXUS_IDS['STAGES']['pipe']['filter_vcf']}.bedfile=",
            "filter_vcf_instance": f"--instance-type {NEXUS_IDS['STAGES']['pipe']['filter_vcf']}=mem1_ssd1_v2_x2",
            "happy_skip": f"-i{NEXUS_IDS['STAGES']['pipe']['happy']}.skip=",
            "happy_prefix": f"-i{NEXUS_IDS['STAGES']['pipe']['happy']}.prefix=",
            "sambamba_instance": f"--instance-type {NEXUS_IDS['STAGES']['pipe']['sambamba']}=mem1_ssd1_v2_x2",
            "sambamba_bed": f"-i{NEXUS_IDS['STAGES']['pipe']['sambamba']}.sambamba_bed=",
            "sambamba_min_base_qual": f"-i{NEXUS_IDS['STAGES']['pipe']['sambamba']}.min_base_qual=",
            "sambamba_min_mapping_qual": f"-i{NEXUS_IDS['STAGES']['pipe']['sambamba']}.min_mapping_qual=",
            "sambamba_cov_level": f"-i{NEXUS_IDS['STAGES']['pipe']['sambamba']}.coverage_level=",
            "sambamba_filter_cmds": (
                f"-i{NEXUS_IDS['STAGES']['pipe']['sambamba']}"
                ".additional_filter_commands='not (unmapped or secondary_alignment)'"
            ),
            "sambamba_excl_dups": f"-i{NEXUS_IDS['STAGES']['pipe']['sambamba']}.exclude_duplicate_reads=true",
            "sambamba_excl_failed_qual": (
                f"-i{NEXUS_IDS['STAGES']['pipe']['sambamba']}.exclude_failed_quality_control=true"
            ),
            "sambamba_count_overl_mates": (
                f"-i{NEXUS_IDS['STAGES']['pipe']['sambamba']}.merge_overlapping_mate_reads=true"
            ),
            "fhprs_skip": f"-i{NEXUS_IDS['STAGES']['pipe']['fhprs']}.skip=false",
            "fhprs_bed": f"-i{NEXUS_IDS['STAGES']['pipe']['fhprs']}.BEDfile=",
            "polyedge_gene": f"-i{NEXUS_IDS['STAGES']['pipe']['polyedge']}.gene=",
            "polyedge_chrom": f"-i{NEXUS_IDS['STAGES']['pipe']['polyedge']}.chrom=",
            "polyedge_poly_start": f"-i{NEXUS_IDS['STAGES']['pipe']['polyedge']}.poly_start=",
            "polyedge_poly_end": f"-i{NEXUS_IDS['STAGES']['pipe']['polyedge']}.poly_end=",
            "polyedge_skip": f"-i{NEXUS_IDS['STAGES']['pipe']['polyedge']}.skip=false",
        },
        "wes": {
            "fastqc1_reads": f"-i{NEXUS_IDS['STAGES']['wes']['fastqc1']}.reads=",
            "fastqc2_reads": f"-i{NEXUS_IDS['STAGES']['wes']['fastqc2']}.reads=",
            "picard_bed": f"-i{NEXUS_IDS['STAGES']['wes']['picard']}.vendor_exome_bedfile=",
            "sambamba_bed": f"-i{NEXUS_IDS['STAGES']['wes']['sambamba']}.sambamba_bed=",
            # Prevents incorrect parsing from fastq filename
            "sentieon_samplename": f"-i{NEXUS_IDS['STAGES']['wes']['sentieon']}.sample=",
            "sentieon_bed": f"-i{NEXUS_IDS['STAGES']['wes']['sentieon']}.targets_bed=",
        },
        "snp": {
            "fastqc1_reads": f"-i{NEXUS_IDS['STAGES']['snp']['fastqc1']}.reads=",
            "fastqc2_reads": f"-i{NEXUS_IDS['STAGES']['snp']['fastqc2']}.reads=",
            "sentieon_bed": f"-i{NEXUS_IDS['STAGES']['snp']['sentieon']}.targets_bed=",
            # Prevents incorrect parsing from fastq filename
            "sentieon_samplename": f"-i{NEXUS_IDS['STAGES']['snp']['sentieon']}.sample=",
        },
    }


class ToolboxConfig(PanelConfig):
    """
    Toolbox configuration
    """
    if BRANCH == "master":
        DNANEXUS_PROJECT_PREFIX = "002_"  # Denotes production status of run
    else:
        DNANEXUS_PROJECT_PREFIX = "003_"  # Denotes development status of run
    DNANEXUS_PROJ_ID = "${PROJECT_ID}"
    AD_LOGDIR = AD_LOGDIR
    CREDENTIALS = CREDENTIALS
    FASTQ_DIRS = FASTQ_DIRS
    RUNFOLDERS = RUNFOLDERS
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
        "bcl2fastqlog": "bcl2fastq2_output.log",  # Holds bcl2fastq2 logs
        "md5checksum": "md5checksum.txt",  # File holding checksum results
        "sscheck_flag": "sscheck_flagfile.txt",  # Denotes SampleSheet has been checked
        "seq_complete": "RTAComplete.txt",  # Sequencing complete file
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
        "bcl2fastq2": {
            "executable": "docker",
            "test_cmd": f"docker run --rm {BCL2FASTQ_DOCKER} --version",
        },
    }


class URConfig:
    """
    Upload Runfolder configuration
    """

    CREDENTIALS = CREDENTIALS
    DX_CMDS = DX_CMDS
    TIMESTAMP = TIMESTAMP
