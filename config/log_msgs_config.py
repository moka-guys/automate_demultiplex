#!/usr/bin/python3
# coding=utf-8
"""
Config file for logging module. Contains settings specific to logging. The LOG_MSGS
dictionary contains both general messages which are used across multiple modules, and
also logfile-specific messages:
- Ad_email
- Demultiplex
- ss_validator
- sw
- backup
- decision_support
"""
from config import ad_config  # Import ad_config file

# Messages used by individual scripts / modules for logging
LOG_MSGS = {
    # Generic messages used across scripts
    "general": {
        "script_start": "Automate demultiplex release: %s. Start of %s script",
        "script_end": "Automate demultiplex release %s: %s complete.",
        "runfolders_processed": "%s runfolders processed: %s",
        "executing_command": "Executing the following command: %s",
        "cmd_success": "Command executed successfully with returncode %s",
        "cmd_fail": "Command returned non-zero exit code %s. Stdout: %s. Stderr: %s",
        "testing_software": "Testing %s software",
        "test_fail": "%s test failed: Stdout: %s. Stderr: %s",
        "test_pass": "%s test passed",
        "software_fail": "Software tests did not all pass",
        "found_program": "Found program: %s",
        "program_missing": "Could not find program: %s",
        "not_dev_run": "Samplesheet is not from a development run: %s",
        "dev_run": "Samplesheet is from a development run: %s",
        "sschecks_not_passed": "Samplesheet did not pass checks: %s",
        "sschecks_passed": "Samplesheet passed all checks %s",
        "ad_version": "Automate_demultiplex release: %s",
    },
    "ad_email": {
        "sending_email": "Sending the email message: %s",
        "email_success": "Email sent successfully",
        "email_fail": "Email not sent. Exception: %s",
        "html_success": "Successfully generated email HTML",
        "html_error": (
            "There was a problem generating the html file, with "
            "the following exception: %s"
        ),
    },
    "demultiplex": {
        "runfolder_processed": "Runfolder has been processed: %s",
        "demultiplexing_required": "Demultiplexing is required for this runfolder",
        "tso_run": "TSO500 run detected.",
        "ic_fail": ("Integrity check fail. Checksums do not match for " "%s see %s"),
        "bcl2fastq_start": (
            "Demultiplexing started for run %s using bcl2fastq2 command: %s"
        ),
        "bcl2fastq_complete": "bcl2fastq2 subprocess complete for run %s",
        "bcl2fastq_failed": "bcl2fastq2 subprocess failed for run %s. Stdout: %s. Stderr: %s",
        "demux_already_complete": (
            "Demultiplexing already completed: %s. bcl2fastq2 log found @ %s"
        ),
        "demux_not_complete": (
            "Demultiplexing not yet completed: %s. No demultiplex log found @ %s"
        ),
        "run_finished": "Run finished - RTAComplete.txt found @ %s",
        "run_incomplete": (
            "Sequencing not yet complete (RTAComplete.txt file absent) @ %s"
        ),
        "ssfail_haltdemux": "Demultiplexing halted due to samplesheet errors %s: %s",
        "ic_required": (
            "This run was sequenced on a sequencer that requires integrity checking"
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
        "create_bcl2fastqlog_pass": "Created bcl2fastq2 logfile for run %s: %s",
        "create_bcl2fastqlog_fail": (
            "Failed to create bcl2fastq2 logfile for run %s. Exception: %s"
        ),
        "TSO500_run": f"%s is a {ad_config.STRINGS['demultiplexlog_tso500_msg']}",
        "write_TSO_msg_to_bcl2fastqlog": (
            "TSO500 message successfully written to bcl2fastq2_output.log file for "
            "TSO run: %s"
        ),
        "demux_complete": "Demultiplexing completed successfully for run %s",
        "demux_error": (
            "DEMULTIPLEXING UNSUCCESSFUL (BCL2FastQ2 ERROR) - Demultiplexing failed "
            "for run %s. Please see logfile %s"
        ),
        "bcl2fastqlog_empty": (
            "BCL2FASTQ2 logfile is empty for run %s. Please see logfile %s"
        ),
        "bcl2fastqlog_absent": (
            "BCL2FASTQ2 logfile does not exist for run %s. Please see logfile "
        ),
        "running_cd": (
            "Running the following command for cluster density calculation: %s"
        ),
        "cd_success": (
            "Cluster density calculation saved to "
            f"%s{ad_config.STRINGS['lane_metrics_suffix']}"
        ),
        "cd_fail": "Cluster density calculation failed for : %s. " "Error: %s",
    },
    "ss_validator": {
        "ss_present": "Samplesheet with supplied name is present (%s)",
        "ss_absent": "Samplesheet with supplied name not present (%s)",
        "ssname_valid": "Samplesheet name is valid (%s)",
        "ssname_invalid": "Samplesheet name is invalid (%s). Exception: %s",
        "sequencer_id_valid": "Sequencer ID in samplesheet name is valid",
        "sequencer_id_invalid": "Sequencer id not in allowed list (%s, %s)",
        "ss_not_empty": "Samplesheet is (>10 bytes)",
        "ss_empty": "Samplesheet empty (<10 bytes)",
        "get_data_err": "Exception raised while parsing data section: %s",
        "headers_as_expected": "Expected headers present in samplesheet",
        "headers_err": "Header(/s) missing from [Data] section: '%s'",
        "samplenames_match": "All sample names and sample IDS match",
        "nonmatching_samplenames": (
            "The following Sample IDs do not match the corresponding Sample Name: (%s)"
        ),
        "no_illegal_chars": (
            "Sample name %s contains no illegal characters in column %s"
        ),
        "illegal_chars": "Sample name contains invalid characters (%s: %s)",
        "sample_name_valid": "Sample name valid: %s (%s)",
        "sample_name_invalid": "Sample name invalid (%s). Exception: %s",
        "valid_panno": "Pan no is valid: %s",
        "invalid_panno": "Pan no is invalid: %s (%s: %s)",
        "valid_runtype": "Run type is valid: %s",
        "runtypes_err": "Runtype not in allowed list (%s, %s)",
    },
    "sw": {
        "runfolder_identified": "Identified runfolder: %s",
        "runfolder_processed": "Runfolder has been processed: %s",
        "no_users": "No users in user list for permissions level %s",
        "dxtoolkittest_pass": "dx toolkit source command successful",
        "dxtoolkittest_fail": "dx toolkit source command failed",
        "tso_backup": "Backing up TSO runfolder",
        "runfolder_prev_proc": "Runfolder already processed: %s. Skipping.",
        "runfolder_requires_proc": "Runfolder requires processing: %s",
        "ua_file_present": "Upload started file present. Terminating.",
        "ua_file_absent": "Upload started file not found. Continuing.",
        "demux_complete": "Demultiplex completed succesfully.",
        "demux_failed": "Demultiplex failed.",
        "not_yet_demultiplexed": "Demultiplex has not been performed.",
        "bcl2fastqlog_empty": "Bcl2fastq log file exists but is empty",
        "nonexistent_files": "Not all files exist: %s",
        "creating_proj": "Executing project creation script: %s",
        "proj_creation_fail": "Failed to create project in DNAnexus for %s. Stderr: %s",
        "uploading_files": "Uploading %s files",
        "upload_success": "%s files uploaded successfully",
        "upload_fail": "%s upload failed. See %s for detailed error log",
        "building_cmds": "Building dx run commands",
        "sample": "Identified %s sample: %s",
        "decision_support_upload_required": (
            "Samples in project %s require upload to decision support tool"
        ),
        "congenica_upload_required": (
            "Samples in project %s require upload to congenica"
        ),
        "qiagen_upload_required": ("Samples in project %s required upload to QCII"),
        "unrecognised_panno": (
            "Sample in samplesheet does not contain a recognised pan " "number: %s"
        ),
        "recognised_panno": (
            "Sample in samplesheet contains a recognised pan number: %s, %s"
        ),
        "fastq_identified": (
            "The following fastq has been identified in the runfolder %s "
            "as matching the following strings: %s"
        ),
        "cmds_built": "Finished building dx run commands",
        "building_cmd": "Building %s cmd for %s",
        "reference_sample": (
            "NA12878 sample detected, not building congenica upload command " "for %s"
        ),
        "writing_cmds": "Writing dx run commands",
        "running_cmds": "Running dx run commands",
        "dx_run_err": (
            "Error when setting off dx run command for run %s. "
            "Command: %s. Stdout: %s. Stderr: %s"
        ),
        "dx_run_success": "dx run commands issued successfully for run %s",
        "ss_copy_success": "Samplesheet copied to runfolder: %s",
        "ss_copy_fail": "Samplesheet not copied to runfolder",
        "uploading_rf": (
            "Uploading rest of run folder to Nexus using upload_runfolder, "
            "ignoring: %s. Stdout stored in logfile: %s"
        ),
        "upload_rf_error": (
            "An error occurred when uploading the rest of the runfolder: %s. "
            "See %s and %s for further details."
        ),
        "ss_missing": "Samplesheet is missing and is required for sample name parsing",
        "multiple_pipeline_names": (
            "Multiple pipeline names detected from panel config " "for sample list: %s"
        ),
        "wes_batch_nos_identified": "WES batch numbers %s identified",
        "wes_batch_nos_missing": (
            "WES batch numbers missing for run %s. Check for errors "
            "in the sample names"
        ),
        "library_nos_identified": "Library numbers %s identified",
        "library_no_err": (
            "%s - Unable to identify library numbers. Check "
            "for underscores in the sample names."
        ),
        "checking_fastq": "Checking fastq has been collected: %s",
        "sample_match": (
            "Fastq in the BaseCalls directory matches the sample name in "
            "the samplesheet: %s, %s"
        ),
        "sample_mismatch": (
            "Fastq in the BaseCalls directory does not match any sample name in the "
            "samplesheet: %s"
        ),
        "not_fastq": "File is not a zipped fastq: %s",
        "undetermined_identified": (
            "Undetermined file identified to exclude from processing: %s"
        ),
    },
    "backup": {
        "checking_runfolder": "Checking the runfolder exists: %s",
        "nonexistent_runfolder": "The runfolder does not exist: %s",
        "finding_project": "Searching for DNAnexus project: %s",
        "project_name": "Project name is: %s",
        "finding_project_id": (
            "Searching for DNAnexus project ID using the runfolder name %s"
        ),
        "project_id": "Project id is: %s",
        "building_command": "Building upload command",
        "added_command": "Added command to upload commands dictionary",
        "building_file_dict": "Adding the files contained within each folder to the file dictionary",
        "getting_folder_paths": (
            "Walking through the runfolder and creating a list of all folder paths within the runfolder"
        ),
        "getting_file_paths": "Walking through the folder paths and getting a list of files",
        "files_for_upload": "Files for upload: %s",
        "uploading_files": "Uploading files in folder: %s",
        "ignoring_files": "Disincluding file from upload as it contains an ignore string: %s",
        "cmd_out": "Stdout: %s. Stderr: %s",
        "files_exist": "All files in files_list exist as expected",
        "nonexistent_files": "The following files are expected to be present but do not exist: %s",
        "call_ua": "Calling upload agent on %s",
        "iterations_needed": "%s upload iterations needed to upload the files in the folder %s",
        "command_iteration": "Building command for iteration %s of %s",
        "nexus_project_subdirectory": "DNAnexus project runfolder subdirectory is: %s",
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
        "workflow_type": "Workflow is a %s workflow",
        "incorrect_workflow": "Workflow type %s does not require congenica upload",
        "setting_job_id_cmds": "Setting job ID retrieval commands",
        "setting_job_id_cmds_err": (
            "Exception encountered when setting the job ID retrieval commands: %s"
        ),
        "get_job_id": "Getting job ID for file %s",
        "found_job_id": "Found job ID for file %s: %s",
        "get_job_id_err": "Error getting job ID for file %s: %s",
        "get_job_id_fail": ("Exceeded max no. retries to retrieve job ID for file %s"),
        "setting_app_input_str": ("Setting the congenica upload app input string"),
        "app_input_str_err": (
            "Exception encountered when setting the app input string: %s"
        ),
        "printing_app_input_str": ("Printing the congenica upload app input string"),
    },
}
