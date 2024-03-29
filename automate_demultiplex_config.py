"""
Automate demultiplex configuration.

The variables defined in this module are required by the "demultiplex.py",
"upload_and_setoff_workflows.py" and "decision_support_tool_inputs.py" scripts. 
"""

import os

# Set debug mode
testing = False

# =====location of input/output files=====
# root of folder that contains the apps, automate_demultiplexing_logfiles and
# development_area scripts
# (2 levels up from this file)
document_root = "/".join(
    os.path.dirname(os.path.realpath(__file__)).split("/")[:-2]
)

# define the runfolder pattern - only check folders startiing with 6 digits.
runfolder_pattern = "^[0-9]{6}.*$"
# path to run folders - use testing flag to determine folders.
if not testing:
    runfolders = "/media/data3/share"
else:
    # when testing use a different directory
    runfolders = "/media/data3/share/testing/"

# samplesheet folder
samplesheets_dir = os.path.join(runfolders, "samplesheets")

# path to fastq files
fastq_folder = "/Data/Intensities/BaseCalls"

# bcl2fastq base command
bcl2fastq_test_cmd = "sudo docker run --rm seglh/bcl2fastq2:v2.20.0.422_25dd0c0"
bcl2fastq_cmd = (
    "sudo docker run --rm -v %s:/mnt/run -v %s:/mnt/run/%s "
    "seglh/bcl2fastq2:v2.20.0.422_25dd0c0 -R /mnt/run --sample-sheet /mnt/run/%s "
    "--no-lane-splitting >> %s 2>&1"
)

# files for checking NGS runfolders before demultiplexing
file_complete_run = "RTAComplete.txt"
file_demultiplexing = "bcl2fastq2_output.log"
file_demultiplexing_old = "demultiplexlog.txt"

# directories to be ignored when looping through runfolders
ignore_directories = ["samplesheets", "GlacierTest"]

# TSO500 runfolder is used for testing both demultiplexing and usw script
demultiplex_test_folder = [
    "999999_NB552085_0496_DEMUXINTEG",
    "999999_M02353_0496_000000000-DEMUX",
    "999999_A01229_0182_AHM2TSO500",
]

# TSO500 batch size (for splitting samplesheet)
if testing:
    batch_size = 2
else:
    batch_size = 16

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
upload_agent_path = (
    "{document_root}/apps/dnanexus-upload-agent-1.5.17-linux/ua"
).format(document_root=document_root)

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

sdk_source_cmd = "/etc/profile.d/dnanexus.environment.sh"
# command to test dx toolkit
dx_sdk_test = "source %s;dx --version" % (sdk_source_cmd)
# expected result from testing
dx_sdk_test_expected_stdout = "dx v0.2"

# command and output to test agilent connector
agilent_connector_cmd = "/opt/agilent/agilentserviceconnector status"
agilent_connector_output = "agilentserviceconnector is running"

# upload agent test response
upload_agent_expected_stdout = "Upload Agent Version:"

# NA12878 identifiers to exclude from congenica upload
reference_sample_ids = ["NA12878", "136819"]

# =====Moka settings=====
# Moka IDs for generating SQLs to update the Mokadatabase
# audit trail ID for Mokapipe & congenica
mokapipe_congenica_pipeline_ID = "5229"
# Current MokaWES ID
mokawes_pipeline_ID = "5078"
# MokaAMP ID
mokaamp_pipeline_ID = "4851"
# Archer ID
archerDx_pipeline_ID = "5238"
# MokaSNP ID
mokasnp_pipeline_ID = "5091"
# TSO500 pipeline ID
TSO_pipeline_ID = "5288" #TSO v1.6

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
# app_project = "001_ToolsReferenceData:/"
app_project = "project-ByfFPz00jy1fk6PjpZ95F27J:/"
# path to the workflow in the app project

mokapipe_path = "Workflows/GATK3.5_v2.18"
# path to the WES workflow in the app project
mokawes_path = "Workflows/MokaWES_v1.8"

# path to mokaamp
mokaamp_path = "Workflows/MokaAMP_v2.2"
# path to mokasnp
mokasnp_path = "Workflows/MokaSNP_v1.2.0"
# path to paddy app
peddy_path = "Apps/peddy_v1.5"
# path to multiqc app
multiqc_path = "Apps/multiqc_v1.18.0"
# path to congenica upload app
congenica_app_path = "Apps/congenica_upload_v1.3.2"
congenica_SFTP_upload_app = "applet-GFfJpj80jy1x1Bz1P1Bk3vQf"

# TSO500 app 
tso500_app = "applet-GZgv0Jj0jy1Yfbx3QvqyKjzp"  # Apps/TSO500_v1.6.0
tso500_app_name = "TSO500_v1.6.0"
tso500_docker_image = (
    "project-ByfFPz00jy1fk6PjpZ95F27J:file-Fz9Zyx00b5j8xKVkKv4fZ6JB"
)

sambamba_app_id = (
    "applet-G6vyyf00jy1kPkX9PJ1YkxB1"
)
sompy_app_id = (
    "applet-G9yPb780jy1p660k6yBvQg07"
)
TSO500_coverage_commands = "-imerge_overlapping_mate_reads=true -iexclude_failed_quality_control=true -iexclude_duplicate_reads=true -imin_base_qual=%s -imin_mapping_qual=%s"

# path to app which uploads multiqc report
upload_multiqc_path = "Apps/upload_multiqc_v1.4.0"
# RPKM path
RPKM_path = "Apps/RPKM_using_conifer_v1.6"

# FastQC app
fastqc_app = "Apps/fastqc_v1.4.0"
# bedfile folder
bedfile_folder = "Data/BED/"
# DNA Nexus organisation to create the project within
prod_organisation = "org-viapath_prod"


# project tags to denote live cases
live_tag = "live"

# =====istages=====
mokapipe_filter_vcf_with_bedfile_stage = "stage-G5Kpgv80zB02Q64zFf94G05F"
mokapipe_gatk_human_exome_stage = "stage-F28y4qQ0jy1fkqfy5v2b8byx"

# Mokapipe workflow inputs
mokapipe_fastqc = " -istage-Bz3YpP80jy1Y1pZKbZ35Bp0x.reads="  # FastQC Read 1
mokapipe_bwa_reads = " -istage-Byz9BJ80jy1k2VB9xVXBp0Fg.reads_fastqgz="
mokapipe_bwa_reads2 = " -istage-Byz9BJ80jy1k2VB9xVXBp0Fg.reads2_fastqgz="
mokapipe_bwa_rg_sample = (
    " -istage-Byz9BJ80jy1k2VB9xVXBp0Fg.read_group_sample="  # bwa rg samplename
)
mokapipe_bwa_ref_genome = " -istage-Byz9BJ80jy1k2VB9xVXBp0Fg.genomeindex_targz=%s"  # bwa reference genome
mokapipe_mokapicard_vendorbed_input = " -istage-F9GK4QQ0jy1qj14PPZxxq3VG.vendor_exome_bedfile="  # HSMetrics Bed file
mokapipe_mokapicard_capturetype_stage = (
    " -istage-F9GK4QQ0jy1qj14PPZxxq3VG.Capture_panel=%s"
)
mokapipe_haplotype_padding_input = (
    " -i" + mokapipe_gatk_human_exome_stage + ".padding="
)
mokapipe_haplotype_vcf_output_format = (
    " -i" + mokapipe_gatk_human_exome_stage + ".output_format=both"
)
mokapipe_filter_vcf_with_bedfile_bed_input = (
    " -i" + mokapipe_filter_vcf_with_bedfile_stage + ".bedfile="
)
mokapipe_vcf_output_name = "filtered_vcf"
mokapipe_bam_output_name = "bam"
mokapipe_happy_skip = " -istage-G8V205j0fB6QGKXQ2gZ5pB1z.skip=%s"
mokapipe_happy_prefix = " -istage-G8V205j0fB6QGKXQ2gZ5pB1z.prefix=%s"
mokapipe_sambamba_bed_input = " -istage-F35zBKQ0jy1XpfzYPZY4bgX6.sambamba_bed="
mokapipe_sambamba_min_base_qual = (
    " -istage-F35zBKQ0jy1XpfzYPZY4bgX6.min_base_qual=10"
)
mokapipe_sambamba_min_mapping_qual = (
    " -istage-F35zBKQ0jy1XpfzYPZY4bgX6.min_mapping_qual=20"
)
mokapipe_sambamba_coverage_level = (
    " -istage-F35zBKQ0jy1XpfzYPZY4bgX6.coverage_level=30"
)
mokapipe_sambamba_filter_cmds = " -istage-F35zBKQ0jy1XpfzYPZY4bgX6.additional_filter_commands='not (unmapped or secondary_alignment)'"
mokapipe_sambamba_exclude_duplicates = (
    " -istage-F35zBKQ0jy1XpfzYPZY4bgX6.exclude_duplicate_reads=true"
)
mokapipe_sambamba_exclude_failed_qual = (
    " -istage-F35zBKQ0jy1XpfzYPZY4bgX6.exclude_failed_quality_control=true"
)
mokapipe_sambamba_count_overlapping_mates = (
    " -istage-F35zBKQ0jy1XpfzYPZY4bgX6.merge_overlapping_mate_reads=true"
)
mokapipe_fhPRS_skip = " -istage-G9BfkZQ0fB6jZY7v1PfJ81F6.skip=false"
mokapipe_polyedge_stage = "stage-GK71VJ80VQgQkjvz0vyQ8YV1"
polyedge_str = (
    " -i%(stage_str)s.gene={} -i%(stage_str)s.chrom={} "
    "-i%(stage_str)s.poly_start={} -i%(stage_str)s.poly_end={} "
    "-i%(stage_str)s.skip=false" % {"stage_str": mokapipe_polyedge_stage}
)
mokapipe_fhPRS_bedfile_input = " -istage-G9BfkZQ0fB6jZY7v1PfJ81F6.BEDfile="
mokapipe_FH_humanexome_instance_type = (
    "mem3_ssd1_v2_x8"  # required when creating gVCFs
)
mokapipe_GATK_human_exome_appletID = "applet-FYZ097j0jy1ZZPx30GykP63J"
mokapipe_FH_GATK_timeout_args = (
    ' --extra-args \'{"timeoutPolicyByExecutable": {"%s": {"*":{"hours": 12}}}, "executionPolicy": {"restartOn": {"JobTimeoutExceeded":1,"JMInternalError": 1, "UnresponsiveWorker": 2, "ExecutionError":1}}}\''
    % (mokapipe_GATK_human_exome_appletID)
)  # set timeout policy of 6 hours to gatk app and add the jobtimeoutexceeded reason to the auto restart list
# Mokapipe FH_PRS BED file
FH_PRS_bedfile_name = "Pan4909.bed"

