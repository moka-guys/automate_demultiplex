#!/usr/bin/python3
# coding=utf-8
"""
Config file for logging module. Contains settings specific to logging
"""
import os
import datetime
import config.ad_config as ad_config  # Import ad_config file


# Timestamp used for naming log files with datetime
TIMESTAMP = str(f"{datetime.datetime.now():%Y%m%d_%H%M%S}")

if ad_config.TESTING:
    AD_LOGDIR = os.path.join(ad_config.RUNFOLDERS, "automate_demultiplexing_logfiles")
    LOGGING_FORMATTER = (
        "%(asctime)s - TEST MODE - %(name)s - %(flag)s - %(levelname)s - %(message)s"
    )
    TEST_STR = "test"
else:
    AD_LOGDIR = os.path.join(
        ad_config.DOCUMENT_ROOT, "automate_demultiplexing_logfiles"
    )
    LOGGING_FORMATTER = (
        "%(asctime)s - %(name)s - %(flag)s - %(levelname)s - %(message)s"
    )
    TEST_STR = ""

# Folders containing logfiles
LOGDIRS = {
    "demultiplex": os.path.join(AD_LOGDIR, "Demultiplexing_log_files"),
    "dx_run_cmds": os.path.join(AD_LOGDIR, "dx_run_commands"),
    "backup_runfolder": os.path.join(AD_LOGDIR, "backup_runfolder_logfiles"),
    "upload_script": os.path.join(AD_LOGDIR, "upload_agent_script_logfiles"),
    "nexus_project_creation_scripts":
        os.path.join(AD_LOGDIR, "nexus_project_creation_scripts"),
    "decision_support_script_logs":
        os.path.join(AD_LOGDIR, "decision_support_tool_logfiles"),
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
    # Records the logs from the backup runfolder script
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
    "decision_support_script_logs": os.path.join(
        LOGDIRS["decision_support_script_logs"], "decision_support_script_log_%s.log"
    )
}

# Upload and setoff workflows script logfile
SCRIPTLOG_CONFIG = {
    "usw_script": {
        "usw_script": (LOGFILES["upload_script"] % TIMESTAMP)
        },
    "demultiplex_script": {
        "demultiplex_script": (LOGFILES["demultiplex_script_logfile"] % TIMESTAMP)
        },
    "backup_runfolder_script": {
        "backup_runfolder_script": (LOGFILES["backup_runfolder"] % TIMESTAMP)
    },
}

# Flags used in log messages
LOG_FLAGS = {
    "info": f"%s{TEST_STR}_info",
    "fail": f"%s{TEST_STR}_fail",
    "ss_warning": f"%s{TEST_STR}_warning",
}

