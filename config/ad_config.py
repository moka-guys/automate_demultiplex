#!/usr/bin/python3
# coding=utf-8
"""
Automate demultiplex configuration
"""
import os
import datetime
from pygit2 import Repository
from pathlib import Path

# GENERAL SETTINGS USED ACROSS MODULES

# Timestamp used for naming log files with datetime
TIMESTAMP = str(f"{datetime.datetime.now():%Y%m%d_%H%M%S}")

# Project working directory
PROJECT_DIR = str(Path(__file__).absolute().parent.parent)
# Root of folder containing apps, automate_demultiplexing_logfiles and
# development_area scripts (2 levels up from this file)
DOCUMENT_ROOT = "/".join(PROJECT_DIR.split("/")[:-2])

branch = Repository('.').head.shorthand

MAIL_SETTINGS = {
    "host": "email-smtp.eu-west-1.amazonaws.com",
    "port": 587,
    "binfx_email": "gst-tr.mokaguys@nhs.net",
    "alerts_email": "moka.alerts@gstt.nhs.uk",
}

if branch == "master":  # Prod branch
    TESTING = False  # Set testing mode
    SCRIPT_MODE = "PROD MODE"
    JOB_NAME_STR = "--name "
    RUNFOLDERS = "/media/data3/share"
    AD_LOGDIR = os.path.join(DOCUMENT_ROOT, "automate_demultiplexing_logfiles")
    MAIL_SETTINGS = MAIL_SETTINGS | {  # Add prod mail recipients
        "pipeline_started_subj": f"{SCRIPT_MODE}. ALERT: Started pipeline for %s",
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
else:  # Testing branch
    TESTING = True
    SCRIPT_MODE = "TEST_MODE"
    # JOB_NAME_STR must be @-separated to be picked up by the gmail filter which
    # determines which slack channel to send the alert to
    JOB_NAME_STR = "--name TEST@"
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

# Sequencer / run identifiers
NOVASEQ_ID = "A01229"
SEQUENCER_IDS = ["NB551068", "NB552085", "M02353", "M02631", NOVASEQ_ID]
RUNTYPE_LIST = ["NGS", "ADX", "ONC", "SNP", "TSO", "LRPCR"]
# Sequencers requiring md5 checksums from integrity check to be assessed
SEQUENCERS_WITH_INTEGRITY_CHECK = ["NB551068", "NB552085", NOVASEQ_ID]

RUNFOLDER_PATTERN = "^[0-9]{6}.*$"  # Runfolders start with 6 digits

FASTQ_DIRS = {
    "fastqs": "Data/Intensities/BaseCalls",  # Path to fastq files
    "tso_fastqs": "analysis_folder/Logs_Intermediates/CollapsedReads/",
}

# ================ DEMULTIPLEXING (demultiplex.py) ============================
# Settings unique to the demultiplex script

# Integrity check
CHECKSUM_COMPLETE_MSG = "Checksum result reported"  # Checksum complete statement
CHECKSUM_MATCH_MSG = "Checksums match"  # Statement to write when checksums match

# tso500 runfolder is used for testing both demultiplexing and usw script
DEMULTIPLEX_TEST_RUNFOLDERS = [
    "999999_NB552085_0496_DEMUXINTEG",
    "999999_M02353_0496_000000000-DEMUX",
    "999999_A01229_0182_AHM2TSO500",
]

SDK_SOURCE = "/usr/local/src/mokaguys/apps/dx-toolkit/environment"
BCL2FASTQ2_CMD = (
    "sudo docker run --rm -v %s:/mnt/run -v %s:/mnt/run/%s "
    "seglh/bcl2fastq2:v2.20.0.422_25dd0c0 -R /mnt/run --sample-sheet /mnt/run/%s "
    "--no-lane-splitting >> %s 2>&1"
)

UPLOAD_AGENT_EXE = "/usr/local/src/mokaguys/apps/dnanexus-upload-agent-1.5.17-linux/ua"

STRINGS = {
    "cd_success": "picard.illumina.CollectIlluminaLaneMetrics done",
    "lane_metrics_suffix": ".illumina_lane_metrics",
    "phasing_metrics_suffix": ".illumina_phasing_metrics",
    "cd_err": "Exception",
    "demultiplexlog_tso500_msg": "TSO500 run. Does not need demultiplexing locally",
    "demultiplex_success": "Processing completed with 0 errors and 0 warnings.",
}

TEST_PROGRAMS_DICT = {
    "dx_toolkit": {
        "executable": "dx",
        "test_cmd": f"source {SDK_SOURCE}; dx --version",
        },
    "upload_agent": {
        "executable": UPLOAD_AGENT_EXE,
        "test_cmd": f"{UPLOAD_AGENT_EXE} --version",
        },
    "gatk_collect_lane_metrics": {
        "executable": "docker",
        "test_cmd": (
            "sudo docker run --rm broadinstitute/gatk:4.1.8.1 ./gatk "
            "CollectIlluminaLaneMetrics --version"
            ),
        },
    }

TEST_IMAGES_DICT = {
    "bcl2fastq2": f'sudo docker run --rm seglh/bcl2fastq2:v2.20.0.422_25dd0c0 --version'
    }

# ================ UPLOAD AND SETOFF WORKFLOWS ================================
# Settings unique to the upload and setoff workflows script

REF_SAMPLE_IDS = [
    "NA12878",
    "136819",
]  # NA12878 identifiers to exclude from congenica upload

# General
PROD_ORGANISATION = "org-viapath_prod"  # Prod org for billing

if TESTING:
    DNANEXUS_PROJECT_PREFIX = "003_"  # Denotes development status of run
    DNANEXUS_USERS = {  # User access level
        "viewers": [],
        "admins": [PROD_ORGANISATION],
    }
else:
    DNANEXUS_PROJECT_PREFIX = "002_"  # Denotes production status of run
    DNANEXUS_USERS = {  # User access level
        "viewers": [PROD_ORGANISATION, "InterpretationRequest"],
        "admins": ["mokaguys"],
    }

# Paths / IDs for apps in 001_Tools
TOOLS_PROJECT = "project-ByfFPz00jy1fk6PjpZ95F27J"  # 001_ToolsReferenceData

NEXUS_IDS = {
    "FILES": {
        "tso500_docker": f"{TOOLS_PROJECT}:file-Fz9Zyx00b5j8xKVkKv4fZ6JB",
        "hs37d5_bwa_index": f"{TOOLS_PROJECT}:file-B6ZY4942J35xX095VZyQBk0v",
        "hs37d5_ref_with_index": f"{TOOLS_PROJECT}:file-ByYgX700b80gf4ZY1GxvF3Jv",
        "hs37d5_ref_no_index": f"{TOOLS_PROJECT}:file-B6ZY7VG2J35Vfvpkj8y0KZ01",
        "masked_reference": f"{TOOLS_PROJECT}:file-GF84GF00QfBfzV35Gf8Qg53q",
        "ed_vcp1_readcount_normals": f"{TOOLS_PROJECT}:file-GZYK6380f66PPy4kjzVQ7xj8",
        "ed_vcp2_readcount_normals": f"{TOOLS_PROJECT}:file-GZYbq400YG627Q12g1bbP440",
    },
    "APPS": {
        "tso500": f"{TOOLS_PROJECT}:applet-GZgv0Jj0jy1Yfbx3QvqyKjzp",
        "congenica_app": f"{TOOLS_PROJECT}:applet-G8QGBK80jy1zJK6g9yVP7P8V",
        "congenica_sftp": f"{TOOLS_PROJECT}:applet-GFfJpj80jy1x1Bz1P1Bk3vQf",
        "upload_multiqc": f"{TOOLS_PROJECT}:applet-G2XY8QQ0p7kzvPZBJGFygP6f",
        "multiqc": f"{TOOLS_PROJECT}:applet-GXqBzg00jy1pXkQVkY027QqV",
        "sompy": f"{TOOLS_PROJECT}:applet-G9yPb780jy1p660k6yBvQg07",
        "sambamba": f"{TOOLS_PROJECT}:applet-G6vyyf00jy1kPkX9PJ1YkxB1",
        "fastqc": f"{TOOLS_PROJECT}:applet-GKXqZV80jy1QxF4yKYB4Y3Kz",
        "gatk": f"{TOOLS_PROJECT}:applet-FYZ097j0jy1ZZPx30GykP63J",
        "peddy": f"{TOOLS_PROJECT}:applet-Fjvfk280jy1fVg8Q3b1bF6Y1",
        "ed_readcount": f"{TOOLS_PROJECT}:applet-GZJK5kj0jy1V5Qx4G7j6kb92",
        "ed_cnvcalling": f"{TOOLS_PROJECT}:applet-GZJK2J80jy1k14ZkYjjZ5qKp",
        "rpkm": f"{TOOLS_PROJECT}:applet-FxJj0F00jy1ZVXp36PBz2p1j",
        "duty_csv": f"{TOOLS_PROJECT}:applet-GZYx3Kj0kKj3YBV7qgK6VjXQ",
    },
    "WORKFLOWS": {
        "pipe": f"{TOOLS_PROJECT}:workflow-GPq04280jy1k1yVkQP0fXqBg",
        "wes": f"{TOOLS_PROJECT}:workflow-FjjbQ5Q0jy1ZgyjQ3g1zgx9k",
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
    },
}
NEXUS_IDS["WORKFLOWS"]["archerdx"] = NEXUS_IDS["APPS"]["fastqc"]

# Inputs for apps run outside of workflows
APP_INPUTS = {
    "tso500": {
        "docker": "-iTSO500_ruo=",
        "samplesheet": "-isamplesheet=",
        "analysis_options": "-ianalysis_options=",
        "project_name": "-iproject_name=",
        "runfolder_name": "-irunfolder_name=",
        "ht_instance": "mem1_ssd1_v2_x72",
        "lt_instance": "mem1_ssd1_v2_x36",
    },
    "sambamba": {
        "bam": "-ibamfile=",
        "bai": "-ibam_index=",
        "coverage_level": "-icoverage_level=",
        "sambamba_bed": "-isambamba_bed=",
        "cov_cmds": (
            "-imerge_overlapping_mate_reads=true -iexclude_failed_quality_control=true "
            "-iexclude_duplicate_reads=true -imin_base_qual=%s -imin_mapping_qual=%s"
        ),
    },
    "peddy": {"project_name": "-iproject_for_peddy="},
    "sompy": {
        "truth_vcf": (
            "-itruthVCF=project-ByfFPz00jy1fk6PjpZ95F27J:file-G7g9Pfj0jy1f87k1J1qqX83X"
        ),
        "query_vcf": "-iqueryVCF=",
        "tso": "-iTSO=true",
        "skip": "-iskip=false",
    },
    "ed_readcount": {
        "ref_genome": "-ireference_genome=",
        "bed": "-ibedfile=",
        "normals_rdata": "-inormals_RData=",
        "proj": "-iproject_name=",
        "pannos": "-ibamfile_pannumbers=",
    },
    "ed_cnvcalling": {
        "readcount_rdata": "RData",
        "readcount": "-ireadcount_file=",
        "bed": "-isubpanel_bed=",
        "proj": "-iproject_name=",
        "pannos": "-ibamfile_pannumbers=",
    },
    "rpkm": {
        "bed": "-ibedfile=",
        "proj": "-iproject_name=",
        "pannos": "-ibamfile_pannumbers=",
    },
    "multiqc": {
        "project_name": "-iproject_for_multiqc=",
        "coverage_level": "-icoverage_level=",
    },
    "upload_multiqc": {
        "data_input": "-imultiqc_data_input=",
        "multiqc_html": "-imultiqc_html=$jobid:multiqc_report",
    },
    "congenica_upload": {
        "vcf": "-ivcf=",
        "bam": "-ibam=",
        "samplename": "-ianalysis_name=",
    },
    "duty_csv": {
        "project_name": "-iproject_name=",
        "tso_pannumbers": "-itso_pannumbers=",
        "stg_pannumbers": "-istg_pannumbers=",
        "cp_capture_pannos": "-icp_capture_pannos=",
    },
}

UPLOAD_ARGS = {
    "dest": "--dest=",
    "proj": "--project=",
    "token": "--brief --auth %s)",
    "depends": "$depends_list",
    "depends_gatk": "$depends_list_gatk",
    # Arguments to capture jobids. Job IDS are built into a string that can be passed
    # to downstream apps to ensure the jobs don't start until those job ids have
    # completed successfully
    "depends_list": 'depends_list="${depends_list} -d ${jobid} "',
    "depends_list_gatk": 'depends_list_gatk="${depends_list_gatk} -d ${jobid} "',
    "depends_list_recombined": 'depends_list="${depends_list} ${depends_list_gatk} "',
    "depends_list_edreadcount": 'depends_list="${depends_list} -d ${ed_jobid} "',
    # Argument to define depends_list only if the job ID exists
    "if_jobid_exists_depends": 'if ! [ -z "${jobid}" ]; then %s; fi',
}

# Set 6 hour timeout policy for gatk app and jobtimeoutexceeded
# reason to auto restart list
# TODO move this to the DXAPP.JSON file for FH app
PIPE_FH_GATK_TIMEOUT_ARGS = (
    '--extra-args \'{"timeoutPolicyByExecutable": {"'
    f'{NEXUS_IDS["APPS"]["gatk"].split(":")[1]}'
    '": {"*":{"hours": 12}}}, "executionPolicy": {"restartOn": '
    '{"JobTimeoutExceeded":1, "JMInternalError":'
    ' 1, "UnresponsiveWorker": 2, "ExecutionError":1}}}\''
)

STAGE_INPUTS = {
    "pipe": {
        "fastqc_reads": f"-i{NEXUS_IDS['STAGES']['pipe']['fastqc']}.reads=",
        "bwa_reads1": f"-i{NEXUS_IDS['STAGES']['pipe']['bwa']}.reads_fastqgz=",
        "bwa_reads2": f"-i{NEXUS_IDS['STAGES']['pipe']['bwa']}.reads2_fastqgz=",
        "bwa_rg_sample": f"-i{NEXUS_IDS['STAGES']['pipe']['bwa']}.read_group_sample=",
        "bwa_ref": f"-i{NEXUS_IDS['STAGES']['pipe']['bwa']}.genomeindex_targz=",
        # HSMetrics Bedfile
        "picard_bed": (
            f"-i{NEXUS_IDS['STAGES']['pipe']['picard']}.vendor_exome_bedfile="
        ),
        "picard_capturetype": (
            f"-i{NEXUS_IDS['STAGES']['pipe']['picard']}.Capture_panel="
        ),
        "gatk_padding": (f"-i{NEXUS_IDS['STAGES']['pipe']['gatk']}.padding="),
        "gatk_vcf_format": (
            f"-i{NEXUS_IDS['STAGES']['pipe']['gatk']}.output_format=both"
        ),
        "filter_vcf_bed": f"-i{NEXUS_IDS['STAGES']['pipe']['filter_vcf']}.bedfile=",
        "happy_skip": f"-i{NEXUS_IDS['STAGES']['pipe']['happy']}.skip=",
        "happy_prefix": f"-i{NEXUS_IDS['STAGES']['pipe']['happy']}.prefix=",
        "sambamba_bed": f"-i{NEXUS_IDS['STAGES']['pipe']['sambamba']}.sambamba_bed=",
        "sambamba_min_base_qual": (
            f"-i{NEXUS_IDS['STAGES']['pipe']['sambamba']}.min_base_qual="
        ),
        "sambamba_min_mapping_qual": (
            f"-i{NEXUS_IDS['STAGES']['pipe']['sambamba']}.min_mapping_qual="
        ),
        "sambamba_cov_level": (
            f"-i{NEXUS_IDS['STAGES']['pipe']['sambamba']}.coverage_level="
        ),
        "sambamba_filter_cmds": (
            f"-i{NEXUS_IDS['STAGES']['pipe']['sambamba']}"
            ".additional_filter_commands='not (unmapped or secondary_alignment)'"
        ),
        "sambamba_excl_dups": (
            f"-i{NEXUS_IDS['STAGES']['pipe']['sambamba']}.exclude_duplicate_reads=true"
        ),
        "sambamba_excl_failed_qual": (
            f"-i{NEXUS_IDS['STAGES']['pipe']['sambamba']}"
            ".exclude_failed_quality_control=true"
        ),
        "sambamba_count_overl_mates": (
            f"-i{NEXUS_IDS['STAGES']['pipe']['sambamba']}"
            ".merge_overlapping_mate_reads=true"
        ),
        "fhprs_skip": f"-i{NEXUS_IDS['STAGES']['pipe']['fhprs']}.skip=false",
        "fhprs_bed": f"-i{NEXUS_IDS['STAGES']['pipe']['fhprs']}.BEDfile=",
        "fhprs_instance": "mem3_ssd1_v2_x8",  # Required when creating gVCFs
        "polyedge_gene": f"-i{NEXUS_IDS['STAGES']['pipe']['polyedge']}.gene=",
        "polyedge_chrom": f"-i{NEXUS_IDS['STAGES']['pipe']['polyedge']}.chrom=",
        "polyedge_poly_start": (
            f"-i{NEXUS_IDS['STAGES']['pipe']['polyedge']}.poly_start="
        ),
        "polyedge_poly_end": f"-i{NEXUS_IDS['STAGES']['pipe']['polyedge']}.poly_end=",
        "polyedge_skip": f"-i{NEXUS_IDS['STAGES']['pipe']['polyedge']}.skip=false",
    },
    "wes": {
        "fastqc1_reads": f"-i{NEXUS_IDS['STAGES']['wes']['fastqc1']}.reads=",
        "fastqc2_reads": f"-i{NEXUS_IDS['STAGES']['wes']['fastqc2']}.reads=",
        # HSmetrics bedfile
        "picard_bed": (
            f"-i{NEXUS_IDS['STAGES']['wes']['picard']}.vendor_exome_bedfile="
        ),
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

# Command strings
EMPTY_DEPENDS = "depends_list=''\n"
EMPTY_GATK_DEPENDS = "depends_list_gatk=''\n"

DX_CMDS = {
    "create_proj": str(
        'project_id="$(dx new project '
        '--bill-to %s "%s" --brief ' '--auth %s)" &&\n'
    ),
    "find_proj_name": f"source {SDK_SOURCE}; dx find projects --name *%s* --auth %s",
    "proj_name_from_id": (
        f'source {SDK_SOURCE}; dx describe %s --auth %s --json | jq -r .name'
        ),
    "find_proj_id": f'source {SDK_SOURCE}; dx describe --auth %s %s --json | jq -r .id',
    "find_execution_id": (
        f"source {SDK_SOURCE}; dx describe %s --json --auth %s | jq -r '.stages[] | "
        "select( .id == \"%s\") | .execution.id'"
        ),
    "find_data": (
        f"source {SDK_SOURCE}; dx find data --project %s --auth %s | wc -l"
        ),
    "invite_user": str(
        'invite_user_out="$(dx invite %s $project_id %s --no-email --auth %s)" &&\n'
    ),
    "file_upload_cmd": str(
        f"{UPLOAD_AGENT_EXE} --auth %s --project %s --folder /%s --do-not-compress "
        "--upload-threads 10 %s"
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
    "tso500": (
        f"jobid=$(dx run {NEXUS_IDS['APPS']['tso500']}"
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
    "ed_readcount": (
        f"ed_jobid=$(dx run {NEXUS_IDS['APPS']['ed_readcount']} "
        f"--priority high -y --instance-type mem1_ssd1_v2_x8 {JOB_NAME_STR}"
    ),
    "ed_cnvcalling": (
        f"jobid=$(dx run {NEXUS_IDS['APPS']['ed_cnvcalling']} "
        f"--priority high -y --instance-type mem1_ssd1_v2_x4 {JOB_NAME_STR}"
    ),
    "rpkm": (
        f"jobid=$(dx run {NEXUS_IDS['APPS']['rpkm']}"
        f" --priority high -y --instance-type mem1_ssd1_v2_x8 {JOB_NAME_STR}"
    ),
    "congenica_sftp": (
        f"echo 'dx run {NEXUS_IDS['APPS']['congenica_sftp']} "
        f"--priority high -y ' $analysisid ' {JOB_NAME_STR}"
    ),
    "congenica_app": (
        f"echo 'dx run {NEXUS_IDS['APPS']['congenica_app']} --priority high -y "
        f"--instance-type mem1_ssd1_v2_x2 ' $analysisid ' {JOB_NAME_STR}"
    ),
    "sompy": (
        f"jobid=$(dx run {NEXUS_IDS['APPS']['sompy']} --priority high -y {JOB_NAME_STR}"
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
        "archerdx": 5238,
        "snp": 5091,
        "tso500": 5288,
    },
    "WES_TEST_STATUS": {
        "nextseq_sequencing": 1202218804,  # Test Status = NextSEQ sequencing
        "data_processing": 1202218805,  # Test Status = Data Processing
    },
}

QUERIES = {
    "customrun": (
        "insert into NGSCustomRuns(DNAnumber,PipelineVersion, RunID) values (%s)"
        ),
    "wes": (
        "update NGSTest set PipelineVersion = %s, StatusID = %s where dna in ('%s') "
        "and StatusID = %s"
        ),
    "oncology": (
        "insert into "
        "NGSOncologyAudit(SampleID1,SampleID2,RunID,PipelineVersion,ngspanelid) "
        "values (%s)"
        ),
}