### exome depth
# exome depth readcount app
ED_readcount_path = "Apps/ED_readcount_analysis_v1.3.0"
ED_readcount_path_instance_type = "mem1_ssd1_v2_x8"
#exome depth variant calling app
ED_cnvcalling_path = "Apps/ED_cnv_calling_v1.3.0"
ED_cnvcalling_instance_type = "mem1_ssd1_v2_x4"
#VCP1 exome depth
ED_readcount_normals_VCP1_file= "project-ByfFPz00jy1fk6PjpZ95F27J:file-Gbv7Yb80v8Q40f8v140QBPQv"#"Pan5191_normals_v1.1.0.RData"
ED_VCP1_readcount_BEDfile_pannum = "Pan5191_exomedepth.bed" 
#VCP2 normals data file
ED_readcount_normals_VCP2_file="project-ByfFPz00jy1fk6PjpZ95F27J:file-Gbkgyq00ZpxpFKx03zVPJ9GX"#"Pan5188_normals_v1.1.0.RData"
ED_VCP2_readcount_BEDfile_pannum = "Pan5188_exomedepth.bed" 
#VCP3 normals data file
ED_readcount_normals_VCP3_file="project-ByfFPz00jy1fk6PjpZ95F27J:file-GbkY5v80jjgjkJqPXbgFpYzF"#"Pan5192_normals_v1.0.0.RData"
ED_VCP3_readcount_BEDfile_pannum = "Pan5192_exomedepth.bed"

exomedepth_refgenome_file = "project-ByfFPz00jy1fk6PjpZ95F27J:file-B6ZY7VG2J35Vfvpkj8y0KZ01" #hs37d5.fa.gz from 001
## readcount app inputs
exomedepth_readcount_reference_genome_input=" -ireference_genome=%s" % (exomedepth_refgenome_file)
exomedepth_readcount_bedfile_input=" -ibedfile="
exomedepth_readcount_normalsRdata_input=" -inormals_RData="
exomedepth_readcount_projectname_input=" -iproject_name="
exomedepth_readcount_pannumbers_input=" -ibamfile_pannumbers="
exomedepth_readcount_rdata_output="RData"


## ED CNV calling inputs
exomedepth_cnvcalling_reference_genome_input=" -ireference_genome=%s" % (exomedepth_refgenome_file)
exomedepth_cnvcalling_readcount_file_input=" -ireadcount_file="
exomedepth_cnvcalling_subpanel_bed_input=" -isubpanel_bed="
exomedepth_cnvcalling_projectname_input=" -iproject_name="
exomedepth_cnvcalling_pannumbers_input=" -ibamfile_pannumbers="


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

# mokasnp workflow inputs
snp_fastqc1 = " -istage-FgPp4V00YkVJVjKF4kYkBF8v.reads="  # FastQC Read 1
snp_fastqc2 = " -istage-FgPp4V00YkVJVjKF4kYkBF90.reads="  # FastQC Read 2
snp_sentieon_stage_id = "stage-FgPp4XQ0YkV48jZG4Py6F55k"
# BED file used to restrict Senteion variant calling
snp_sentieon_targets_bed = " -i%s.targets_bed=" % snp_sentieon_stage_id
# sample name for sentieon app - prevents sample being incorrectly parsed from fastq filename
snp_sentieon_samplename = " -i%s.sample=" % snp_sentieon_stage_id


# MokaAMP - stages that may change between samples/panels
mokaamp_fastq_R1_stage = " -istage-FPzGj780jy1g3p1F4F8z4J7V.reads_fastqgz="
mokaamp_fastq_R2_stage = " -istage-FPzGj780jy1g3p1F4F8z4J7V.reads2_fastqgz="
mokaamp_bwa_rg_sample = " -istage-FPzGj780jy1g3p1F4F8z4J7V.read_group_sample="
mokaamp_mokapicard_bed_stage = (
    " -istage-FPzGjV80jy1x97jg607Fg22b.vendor_exome_bedfile="
)
mokaamp_mokapicard_capturetype_stage = (
    " -istage-FPzGjV80jy1x97jg607Fg22b.Capture_panel="
)
mokaamp_ampliconfilter_BEDPE_stage = (
    " -istage-FPzGjJQ0jy1fF6505zFP6zz9.PE_BED="
)
mokaamp_chanjo_cov_level_stage = (
    " -istage-FPzGjfQ0jy1y01vG60K22qG1.coverage_level="
)
mokaamp_sambamba_bed_stage = " -istage-FPzGjfQ0jy1y01vG60K22qG1.sambamba_bed="
mokaamp_vardict_bed_stage = " -istage-G0vKZk80GfYkQx86PJGGjz9Y.bedfile="
mokaamp_vardict_samplename_stage = (
    " -istage-G0vKZk80GfYkQx86PJGGjz9Y.sample_name=vardict_"
)
mokaamp_varscan_bed_stage = " -istage-FPzGjp80jy1V3Jvb5z6xfpfZ.bed_file="
mokaamp_varscan_samplename_stage = (
    " -istage-FPzGjp80jy1V3Jvb5z6xfpfZ.samplename=varscan_"
)
mokaamp_varscan_strandfilter_stage = (
    " -istage-FPzGjp80jy1V3Jvb5z6xfpfZ.strand_filter="
)
mokaamp_mpileup_cov_level_stage = (
    " -istage-FxypXb807p1zj3g8Jv45Y54P.min_coverage="
)

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

# TSO500 stage ids
TSO500_docker_image_stage = " -iTSO500_ruo="
TSO500_samplesheet_stage = " -isamplesheet="
TSO500_analysis_options_stage = " -ianalysis_options="
TSO500_project_name_stage = " -iproject_name="
TSO500_runfolder_name_stage = " -irunfolder_name="

# app instance types
TSO500_analysis_instance_high_throughput = "mem1_ssd1_v2_x72"
TSO500_analysis_instance_low_throughput = "mem1_ssd1_v2_x36"

# RPKM inputs
rpkm_bedfile_input = " -ibedfile="
rpkm_project_input = " -iproject_name="
rpkm_bamfiles_to_download_input = " -ibamfile_pannumbers="

# email addresses
# if sending to multiple addresses provide in a list
mokaguys_email = "gst-tr.mokaguys@nhs.net"
if testing:
    # oncology email address for email alerts
    oncology_ops_email = mokaguys_email
    WES_sample_name_email_list = [mokaguys_email]
else:
    # oncology email address for email alerts
    oncology_ops_email = "m.neat@nhs.net"
    WES_sample_name_email_list = [
        "DNAdutyscientist@viapath.co.uk",
        "Suzanne.lillis@viapath.co.uk",
        mokaguys_email,
        "eblab@gstt.nhs.uk",
        "lu.liu@viapath.co.uk",
    ]


# DNA Nexus authentication token
nexus_api_key_file = "{document_root}/.dnanexus_auth_token".format(
    document_root=document_root
)
with open(nexus_api_key_file, "r") as nexus_api:
    Nexus_API_Key = nexus_api.readline().rstrip()

# list of DNA Nexus users with view access to project
view_users = ["org-viapath_prod", "InterpretationRequest"]
# list of DNA Nexus users with admin access of project
admin_users = ["mokaguys"]