# Messages used by individual scripts / modules for logging
LOG_MSGS = {
    "ad_email": {
        "sending_email": "Sending the email message: %s",
        "email_success": "Email sent successfully",
        "email_fail": "AD_FAIL - Email not sent. Exception: %s",
        "html_success": "Successfully generated email HTML",
        "html_error": (
            "AD_FAIL - There was a problem generating the html file, with "
            "the following exception: %s"
            ),
    },
    "shared_functions": {
        "executing_command": "Executing the following command: %s",
        "cmd_success": "Command executed successfully with returncode %s",
        "cmd_fail": "Command returned non-zero exit code %s. Stdout: %s. Stderr: %s",
        "testing_software": "Testing %s software",
        "test_fail": "AD_FAIL - %s test failed",
        "test_pass": "%s test passed",
        "found_program": "Found program: %s",
        "program_missing": "Could not find program: %s",
        },
    "demultiplex": {
        "script_start": (
            "Automate demultiplex release: %s . Start of demultiplex.py script"
        ),
        "demux_script_end": (
            "Automate demultiplex release %s: Demultiplex.py complete. %s "
            "runfolders processed: %s"
        ),
        "runfolder_processed": "Runfolder has been processed: %s",
        "demultiplexing_required": ("Demultiplexing is required for this runfolder"),
        "demux_runfolder_start": (
            "Automate_demultiplex release: %s -------------- Assessing %s"
        ),
        "ic_fail": (
            "DEMUX_FAIL - Integrity check fail. Checksums do not match for " "%s see %s"
        ),
        "bcl2fastq_start": (
            "Demultiplexing started for run %s using bcl2fastq command: %s"
        ),
        "bcl2fastq_complete": "bcl2fastq subprocess complete for run %s",
        "bcl2fastq_failed": "DEMUX_FAIL - bcl2fastq subprocess failed for run %s",
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
        "ssfail_haltdemux": (
            "DEMUX_FAIL - Demultiplexing halted due to samplesheet errors %s: %s"
        ),
        "ic_required": (
            "This run was sequenced on a sequencer that requires integrity " "checking"
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
            "DEMUX_FAIL - Failed to create bcl2fastq logfile for run %s. "
            "Exception: %s"
        ),
        "TSO500_run": f"%s is a {ad_config.STRINGS['demultiplexlog_tso500_msg']}",
        "write_TSO_msg_to_bcl2fastqlog": (
            "TSO500 message successfully written to "
            "bcl2fastq2_output.log file for TSO run: %s"
        ),
        "subprocess_success": (
            "Subprocess successful for command %s with exit code %s"
        ),
        "subprocess_fail": (
            "DEMUX_FAIL - Subprocess failed for command %s with exit code %s"
        ),
        "demux_complete": "Demultiplexing completed successfully for run %s",
        "demux_error": (
            "DEMUX_FAIL - DEMULTIPLEXING UNSUCCESSFUL (BCL2FastQ2 ERROR) "
            "- Demultiplexing failed for run %s. Please see logfile %s"
        ),
        "bcl2fastqlog_empty": (
            "DEMUX_FAIL - BCL2FASTQ2 logfile is empty for run %s. "
            "Please see logfile %s"
        ),
        "bcl2fastqlog_absent": (
            "DEMUX_FAIL - BCL2FASTQ2 logfile does not exist for "
            "run %s. Please see logfile "
        ),
        "running_cd": (
            "Running the following command for cluster density calculation: %s"
        ),
        "cd_success": (
            "Cluster density calculation saved to "
            f"%s{ad_config.STRINGS['cd_file_suffix']}"
        ),
        "cd_fail": (
            "DEMUX_FAIL - Cluster density calculation failed for : %s. " "Error: %s"
        ),
    },
    "usw": {
        "script_start": (
            "Automate demultiplex release: %s . "
            "Start of upload_and_setoff_workflows.py script"
        ),
        "runfolder_identified": "Identified runfolder: %s",
        "runfolder_looping": "Looping through runfolders: %s",
        "runfolder_processed": "Runfolder has been processed: %s",
        "runfolder_not_require_processing": "Runfolder does not require processing: %s",
        "script_complete": (
            "Automate demultiplex release %s: upload_and_setoff_workflows.py "
            "complete. %s runfolders processed: %s"
        ),
        "no_users": "No users in user list for permissions level %s",
        "dxtoolkittest_pass": "dx toolkit source command successful",
        "dxtoolkittest_fail": "USW_FAIL - dx toolkit source command failed",
        "TSO_backup_attempt": "Attempting to backup TSO runfolder. Attempt %s",
        "runfolder_prev_proc": "Runfolder previously processed: %s. Skipping.",
        "runfolder_requires_proc": "Runfolder requires processing: %s",
        "ua_file_present": "Upload started file present. Terminating.",
        "ua_file_absent": "Upload started file not found. Continuing.",
        "tso_run": "TSO500 run detected.",
        "demux_complete": "Demultiplex completed succesfully.",
        "demux_failed": "Demultiplex failed.",
        "not_yet_demultiplexed": "Demultiplex has not been performed.",
        "nonexistent_files": "Not all files exist: %s",
        "creating_proj": "Executing project creation script: %s",
        "proj_creation_fail": "USW_FAIL - failed to create project in DNAnexus for %s",
        "uploading_files": "Uploading %s files",
        "upload_success": "%s files uploaded successfully",
        "upload_fail": "%s upload failed. See %s for detailed error log",
        "building_cmds": "Building dx run commands",
        "sample": "Identified %s sample: %s",
        "congenica_upload_required": (
            "Samples in project %s require upload to congenica"
        ),
        "cmds_built": "Finished building dx run commands",
        "building_cmd": "Building %s cmd for %s",
        "reference_sample": (
            "NA12878 sample detected, not building congenica upload command " "for %s"
        ),
        "writing_cmds": "Writing dx run commands",
        "running_cmds": "Running dx run commands",
        "dx_run_err": (
            "USW_FAIL - Error when setting off dx run command for run %s. "
            "Command: %s. Stderror = \n%s"
        ),
        "dx_run_success": "dx run commands issued successfully for run %s",
        "ss_copy_success": "Samplesheet copied to runfolder: %s",
        "ss_copy_fail": "Samplesheet not copied to runfolder",
        "uploading_rf": (
            "Uploading rest of run folder to Nexus using backup_runfolder, "
            "ignoring: %s. Stdout stored in logfile: %s"
        ),
        "upload_rf_error": (
            "An error occurred when uploading the rest of the runfolder: %s. "
            "See %s and %s for further details."
            ),
        "upload_rf_fail": (
            "USW_FAIL - Error in upload of rest of runfolder: %s in " "runfolder %s"
        ),
        "upload_rf_success": "Rest of runfolder %s uploaded ok",
    },
    "rf_obj": {
        "created_runfolder_obj": "Created runfolder object for %s",
        "multiple_pipeline_names": (
            "USW_FAIL - Multiple pipeline names detected from panel config "
            "for sample list: %s"
        ),
        "checking_fastq": "Checking fastq has been collected: %s",
        "undetermined_identified": (
            "Undetermined file identified to exclude from processing: %s"
        ),
        "miseq_fastq_identified": (
            "Fastq created by MiSeq identified to exclude from processing: %s"
        ),
        "unrecognised_panno": (
            "USW_FAIL - Sample in samplesheet does not contain a recognised pan "
            "number: %s"
        ),
        "recognised_panno": (
            "Sample in samplesheet contains a recognised pan number: %s, %s"
            ),
        "sample_match": (
            "Fastq in the BaseCalls directory matches the sample name in "
            "the samplesheet: %s, %s"
        ),
        "sample_mismatch": (
            "Fastq in the BaseCalls directory does not match any sample name in the "
            "samplesheet: %s"
        ),
        "not_fastq": "File is not a zipped fastq: %s",
        "library_batch_no_err": (
            "USW_FAIL '%s - Unable to identify library batch numbers. Check "
            "for underscores in the samplenames.",
        ),
    },
    "backup_runfolder": {
        "checking_runfolder": "Checking the runfolder exists: %s",
        "nonexistent_runfolder": "BR_FAIL - The runfolder does not exist: %s",
        "finding_project": "Searching for DNAnexus project: %s",
        "building_command": "Building upload command",
        "building_file_dict": "Building the dictionary of files for upload",
        "files_for_upload": "Files for upload: %s",
        "executing_command": "Executing command: %s",
        "cmd_out": "Stdout: %s. Stderr: %s",
        "call_ua": "Calling upload agent on %s to location %s",
        "uploading_file_range": "Uploading files %s to %s",
        "counting_files": (
            "Counting the number of files that need to be uploaded, have been uploaded "
            "and check if any that should have been ignored are in DNAnexus"
            ),
        "files_uploaded": (
            "%s files should have been uploaded (excluding any with ignore terms in "
            "filename or path). %s files present in DNAnexus project."
            ),
        "check_ignore": (
            "%s files present in DNAnexus project containing one of the ignore terms. "
            "NB this may not be accurate if the ignore term is found in the result of "
            "dx find data (eg present in project name)"
            ),
    },
    "decision_support": {
        "script_start": (
            "Automate demultiplex release: %s . Start of "
            "decision_support_tool_inputs.py script"
            ),
        "workflow_type": "Workflow is a %s workflow",
        "setting_job_id_cmds": "Setting job ID retrieval commands",
        "setting_job_id_cmds_err":  (
            "DST_FAIL - Exception encountered when setting the job ID retrieval "
            "commands: %s"
            ),
        "get_job_id": "Getting job ID for file %s",
        "found_job_id": "Found job ID for file %s: %s",
        "get_job_id_err": "Error getting job ID for file %s: %s",
        "get_workflow_name_err": "Error getting workflow name for analysis %s: %s",
        "get_job_id_fail": (
            "DST_FAIL - Exceeded max no. retries to retrieve job ID for file %s: %s"
            ),
        "setting_app_input_str": (
            "Setting the decision support tool upload app input string"),
        "app_input_str_err": (
            "DST_FAIL - Exception encountered when setting the app input string: %s"
            ),
        "printing_app_input_str": (
            "Printing the decision support tool upload app input string"
            ),
        "script_end": (
            "Automate demultiplex release %s: decision_support_tool_inputs.py complete."
        ),
    },
}