# =====Decision support script
# takes an analysis id and builds inputs for the decision support upload.
decision_support_tool_input_script = "decision_support_tool_inputs.py"
mokawes_sentieon_bam_output_name = "mappings_bam"
mokawes_sentieon_bai_output_name = "mappings_bam_bai"
mokawes_sentieon_vcf_output_name = "variants_vcf"
congenica_vcf_inputname = " -ivcf="
congenica_bam_inputname = " -ibam="
congenica_samplename = " -ianalysis_name="


# ===== List of all panel numbers =====

# MokaSNP does not have R numbers as it is an identity check for the GMS SMS

# Panels for WES (analysed in Congenica), SWIFT and TSO500 (analysed in QCII), and ArcherDX (analysed in Archer
# software), are applied at the point of analysis, so R and M numbers for these are not listed below. These pan numbers
# do not necessarily refer to bed files but rather project configuration (e.g. DNAnexus instances, project layout etc.)

# If the tso pan numbers, stg pan numbers or custom panels whole capture pan
# numbers change, these must be updated in the duty_csv_inputs config

panel_list = [
    "Pan4009",  # MokaSNP
    "Pan2835",  # Twist WES
    "Pan4940",  # Twist WES for EB lab
    "Pan3174",  # WES trio
    "Pan4081",  # Swift EGFR
    "Pan4082",  # Swift 57
    "Pan4396",  # ArcherDx (Synnovis)
    "Pan5113",  # ArcherDx (BSPS)
    "Pan5115",  # ArcherDx (control)
    "Pan4969",  # TSO500 - no UTRS TERT promoter
    "Pan5085",  # TSO500 High throughput Synnovis. no UTRS TERT promoter
    "Pan5112",  # TSO500 High throughput BSPS. no UTRS TERT promoter
    "Pan5114",  # TSO500 High throughput Control. no UTRS TERT promoter
    "Pan4119",  # VCP1 Viapath R134 (FH)
    "Pan4121",  # VCP1 Viapath R184 (CF)
    "Pan4122",  # VCP1 Viapath R25 (FGFR)
    "Pan4125",  # VCP1 Viapath R73 (DMD)
    "Pan4126",  # VCP1 Viapath R337 (CADASIL)
    "Pan4974",  # VCP1 Viapath (Molecular Haemostasis) R112
    "Pan4975",  # VCP1 Viapath (Molecular Haemostasis) R115
    "Pan4976",  # VCP1 Viapath (Molecular Haemostasis) R116
    "Pan4977",  # VCP1 Viapath (Molecular Haemostasis) R117
    "Pan4978",  # VCP1 Viapath (Molecular Haemostasis) R118
    "Pan4979",  # VCP1 Viapath (Molecular Haemostasis) R119
    "Pan4980",  # VCP1 Viapath (Molecular Haemostasis) R120
    "Pan4981",  # VCP1 Viapath (Molecular Haemostasis) R121
    "Pan4982",  # VCP1 Viapath (Molecular Haemostasis) R122
    "Pan4983",  # VCP1 Viapath (Molecular Haemostasis) R123
    "Pan4984",  # VCP1 Viapath (Molecular Haemostasis) R124
    "Pan4145",  # VCP3 Viapath R79 (CMD)
    "Pan4146",  # VCP3 Viapath R81 (CM)
    "Pan4149",  # VCP2 Viapath R208 (BRCA)
    "Pan4150",  # VCP2 Viapath R207 (ovarian)
    "Pan4129",  # VCP2 Viapath R210 (lynch)
    "Pan4964",  # VCP2 Viapath R259 (nijmegen)
    "Pan4130",  # VCP2 Viapath R211 (polyposis)
    "Pan5186",  # VCP2 Viapath R414 APC
    "Pan5121",  # VCP2 Viapath R430 (prostate)
    "Pan5143",  # VCP2 Viapath R444.1 Breast cancer (PARP treatment)
    "Pan5147",  # VCP2 Viapath R444.2 Prostate cancer (PARP treatment)
    "Pan4132",  # VCP3 Viapath R56
    "Pan4134",  # VCP3 Viapath R57
    "Pan4136",  # VCP3 Viapath R58
    "Pan4137",  # VCP3 Viapath R60
    "Pan4138",  # VCP3 Viapath R62
    "Pan4143",  # VCP3 Viapath R66
    "Pan4144",  # VCP3 Viapath R78
    "Pan4151",  # VCP3 Viapath R82
    "Pan4314",  # VCP3 Viapath R229
    "Pan4351",  # VCP3 Viapath R227
    "Pan4387",  # VCP3 Viapath R90
    "Pan4390",  # VCP3 Viapath R97
    "Pan4821",  # VCP1 STG R134 FH
    "Pan4822",  # VCP1 STG R184 CF
    "Pan4823",  # VCP1 STG R25 FGFR
    "Pan4824",  # VCP1 STG R73 DMD
    "Pan4825",  # VCP1 STG R337 CADASIL
    "Pan4816",  # VCP2 STG R208 BRCA
    "Pan4817",  # VCP2 STG R207 ovarian
    "Pan4819",  # VCP2 STG R210 lynch
    "Pan4820",  # VCP2 STG R211 polyposis
    "Pan5185",  # VCP2 STG R414 APC
    "Pan5122",  # VCP2 STG R430 prostate
    "Pan5144",  # VCP2 STG R444.1 Breast cancer (PARP treatment)
    "Pan5148",  # VCP2 STG R444.2 Prostate cancer (PARP treatment)
    "Pan4826",  # VCP3 STG R56
    "Pan4827",  # VCP3 STG R57
    "Pan4828",  # VCP3 STG R58
    "Pan4829",  # VCP3 STG R60
    "Pan4830",  # VCP3 STG R62
    "Pan4831",  # VCP3 STG R66
    "Pan4832",  # VCP3 STG R78
    "Pan4833",  # VCP3 STG R79 CMD
    "Pan4834",  # VCP3 STG R81 CM
    "Pan4835",  # VCP3 STG R82 limb girdle
    "Pan4836",  # VCP3 STG R229
    "Pan5007",  # LRPCR Via R207 PMS2
    "Pan5008",  # LRPCR STG R207 PMS2
    "Pan5009",  # LRPCR Via R208 CHEK2
    "Pan5010",  # LRPCR STG R208 CHEK2
    "Pan5011",  # LRPCR Via R210 PMS2
    "Pan5012",  # LRPCR STG R210 PMS2
    "Pan5013",  # LRPCR Via R211 PMS2
    "Pan5014",  # LRPCR STG R211 PMS2
    "Pan5015",  # LRPCR Via R71 SMN1
    "Pan5016",  # LRPCR Via R239	IKBKG
    "Pan5180",  # development run - stops warning messages
]


# create lists of pan numbers for each capture panel for use with RPKM
# IMPORTANT: Lists below are used by the trend analysis scripts, if changed the trend analysis script will need to be updated
vcp1_panel_list = [
    "Pan4119",
    "Pan4121",
    "Pan4122",
    "Pan4125",
    "Pan4126",
    "Pan4821",
    "Pan4822",
    "Pan4823",
    "Pan4824",
    "Pan4825",
    "Pan4974",
    "Pan4975",
    "Pan4976",
    "Pan4977",
    "Pan4978",
    "Pan4979",
    "Pan4980",
    "Pan4981",
    "Pan4982",
    "Pan4983",
    "Pan4984",
]
vcp2_panel_list = [
    "Pan4149",
    "Pan4150",
    "Pan4129",
    "Pan4130",
    "Pan4816",
    "Pan4817",
    "Pan4819",
    "Pan4820",
    "Pan4964",
    "Pan5121",
    "Pan5122",
    "Pan5143",
    "Pan5144",
    "Pan5147",
    "Pan5148",
    "Pan5185",  
    "Pan5186",  
]
vcp3_panel_list = [
    "Pan4132",
    "Pan4134",
    "Pan4136",
    "Pan4137",
    "Pan4138",
    "Pan4143",
    "Pan4144",
    "Pan4145",
    "Pan4146",
    "Pan4151",
    "Pan4314",
    "Pan4351",
    "Pan4387",
    "Pan4390",
    "Pan4826",
    "Pan4827",
    "Pan4828",
    "Pan4829",
    "Pan4830",
    "Pan4831",
    "Pan4832",
    "Pan4833",
    "Pan4834",
    "Pan4835",
    "Pan4836",
]
WES_panel_lists = ["Pan2835", "Pan3174", "Pan4940"]
SNP_panel_lists = ["Pan4009"]
archer_panel_list = ["Pan4396", "Pan5113", "Pan5115"]
swift_57G_panel_list = ["Pan4082"]
swift_egfr_panel_list = ["Pan4081"]
LRPCR_panel_list = [
    "Pan5007",
    "Pan5008",
    "Pan5009",
    "Pan5010",
    "Pan5011",
    "Pan5012",
    "Pan5013",
    "Pan5014",
    "Pan5015",
    "Pan5016",
]
development_pannumber_list=["Pan5180"]
tso500_panel_list = [
    "Pan4969",
    "Pan5085",
    "Pan5112",
    "Pan5114",
]  


default_panel_properties = {
    "UMI": False,
    "UMI_bcl2fastq": None,  # eg Y145,I8,Y9I8,Y145
    "RPKM_bedfile_pan_number": None,
    "RPKM_also_analyse": None,  # List of Pan Numbers indicating which BAM files to download
    "mokawes": False,
    "joint_variant_calling": False,
    "mokaamp": False,
    "capture_type": "Hybridisation",  # "Amplicon" or "Hybridisation"
    "mokasnp": False,
    "mokapipe": False,
    "mokapipe_haplotype_caller_padding": 0,
    "FH": False,
    "FH_PRS_bedfile": FH_PRS_bedfile_name,
    "polyedge": False,
    "mokaamp_varscan_strandfilter": True,
    "iva_upload": False,
    "congenica_upload": True,
    "STG": False,
    "oncology": False,
    "destination_command": None,
    "congenica_credentials": "Viapath",  # "Viapath" OR "STG"
    "congenica_IR_template": "priority",  # 'priority' or 'non-priority'
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
    "mokaamp_variant_calling_bed": None,
    "congenica_project": None,
    "peddy": False,
    "archerdx": False,
    "TSO500": False,
    "TSO500_high_throughput": False,
    "drylab_dnanexus_id": None,
    "masked_reference": False,
    "exome_depth_cnvcalling_BED": False,
    "development_run":False, # used to stopunknown pan number errors but will only demultiplex
    
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
        "congenica_upload": True,
    },
    "Pan4081": {  # EGFR SWIFT Panel
        "mokaamp": True,
        "oncology": True,
        "capture_type": "Amplicon",
        "clinical_coverage_depth": 600,  # only found in mokamp command
        "multiqc_coverage_level": 100,
        "hsmetrics_bedfile": "Pan4081.bed",
        "sambamba_bedfile": "Pan4081Sambamba.bed",
    },
    "Pan4082": {  # 57G SWIFT panel
        "mokaamp": True,
        "oncology": True,
        "capture_type": "Amplicon",
        "clinical_coverage_depth": 600,  # only found in mokamp command
        "multiqc_coverage_level": 100,
        "hsmetrics_bedfile": "Pan4082.bed",
        "sambamba_bedfile": "Pan4082Sambamba.bed",
    },
    "Pan5144": {  # VCP2 R444.1 Breast cancer (PARP treatment- STG)
        "mokapipe": True,
        "multiqc_coverage_level": 30,
        "RPKM_bedfile_pan_number": "Pan5109",
        "RPKM_also_analyse": vcp2_panel_list,
        "congenica_credentials": "STG",
        "congenica_IR_template": "non-priority",
        "congenica_project": "14629",
        "hsmetrics_bedfile": "Pan5123data.bed",
        "variant_calling_bedfile": "Pan5119data.bed",
        "sambamba_bedfile": "Pan5123dataSambamba.bed",
        "exome_depth_cnvcalling_BED": "Pan5183"
    },
    "Pan5148": {  # VCP2 R444.2 Prostate cancer (PARP treatment- STG)
        "mokapipe": True,
        "multiqc_coverage_level": 30,
        "RPKM_bedfile_pan_number": "Pan5109",
        "RPKM_also_analyse": vcp2_panel_list,
        "congenica_credentials": "STG",
        "congenica_IR_template": "non-priority",
        "congenica_project": "14630",
        "hsmetrics_bedfile": "Pan5123data.bed",
        "variant_calling_bedfile": "Pan5119data.bed",
        "sambamba_bedfile": "Pan5123dataSambamba.bed",
        "exome_depth_cnvcalling_BED":  "Pan5184"
    },
    "Pan4009": {  # MokaSNP
        "mokasnp": True,
        "multiqc_coverage_level": 30,
        "variant_calling_bedfile": "Pan4009.bed",
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
        "exome_depth_cnvcalling_BED": "Pan4702"
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
        "exome_depth_cnvcalling_BED": "Pan4703"
    },
    "Pan4122": {  # VCP1 R25 FGFR Viapath
        "mokapipe": True,
        "multiqc_coverage_level": 30,
        "RPKM_bedfile_pan_number": "Pan4399",
        "congenica_project": "5291",
        "RPKM_also_analyse": vcp1_panel_list,
        "hsmetrics_bedfile": "Pan4397data.bed",
        "sambamba_bedfile": "Pan4397dataSambamba.bed",
        "variant_calling_bedfile": "Pan4398data.bed", # CNV not required
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
        "exome_depth_cnvcalling_BED": "Pan4622"
    },
    "Pan4126": {  # VCP1 R337_CADASIL Viapath
        "mokapipe": True,
        "multiqc_coverage_level": 30,
        "RPKM_bedfile_pan_number": "Pan4399",
        "congenica_project": "4865",
        "RPKM_also_analyse": vcp1_panel_list,
        "hsmetrics_bedfile": "Pan4397data.bed",
        "sambamba_bedfile": "Pan4397dataSambamba.bed",
        "variant_calling_bedfile": "Pan4398data.bed",# cnv not required
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
        "exome_depth_cnvcalling_BED": "Pan4985"
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
        "exome_depth_cnvcalling_BED":  "Pan4986"
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
        "exome_depth_cnvcalling_BED": "Pan4987"
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
        "exome_depth_cnvcalling_BED": "Pan4988"
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
        "exome_depth_cnvcalling_BED": "Pan4989"
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
        "exome_depth_cnvcalling_BED": "Pan4990"
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
        "exome_depth_cnvcalling_BED": "Pan4991"
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
        "exome_depth_cnvcalling_BED": "Pan4708"
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
        "exome_depth_cnvcalling_BED": "Pan4992"
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
        "exome_depth_cnvcalling_BED": "Pan4993"
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
        "exome_depth_cnvcalling_BED": "Pan4994"
    },
    "Pan4149": {  # VCP2 BRCA (Viapath) R208
        "mokapipe": True,
        "multiqc_coverage_level": 30,
        "RPKM_bedfile_pan_number": "Pan5109",
        "congenica_project": "4665",
        "RPKM_also_analyse": vcp2_panel_list,
        "hsmetrics_bedfile": "Pan5123data.bed",
        "sambamba_bedfile": "Pan5123dataSambamba.bed",
        "variant_calling_bedfile": "Pan5119data.bed",
        "exome_depth_cnvcalling_BED": "Pan5158"
    },
    "Pan4964": {  # VCP2 R259 nijmegen breakage (Viapath)
        "mokapipe": True,
        "multiqc_coverage_level": 30,
        "RPKM_bedfile_pan_number": "Pan5109",
        "congenica_project": "9118",
        "RPKM_also_analyse": vcp2_panel_list,
        "hsmetrics_bedfile": "Pan5123data.bed",
        "sambamba_bedfile": "Pan5123dataSambamba.bed",
        "variant_calling_bedfile": "Pan5119data.bed",
        "exome_depth_cnvcalling_BED": "Pan5161"
    },
    "Pan4150": {  # VCP2 R207 ovarian cancer (Viapath)
        "mokapipe": True,
        "multiqc_coverage_level": 30,
        "RPKM_bedfile_pan_number": "Pan5109",
        "congenica_project": "4864",
        "RPKM_also_analyse": vcp2_panel_list,
        "hsmetrics_bedfile": "Pan5123data.bed",
        "sambamba_bedfile": "Pan5123dataSambamba.bed",
        "variant_calling_bedfile": "Pan5119data.bed",
        "polyedge": "MSH2",
        "exome_depth_cnvcalling_BED": "Pan5152"
    },
    "Pan4129": {  # VCP2 R210 Lynch syndrome (Viapath)
        "mokapipe": True,
        "multiqc_coverage_level": 30,
        "RPKM_bedfile_pan_number": "Pan5109",
        "congenica_project": "5094",
        "RPKM_also_analyse": vcp2_panel_list,
        "hsmetrics_bedfile": "Pan5123data.bed",
        "sambamba_bedfile": "Pan5123dataSambamba.bed",
        "variant_calling_bedfile": "Pan5119data.bed",
        "polyedge": "MSH2",
        "exome_depth_cnvcalling_BED": "Pan5206"
    },
    "Pan4130": {  # VCP2 R211 polyposis (Viapath)
        "mokapipe": True,
        "multiqc_coverage_level": 30,
        "RPKM_bedfile_pan_number": "Pan5109",
        "congenica_project": "5095",
        "RPKM_also_analyse": vcp2_panel_list,
        "hsmetrics_bedfile": "Pan5123data.bed",
        "sambamba_bedfile": "Pan5123dataSambamba.bed",
        "variant_calling_bedfile": "Pan5119data.bed",
        "polyedge": "MSH2",
        "exome_depth_cnvcalling_BED": "Pan5193"
    },
    "Pan5186": {  # VCP2 R414 APC (Viapath)
        "mokapipe": True,
        "multiqc_coverage_level": 30,
        "RPKM_bedfile_pan_number": "Pan5109",
        "congenica_project": "5095",
        "RPKM_also_analyse": vcp2_panel_list,
        "hsmetrics_bedfile": "Pan5123data.bed",
        "sambamba_bedfile": "Pan5123dataSambamba.bed",
        "variant_calling_bedfile": "Pan5119data.bed",
        "exome_depth_cnvcalling_BED": "Pan5162"
    },
    "Pan5121": {  # VCP2 R430 prostate (Viapath)
        "mokapipe": True,
        "multiqc_coverage_level": 30,
        "RPKM_bedfile_pan_number": "Pan5109",
        "congenica_project": "12814",
        "RPKM_also_analyse": vcp2_panel_list,
        "hsmetrics_bedfile": "Pan5123data.bed",
        "sambamba_bedfile": "Pan5123dataSambamba.bed",
        "variant_calling_bedfile": "Pan5119data.bed",
        "polyedge": "MSH2",
        "exome_depth_cnvcalling_BED": "Pan5165",
    },
    "Pan5143": {  # VCP2 R444.1 Breast cancer (PARP treatment- Viapath)
        "mokapipe": True,
        "multiqc_coverage_level": 30,
        "RPKM_bedfile_pan_number": "Pan5109",
        "congenica_project": "14563",
        "RPKM_also_analyse": vcp2_panel_list,
        "hsmetrics_bedfile": "Pan5123data.bed",
        "sambamba_bedfile": "Pan5123dataSambamba.bed",
        "variant_calling_bedfile": "Pan5119data.bed",
        "exome_depth_cnvcalling_BED": "Pan5183"
    },
    "Pan5147": {  # VCP2 R444.2 Prostate cancer (PARP treatment- Viapath)
        "mokapipe": True,
        "multiqc_coverage_level": 30,
        "RPKM_bedfile_pan_number": "Pan5109",
        "congenica_project": "14564",
        "RPKM_also_analyse": vcp2_panel_list,
        "hsmetrics_bedfile": "Pan5123data.bed",
        "sambamba_bedfile": "Pan5123dataSambamba.bed",
        "variant_calling_bedfile": "Pan5119data.bed",
        "exome_depth_cnvcalling_BED":  "Pan5184",
    },
    "Pan4132": {  # VCP3 R56 (Viapath)
        "mokapipe": True,
        "multiqc_coverage_level": 30,
        "RPKM_bedfile_pan_number": "Pan4362",
        "congenica_project": "5092",
        "RPKM_also_analyse": vcp3_panel_list,
        "hsmetrics_bedfile": "Pan4995data.bed",
        "sambamba_bedfile": "Pan4995dataSambamba.bed",
        "variant_calling_bedfile": "Pan4995data.bed", # CNV not required
    },
    "Pan4134": {  # VCP3 R57 (Viapath)
        "mokapipe": True,
        "multiqc_coverage_level": 30,
        "RPKM_bedfile_pan_number": "Pan4362",
        "congenica_project": "5092",
        "RPKM_also_analyse": vcp3_panel_list,
        "hsmetrics_bedfile": "Pan4995data.bed",
        "sambamba_bedfile": "Pan4995dataSambamba.bed",
        "variant_calling_bedfile": "Pan4995data.bed", # CNV not required
    },
    "Pan4136": {  # VCP3 R58 (Viapath)
        "mokapipe": True,
        "multiqc_coverage_level": 30,
        "RPKM_bedfile_pan_number": "Pan4362",
        "congenica_project": "5092",
        "RPKM_also_analyse": vcp3_panel_list,
        "hsmetrics_bedfile": "Pan4995data.bed",
        "sambamba_bedfile": "Pan4995dataSambamba.bed",
        "variant_calling_bedfile": "Pan4995data.bed",# CNV not required
    },
    "Pan4137": {  # VCP3 R60 (Viapath)
        "mokapipe": True,
        "multiqc_coverage_level": 30,
        "RPKM_bedfile_pan_number": "Pan4362",
        "congenica_project": "5092",
        "RPKM_also_analyse": vcp3_panel_list,
        "hsmetrics_bedfile": "Pan4995data.bed",
        "sambamba_bedfile": "Pan4995dataSambamba.bed",
        "variant_calling_bedfile": "Pan4995data.bed",# CNV not required
    },
    "Pan4138": {  # VCP3 R62 (Viapath)
        "mokapipe": True,
        "multiqc_coverage_level": 30,
        "RPKM_bedfile_pan_number": "Pan4362",
        "congenica_project": "5092",
        "RPKM_also_analyse": vcp3_panel_list,
        "hsmetrics_bedfile": "Pan4995data.bed",
        "sambamba_bedfile": "Pan4995dataSambamba.bed",
        "variant_calling_bedfile": "Pan4995data.bed",# CNV not required
    },
    "Pan4143": {  # VCP3 R66 (Viapath)
        "mokapipe": True,
        "multiqc_coverage_level": 30,
        "RPKM_bedfile_pan_number": "Pan4362",
        "congenica_project": "5092",
        "RPKM_also_analyse": vcp3_panel_list,
        "hsmetrics_bedfile": "Pan4995data.bed",
        "sambamba_bedfile": "Pan4995dataSambamba.bed",
        "variant_calling_bedfile": "Pan4995data.bed",
        "exome_depth_cnvcalling_BED": "Pan5174"
    },
    "Pan4144": {  # VCP3 R78 (Viapath)
        "mokapipe": True,
        "multiqc_coverage_level": 30,
        "RPKM_bedfile_pan_number": "Pan4362",
        "congenica_project": "5092",
        "RPKM_also_analyse": vcp3_panel_list,
        "hsmetrics_bedfile": "Pan4995data.bed",
        "sambamba_bedfile": "Pan4995dataSambamba.bed",
        "variant_calling_bedfile": "Pan4995data.bed",# CNV not required
    },
    "Pan4145": {  # VCP3 R79 - CMD (Viapath)
        "mokapipe": True,
        "multiqc_coverage_level": 30,
        "RPKM_bedfile_pan_number": "Pan4362",
        "congenica_project": "4666",
        "RPKM_also_analyse": vcp3_panel_list,
        "hsmetrics_bedfile": "Pan4995data.bed",
        "sambamba_bedfile": "Pan4995dataSambamba.bed",
        "variant_calling_bedfile": "Pan4995data.bed",
        "exome_depth_cnvcalling_BED": "Pan5168"
    },
    "Pan4146": {  # VCP3 R81 CM (Viapath)
        "mokapipe": True,
        "multiqc_coverage_level": 30,
        "RPKM_bedfile_pan_number": "Pan4362",
        "congenica_project": "4666",
        "RPKM_also_analyse": vcp3_panel_list,
        "hsmetrics_bedfile": "Pan4995data.bed",
        "sambamba_bedfile": "Pan4995dataSambamba.bed",
        "variant_calling_bedfile": "Pan4995data.bed",
        "exome_depth_cnvcalling_BED": "Pan5170"
    },
    "Pan4151": {  # VCP3 R82 limb girdle (Viapath)
        "mokapipe": True,
        "multiqc_coverage_level": 30,
        "RPKM_bedfile_pan_number": "Pan4362",
        "congenica_project": "5092",
        "RPKM_also_analyse": vcp3_panel_list,
        "hsmetrics_bedfile": "Pan4995data.bed",
        "sambamba_bedfile": "Pan4995dataSambamba.bed",
        "variant_calling_bedfile": "Pan4995data.bed",# CNV not required
    },
    "Pan4351": {  # VCP3 R227 (Viapath)
        "mokapipe": True,
        "multiqc_coverage_level": 30,
        "RPKM_bedfile_pan_number": "Pan4362",
        "congenica_project": "5522",
        "RPKM_also_analyse": vcp3_panel_list,
        "hsmetrics_bedfile": "Pan4995data.bed",
        "sambamba_bedfile": "Pan4995dataSambamba.bed",
        "variant_calling_bedfile": "Pan4995data.bed",
        "exome_depth_cnvcalling_BED": "Pan5177"
    },
    "Pan4387": {  # VCP3 R90 Bleeding and platelet disorders (Viapath)
        "mokapipe": True,
        "multiqc_coverage_level": 30,
        "RPKM_bedfile_pan_number": "Pan4362",
        "congenica_project": "4699",
        "RPKM_also_analyse": vcp3_panel_list,
        "hsmetrics_bedfile": "Pan4995data.bed",
        "sambamba_bedfile": "Pan4995dataSambamba.bed",
        "variant_calling_bedfile": "Pan4995data.bed",
        "exome_depth_cnvcalling_BED": "Pan5171" 
    },
    "Pan4390": {  # VCP3 R97 Thrombophilia with a likely monogenic cause (Viapath)
        "mokapipe": True,
        "multiqc_coverage_level": 30,
        "RPKM_bedfile_pan_number": "Pan4362",
        "congenica_project": "4699",
        "RPKM_also_analyse": vcp3_panel_list,
        "hsmetrics_bedfile": "Pan4995data.bed",
        "sambamba_bedfile": "Pan4995dataSambamba.bed",
        "variant_calling_bedfile": "Pan4995data.bed",
        "exome_depth_cnvcalling_BED": "Pan5173",
    },
    "Pan4314": {  # VCP3 R229 (Viapath)
        "mokapipe": True,
        "multiqc_coverage_level": 30,
        "RPKM_bedfile_pan_number": "Pan4362",
        "congenica_project": "5290",
        "RPKM_also_analyse": vcp3_panel_list,
        "hsmetrics_bedfile": "Pan4995data.bed",
        "sambamba_bedfile": "Pan4995dataSambamba.bed",
        "variant_calling_bedfile": "Pan4995data.bed",
        "exome_depth_cnvcalling_BED": "Pan5179",
    },
    "Pan4396": {  # ArcherDx (Synnovis)
        "archerdx": True,
        "congenica_upload": False,
    },
    "Pan5113": {  # ArcherDx (BSPS)
        "archerdx": True,
        "congenica_upload": False,
    },
    "Pan5115": {  # ArcherDx (Control)
        "archerdx": True,
        "congenica_upload": False,
    },
    "Pan4969": {  # TSO500 no UTRs. TERT promoter
        "TSO500": True,
        "sambamba_bedfile": "Pan5205dataSambamba.bed",
        "clinical_coverage_depth": 100,
        "multiqc_coverage_level": 100,
        "coverage_min_basecall_qual": 25,
        "coverage_min_mapping_qual": 30,
    },
    "Pan5085": {  # TSO500 High throughput Synnovis. no UTRs. TERT promoter
        "TSO500": True,
        "TSO500_high_throughput": True,
        "sambamba_bedfile": "Pan5205dataSambamba.bed",
        "clinical_coverage_depth": 100,
        "multiqc_coverage_level": 100,
        "coverage_min_basecall_qual": 25,
        "coverage_min_mapping_qual": 30,
    },
    "Pan5112": {  # TSO500 High throughput BSPS. no UTRs. TERT promoter
        "TSO500": True,
        "TSO500_high_throughput": True,
        "sambamba_bedfile": "Pan5205dataSambamba.bed",
        "clinical_coverage_depth": 100,
        "multiqc_coverage_level": 100,
        "coverage_min_basecall_qual": 25,
        "coverage_min_mapping_qual": 30,
        "drylab_dnanexus_id": "BSPS_MD",
    },
    "Pan5114": {  # TSO500 High throughput Control. no UTRs. TERT promoter
        "TSO500": True,
        "TSO500_high_throughput": True,
        "sambamba_bedfile": "Pan5205dataSambamba.bed",
        "clinical_coverage_depth": 100,
        "multiqc_coverage_level": 100,
        "coverage_min_basecall_qual": 25,
        "coverage_min_mapping_qual": 30,
        "drylab_dnanexus_id": "BSPS_MD",
    },
    "Pan4821": {  # VCP1 STG R134_FH
        "mokapipe": True,
        "multiqc_coverage_level": 30,
        "RPKM_bedfile_pan_number": "Pan4399",
        "RPKM_also_analyse": vcp1_panel_list,
        "congenica_credentials": "STG",
        "congenica_IR_template": "non-priority",
        "congenica_project": "4203",
        "hsmetrics_bedfile": "Pan4397data.bed",
        "variant_calling_bedfile": "Pan4398data.bed",
        "sambamba_bedfile": "Pan4397dataSambamba.bed",
        "STG": True,
        "FH": True,
        "exome_depth_cnvcalling_BED": "Pan4702"
    },
    "Pan4822": {  # VCP1 STG R184_CF
        "mokapipe": True,
        "multiqc_coverage_level": 30,
        "RPKM_bedfile_pan_number": "Pan4399",
        "RPKM_also_analyse": vcp1_panel_list,
        "congenica_credentials": "STG",
        "congenica_IR_template": "non-priority",
        "congenica_project": "4203",
        "hsmetrics_bedfile": "Pan4397data.bed",
        "variant_calling_bedfile": "Pan4398data.bed",
        "sambamba_bedfile": "Pan4397dataSambamba.bed",
        "STG": True,
        "exome_depth_cnvcalling_BED": "Pan4703",
    },
    "Pan4823": {  # VCP1 STG R25_FGFR
        "mokapipe": True,
        "multiqc_coverage_level": 30,
        "RPKM_bedfile_pan_number": "Pan4399",
        "RPKM_also_analyse": vcp1_panel_list,
        "congenica_credentials": "STG",
        "congenica_IR_template": "non-priority",
        "congenica_project": "4203",
        "hsmetrics_bedfile": "Pan4397data.bed",
        "variant_calling_bedfile": "Pan4398data.bed",
        "sambamba_bedfile": "Pan4397dataSambamba.bed",
        "STG": True, # CNV not required
    },
    "Pan4824": {  # VCP1 STG R73_DMD
        "mokapipe": True,
        "multiqc_coverage_level": 30,
        "RPKM_bedfile_pan_number": "Pan4399",
        "RPKM_also_analyse": vcp1_panel_list,
        "congenica_credentials": "STG",
        "congenica_IR_template": "non-priority",
        "congenica_project": "4203",
        "hsmetrics_bedfile": "Pan4397data.bed",
        "variant_calling_bedfile": "Pan4398data.bed",
        "sambamba_bedfile": "Pan4397dataSambamba.bed",
        "STG": True,
        "exome_depth_cnvcalling_BED": "Pan4622"
    },
    "Pan4825": {  # VCP1 STG R337_cadasil
        "mokapipe": True,
        "multiqc_coverage_level": 30,
        "RPKM_bedfile_pan_number": "Pan4399",
        "RPKM_also_analyse": vcp1_panel_list,
        "congenica_credentials": "STG",
        "congenica_IR_template": "non-priority",
        "congenica_project": "4203",
        "hsmetrics_bedfile": "Pan4397data.bed",
        "variant_calling_bedfile": "Pan4398data.bed",
        "sambamba_bedfile": "Pan4397dataSambamba.bed",
        "STG": True,# CNV not required
    },
    "Pan4826": {  # VCP3 STG R56
        "mokapipe": True,
        "multiqc_coverage_level": 30,
        "RPKM_bedfile_pan_number": "Pan4362",
        "RPKM_also_analyse": vcp3_panel_list,
        "congenica_credentials": "STG",
        "congenica_IR_template": "non-priority",
        "congenica_project": "4201",
        "hsmetrics_bedfile": "Pan4995data.bed",
        "variant_calling_bedfile": "Pan4995data.bed",
        "sambamba_bedfile": "Pan4995dataSambamba.bed",# CNV not required
    },
    "Pan4827": {  # VCP3 STG R57
        "mokapipe": True,
        "multiqc_coverage_level": 30,
        "RPKM_bedfile_pan_number": "Pan4362",
        "RPKM_also_analyse": vcp3_panel_list,
        "congenica_credentials": "STG",
        "congenica_IR_template": "non-priority",
        "congenica_project": "4201",
        "hsmetrics_bedfile": "Pan4995data.bed",
        "variant_calling_bedfile": "Pan4995data.bed",
        "sambamba_bedfile": "Pan4995dataSambamba.bed",# CNV not required
    },
    "Pan4828": {  # VCP3 STG R58
        "mokapipe": True,
        "multiqc_coverage_level": 30,
        "RPKM_bedfile_pan_number": "Pan4362",
        "RPKM_also_analyse": vcp3_panel_list,
        "congenica_credentials": "STG",
        "congenica_IR_template": "non-priority",
        "congenica_project": "4201",
        "hsmetrics_bedfile": "Pan4995data.bed",
        "variant_calling_bedfile": "Pan4995data.bed",
        "sambamba_bedfile": "Pan4995dataSambamba.bed",# CNV not required
    },
    "Pan4829": {  # VCP3 STG R60
        "mokapipe": True,
        "multiqc_coverage_level": 30,
        "RPKM_bedfile_pan_number": "Pan4362",
        "RPKM_also_analyse": vcp3_panel_list,
        "congenica_credentials": "STG",
        "congenica_IR_template": "non-priority",
        "congenica_project": "4201",
        "hsmetrics_bedfile": "Pan4995data.bed",
        "variant_calling_bedfile": "Pan4995data.bed",
        "sambamba_bedfile": "Pan4995dataSambamba.bed",# CNV not required
    },
    "Pan4830": {  # VCP3 STG R62
        "mokapipe": True,
        "multiqc_coverage_level": 30,
        "RPKM_bedfile_pan_number": "Pan4362",
        "RPKM_also_analyse": vcp3_panel_list,
        "congenica_credentials": "STG",
        "congenica_IR_template": "non-priority",
        "congenica_project": "4201",
        "hsmetrics_bedfile": "Pan4995data.bed",
        "variant_calling_bedfile": "Pan4995data.bed",
        "sambamba_bedfile": "Pan4995dataSambamba.bed",# CNV not required
    },
    "Pan4831": {  # VCP3 STG R66
        "mokapipe": True,
        "multiqc_coverage_level": 30,
        "RPKM_bedfile_pan_number": "Pan4362",
        "RPKM_also_analyse": vcp3_panel_list,
        "congenica_credentials": "STG",
        "congenica_IR_template": "non-priority",
        "congenica_project": "4201",
        "hsmetrics_bedfile": "Pan4995data.bed",
        "variant_calling_bedfile": "Pan4995data.bed",
        "sambamba_bedfile": "Pan4995dataSambamba.bed",
        "exome_depth_cnvcalling_BED": "Pan5174"
    },
    "Pan4832": {  # VCP3 STG R78
        "mokapipe": True,
        "multiqc_coverage_level": 30,
        "RPKM_bedfile_pan_number": "Pan4362",
        "RPKM_also_analyse": vcp3_panel_list,
        "congenica_credentials": "STG",
        "congenica_IR_template": "non-priority",
        "congenica_project": "4201",
        "hsmetrics_bedfile": "Pan4995data.bed",
        "variant_calling_bedfile": "Pan4995data.bed",
        "sambamba_bedfile": "Pan4995dataSambamba.bed",# CNV not required
    },
    "Pan4833": {  # VCP3 STG R79
        "mokapipe": True,
        "multiqc_coverage_level": 30,
        "RPKM_bedfile_pan_number": "Pan4362",
        "RPKM_also_analyse": vcp3_panel_list,
        "congenica_credentials": "STG",
        "congenica_IR_template": "non-priority",
        "congenica_project": "4201",
        "hsmetrics_bedfile": "Pan4995data.bed",
        "variant_calling_bedfile": "Pan4995data.bed",
        "sambamba_bedfile": "Pan4995dataSambamba.bed",
        "exome_depth_cnvcalling_BED": "Pan5168",
    },
    "Pan4834": {  # VCP3 STG R81
        "mokapipe": True,
        "multiqc_coverage_level": 30,
        "RPKM_bedfile_pan_number": "Pan4362",
        "RPKM_also_analyse": vcp3_panel_list,
        "congenica_credentials": "STG",
        "congenica_IR_template": "non-priority",
        "congenica_project": "4201",
        "hsmetrics_bedfile": "Pan4995data.bed",
        "variant_calling_bedfile": "Pan4995data.bed",
        "sambamba_bedfile": "Pan4995dataSambamba.bed",
        "exome_depth_cnvcalling_BED":  "Pan5170",
    },
    "Pan4835": {  # VCP3 STG R82
        "mokapipe": True,
        "multiqc_coverage_level": 30,
        "RPKM_bedfile_pan_number": "Pan4362",
        "RPKM_also_analyse": vcp3_panel_list,
        "congenica_credentials": "STG",
        "congenica_IR_template": "non-priority",
        "congenica_project": "4201",
        "hsmetrics_bedfile": "Pan4995data.bed",
        "variant_calling_bedfile": "Pan4995data.bed",
        "sambamba_bedfile": "Pan4995dataSambamba.bed",# CNV not required
    },
    "Pan4836": {  # VCP3 STG R229
        "mokapipe": True,
        "multiqc_coverage_level": 30,
        "RPKM_bedfile_pan_number": "Pan4362",
        "RPKM_also_analyse": vcp3_panel_list,
        "congenica_credentials": "STG",
        "congenica_IR_template": "non-priority",
        "congenica_project": "4201",
        "hsmetrics_bedfile": "Pan4995data.bed",
        "variant_calling_bedfile": "Pan4995data.bed",
        "sambamba_bedfile": "Pan4995dataSambamba.bed",
        "exome_depth_cnvcalling_BED": "Pan5179"
    },
    "Pan4819": {  # VCP2 STG R210
        "mokapipe": True,
        "multiqc_coverage_level": 30,
        "RPKM_bedfile_pan_number": "Pan5109",
        "RPKM_also_analyse": vcp2_panel_list,
        "congenica_credentials": "STG",
        "congenica_IR_template": "non-priority",
        "congenica_project": "4202",
        "hsmetrics_bedfile": "Pan5123data.bed",
        "variant_calling_bedfile": "Pan5119data.bed",
        "sambamba_bedfile": "Pan5123dataSambamba.bed",
        "polyedge": "MSH2",
        "exome_depth_cnvcalling_BED": "Pan5206"
    },
    "Pan4820": {  # VCP2 STG R211
        "mokapipe": True,
        "multiqc_coverage_level": 30,
        "RPKM_bedfile_pan_number": "Pan5109",
        "RPKM_also_analyse": vcp2_panel_list,
        "congenica_credentials": "STG",
        "congenica_IR_template": "non-priority",
        "congenica_project": "4202",
        "hsmetrics_bedfile": "Pan5123data.bed",
        "variant_calling_bedfile": "Pan5119data.bed",
        "sambamba_bedfile": "Pan5123dataSambamba.bed",
        "polyedge": "MSH2",
        "exome_depth_cnvcalling_BED": "Pan5193"
    },
    "Pan5185": {  # VCP2 STG R414
        "mokapipe": True,
        "multiqc_coverage_level": 30,
        "RPKM_bedfile_pan_number": "Pan5109",
        "RPKM_also_analyse": vcp2_panel_list,
        "congenica_credentials": "STG",
        "congenica_IR_template": "non-priority",
        "congenica_project": "4202",
        "hsmetrics_bedfile": "Pan5123data.bed",
        "variant_calling_bedfile": "Pan5119data.bed",
        "sambamba_bedfile": "Pan5123dataSambamba.bed",
        "exome_depth_cnvcalling_BED": "Pan5162"
    },
    "Pan4816": {  # VCP2 STG R208
        "mokapipe": True,
        "multiqc_coverage_level": 30,
        "RPKM_bedfile_pan_number": "Pan5109",
        "RPKM_also_analyse": vcp2_panel_list,
        "congenica_credentials": "STG",
        "congenica_IR_template": "non-priority",
        "congenica_project": "12915", 
        "hsmetrics_bedfile": "Pan5123data.bed",
        "variant_calling_bedfile": "Pan5119data.bed",
        "sambamba_bedfile": "Pan5123dataSambamba.bed",
        "exome_depth_cnvcalling_BED": "Pan5158"
    },
    "Pan4817": {  # VCP2 STG R207
        "mokapipe": True,
        "multiqc_coverage_level": 30,
        "RPKM_bedfile_pan_number": "Pan5109",
        "RPKM_also_analyse": vcp2_panel_list,
        "congenica_credentials": "STG",
        "congenica_IR_template": "non-priority",
        "congenica_project": "12914", 
        "hsmetrics_bedfile": "Pan5123data.bed",
        "variant_calling_bedfile": "Pan5119data.bed",
        "sambamba_bedfile": "Pan5123dataSambamba.bed",
        "polyedge": "MSH2",
        "exome_depth_cnvcalling_BED": "Pan5152"
    },
    "Pan5122": {  # VCP2 STG R430 prostate
        "mokapipe": True,
        "multiqc_coverage_level": 30,
        "RPKM_bedfile_pan_number": "Pan5109",
        "RPKM_also_analyse": vcp2_panel_list,
        "congenica_credentials": "STG",
        "congenica_IR_template": "non-priority",
        "congenica_project": "12913",
        "hsmetrics_bedfile": "Pan5123data.bed",
        "variant_calling_bedfile": "Pan5119data.bed",
        "sambamba_bedfile": "Pan5123dataSambamba.bed",
        "polyedge": "MSH2",
        "exome_depth_cnvcalling_BED": "Pan5165"
    },
    "Pan5007": {  # LRPCR Via R207 PMS2
        "mokapipe": True,
        "multiqc_coverage_level": 30,
        "capture_type": "Amplicon",
        "congenica_IR_template": "priority",
        "congenica_project": "9986",
        "hsmetrics_bedfile": "Pan4967_reference.bed",  # LRPCR amplicon BED file
        "variant_calling_bedfile": "Pan4767data.bed",
        "sambamba_bedfile": "Pan5018dataSambamba.bed",
        "masked_reference": "project-ByfFPz00jy1fk6PjpZ95F27J:file-GF84GF00QfBfzV35Gf8Qg53q",  # hs37d5_Pan4967.bwa-index.tar.gz
    },
    "Pan5008": {  # LRPCR STG R207 PMS2
        "mokapipe": True,
        "multiqc_coverage_level": 30,
        "capture_type": "Amplicon",
        "congenica_IR_template": "non-priority",
        "congenica_project": "10010",
        "congenica_credentials": "STG",
        "hsmetrics_bedfile": "Pan4967_reference.bed",  # LRPCR amplicon BED file
        "variant_calling_bedfile": "Pan4767data.bed",
        "sambamba_bedfile": "Pan5018dataSambamba.bed",
        "masked_reference": "project-ByfFPz00jy1fk6PjpZ95F27J:file-GF84GF00QfBfzV35Gf8Qg53q",  # hs37d5_Pan4967.bwa-index.tar.gz
    },
    "Pan5011": {  # LRPCR Via R210 PMS2
        "mokapipe": True,
        "multiqc_coverage_level": 30,
        "capture_type": "Amplicon",
        "congenica_IR_template": "priority",
        "congenica_project": "9981",
        "hsmetrics_bedfile": "Pan4967_reference.bed",  # LRPCR amplicon BED file
        "variant_calling_bedfile": "Pan4767data.bed",
        "sambamba_bedfile": "Pan5018dataSambamba.bed",
        "masked_reference": "project-ByfFPz00jy1fk6PjpZ95F27J:file-GF84GF00QfBfzV35Gf8Qg53q",  # hs37d5_Pan4967.bwa-index.tar.gz
    },
    "Pan5012": {  # LRPCR STG R210 PMS2
        "mokapipe": True,
        "multiqc_coverage_level": 30,
        "capture_type": "Amplicon",
        "congenica_IR_template": "non-priority",
        "congenica_project": "10042",
        "congenica_credentials": "STG",
        "hsmetrics_bedfile": "Pan4967_reference.bed",  # LRPCR amplicon BED file
        "variant_calling_bedfile": "Pan4767data.bed",
        "sambamba_bedfile": "Pan5018dataSambamba.bed",
        "masked_reference": "project-ByfFPz00jy1fk6PjpZ95F27J:file-GF84GF00QfBfzV35Gf8Qg53q",  # hs37d5_Pan4967.bwa-index.tar.gz
    },
    "Pan5013": {  # LRPCR Via R211 PMS2
        "mokapipe": True,
        "multiqc_coverage_level": 30,
        "capture_type": "Amplicon",
        "congenica_IR_template": "priority",
        "congenica_project": "9982",
        "hsmetrics_bedfile": "Pan4967_reference.bed",  # LRPCR amplicon BED file
        "variant_calling_bedfile": "Pan4767data.bed",
        "sambamba_bedfile": "Pan5018dataSambamba.bed",
        "masked_reference": "project-ByfFPz00jy1fk6PjpZ95F27J:file-GF84GF00QfBfzV35Gf8Qg53q",  # hs37d5_Pan4967.bwa-index.tar.gz
    },
    "Pan5014": {  # LRPCR STG R211 PMS2
        "mokapipe": True,
        "multiqc_coverage_level": 30,
        "capture_type": "Amplicon",
        "congenica_IR_template": "non-priority",
        "congenica_project": "10042",
        "congenica_credentials": "STG",
        "hsmetrics_bedfile": "Pan4967_reference.bed",  # LRPCR amplicon BED file
        "variant_calling_bedfile": "Pan4767data.bed",
        "sambamba_bedfile": "Pan5018dataSambamba.bed",
        "masked_reference": "project-ByfFPz00jy1fk6PjpZ95F27J:file-GF84GF00QfBfzV35Gf8Qg53q",  # hs37d5_Pan4967.bwa-index.tar.gz
    },
    "Pan5009": {  # LRPCR Via R208 CHEK2
        "mokapipe": True,
        "multiqc_coverage_level": 30,
        "capture_type": "Amplicon",
        "congenica_IR_template": "priority",
        "congenica_project": "9984",
        "hsmetrics_bedfile": "Pan4967_reference.bed",  # LRPCR amplicon BED file
        "variant_calling_bedfile": "Pan4767data.bed",
        "sambamba_bedfile": "Pan5018dataSambamba.bed",
        "masked_reference": "project-ByfFPz00jy1fk6PjpZ95F27J:file-GF84GF00QfBfzV35Gf8Qg53q",  # hs37d5_Pan4967.bwa-index.tar.gz
    },
    "Pan5010": {  # LRPCR STG R208 CHEK2
        "mokapipe": True,
        "multiqc_coverage_level": 30,
        "capture_type": "Amplicon",
        "congenica_IR_template": "non-priority",
        "congenica_project": "10009",
        "congenica_credentials": "STG",
        "hsmetrics_bedfile": "Pan4967_reference.bed",  # LRPCR amplicon BED file
        "variant_calling_bedfile": "Pan4766data.bed",
        "sambamba_bedfile": "Pan5018dataSambamba.bed",
        "masked_reference": "project-ByfFPz00jy1fk6PjpZ95F27J:file-GF84GF00QfBfzV35Gf8Qg53q",  # hs37d5_Pan4967.bwa-index.tar.gz
    },
    "Pan5015": {  # LRPCR Via R71 SMN1
        "mokapipe": True,
        "multiqc_coverage_level": 30,
        "capture_type": "Amplicon",
        "congenica_IR_template": "non-priority",  # TODO
        "congenica_project": "9547",  # TODO
        "hsmetrics_bedfile": "Pan4967_reference.bed",  # LRPCR amplicon BED file
        "variant_calling_bedfile": "Pan4971data.bed",
        "sambamba_bedfile": "Pan5018dataSambamba.bed",
        "masked_reference": "project-ByfFPz00jy1fk6PjpZ95F27J:file-GF84GF00QfBfzV35Gf8Qg53q",  # hs37d5_Pan4967.bwa-index.tar.gz
    },
    "Pan5016": {  # LRPCR Via R239 IKBKG
        "mokapipe": True,
        "multiqc_coverage_level": 30,
        "capture_type": "Amplicon",
        "congenica_IR_template": "priority",
        "congenica_project": "9985",
        "hsmetrics_bedfile": "Pan4967_reference.bed",  # LRPCR amplicon BED file
        "variant_calling_bedfile": "Pan4768data.bed",
        "sambamba_bedfile": "Pan5018dataSambamba.bed",
        "masked_reference": "project-ByfFPz00jy1fk6PjpZ95F27J:file-GF84GF00QfBfzV35Gf8Qg53q",  # hs37d5_Pan4967.bwa-index.tar.gz
    },
    "Pan5180": {  # DEVELOPMENT run - used to allow demultiplexing, but stop samplesheet checks/incorrect pan number alerts
        "development_run": True,
    },
}


# =================turnaround time
# if a task takes more than this amount of time it is out of TAT
allowed_time_for_tasks = 4

# =================== Email server settings
username_file_path = "{document_root}/.amazon_email_username".format(
    document_root=document_root
)
with open(username_file_path, "r") as username_file:
    user = username_file.readline().rstrip()
pw_file = "{document_root}/.amazon_email_pw".format(
    document_root=document_root
)
with open(pw_file, "r") as email_password_file:
    pw = email_password_file.readline().rstrip()
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


# ================ Integrity check
# the filename which holds the checksum results
md5checksum_name = "md5checksum.txt"
# checksum complete statement
checksum_complete_flag = "Checksum result reported"
# statement to write when checksums match
checksum_match = "Checksums match"

# ================ cluster density calculation
cluster_density_success_statement = (
    "picard.illumina.CollectIlluminaLaneMetrics done"
)
cluster_density_error_statement = "PicardException"
cluster_density_file_suffix = ".illumina_lane_metrics"
phasing_metrics_file_suffix = ".illumina_phasing_metrics"
novaseq_id = "A01229"

# ================ demultiplexing
demultiplex_success_match = (
    r".*Processing completed with 0 errors and 0 warnings.$"
)
demultiplexing_log_file_TSO500_message = (
    "TSO500 run. Does not need demultiplexing locally"
)
# list of sequencers which require md5 checksums from integrity check to be assessed
sequencers_with_integrity_check = ["NB551068", "NB552085", novaseq_id]
bcl2fastq_stats_filename = "Stats.json"
bcl2fastq_stats_path = os.path.join(fastq_folder, "Stats")

polyedge_inputs = {
    "MSH2": {
        "chrom": 2,
        "poly_start": 47641559,
        "poly_end": 47641586,
    }
}

duty_csv_id = (
    "project-ByfFPz00jy1fk6PjpZ95F27J:applet-GZYx3Kj0kKj3YBV7qgK6VjXQ"
)
duty_csv_inputs = {
    # tso_pannumbers should not include the dry lab pan number
    "tso_pannumbers": "-itso_pannumbers=Pan4969,Pan5085,Pan5114",
    "stg_pannumbers": (
        "-istg_pannumbers=Pan4821,Pan4822,Pan4823,Pan4824,Pan4825,Pan4816,Pan4817,Pan4819,Pan4820,"
        "Pan4826,Pan4827,Pan4828,Pan4829,Pan4830,Pan4831,Pan4832,Pan4833,Pan4834,Pan4835,Pan4836,"
        "Pan5008,Pan5010,Pan5012,Pan5014,Pan5122,Pan5144,Pan5148"
    ),
    "cp_capture_pannos": "-icp_capture_pannos=Pan5109,Pan4399,Pan4362",
}
