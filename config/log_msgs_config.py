#!/usr/bin/python3
"""
Config file for logging module. Contains settings specific to logging. The LOG_MSGS dictionary contains
both general messages which are used across multiple modules, and also logfile-specific messages:
- Ad_email
- Demultiplex
- ss_validator
- sw
- backup
- decision_support
"""

# Messages used by individual scripts / modules for logging
LOG_MSGS = {
    "general": {  # General messages used across scripts
        "script_start": "Automate demultiplex release: %s. Start of %s script",
        "script_end": "Automate demultiplex release %s: %s complete",
        "runfolders_processed": "%s runfolders processed: %s",
        "executing_command": "Executing the following command: %s",
        "cmd_success": "Command executed successfully with returncode %s",
        "cmd_fail": "Command returned non-zero exit code %s. Stdout: %s. Stderr: %s",
        "testing_software": "Testing %s software",
        "test_fail": "%s test failed: Stdout: %s. Stderr: %s. Script exited",
        "test_pass": "%s test passed",
        "software_fail": "Software tests did not all pass. Script exited",
        "found_program": "Found program: %s",
        "program_missing": "Could not find program: %s. Script exited",
        "not_dev_run": "SampleSheet is not from a development run: %s",
        "dev_run": "SampleSheet is from a development run: %s",
        "sschecks_passed": "SampleSheet passed all checks %s",
        "ad_version": "Automate_demultiplex release: %s",
    },
    "ad_email": {
        "sending_email": "Sending the email message: %s",
        "email_success": "Email sent successfully",
        "email_fail": "Email not sent. Exception: %s",
        "html_success": "Successfully generated email HTML",
        "html_error": "There was a problem generating the email html file, with the following exception: %s",
    },
    "demultiplex": {
        "cmd_line_runfolder": "Runfolder %s has been supplied on the command line",
        "programmatic_runfolders": "Runfolders were gathered programmatically",
        "runfolder_names": "Runfolders identified for processing: %s",
        "runfolder_processed": "Runfolder has been processed: %s",
        "demultiplexing_required": "Demultiplexing is required for this runfolder",
        "tso_run": "TSO500 run detected",
        "bcl2fastq_start": "Demultiplexing started for run %s using bcl2fastq2 command: %s",
        "bcl2fastq_complete": "Demultiplexing compelted successfully - bcl2fastq2 subprocess complete for run %s",
        "bcl2fastq_failed": (
            "Demultiplexing failed - bcl2fastq2 subprocess failed for run %s. Stdout: %s. Stderr: %s. Script exited"
        ),
        "demux_already_complete": "Demultiplexing already completed: %s. bcl2fastq2 log found @ %s",
        "skipping_runfolder": "Skipping runfolder: %s",
        "demux_not_complete": "Demultiplexing not yet completed: %s. No demultiplex log found @ %s",
        "run_finished": "Run finished - RTAComplete.txt found @ %s",
        "run_incomplete": "Sequencing not yet complete (RTAComplete.txt file absent) @ %s",
        "ssfail_haltdemux": (
            "SampleSheet contains critical errors %s: %s. Please correct these, remove the SampleSheet check flag "
            "file, (and the checksums assessed string from the md5checksum file if the sequencer has integrity "
            "checking) to continue processing"
        ),
        "no_disallowed_ss_errs": "SampleSheet does not contain any disallowed SampleSheet errors: %s",
        "dev_run_needs_processing": "Development run %s requires processing",
        "dev_run_will_be_processed": "Development run %s will be processed by the scripts",
        "seq_with_ic": "This run was sequenced on a sequencer that requires integrity checking",
        "seq_without_ic": "This run was sequenced on a sequencer that does not require integrity checking",
        "checksumfile_present": "Checksums file present - checksums have been generated by integrity check scripts: %s",
        "checksumfile_absent": (
            "Checksums file absent - checksums not yet generated by integrity check scripts for this run: %s"
        ),
        "checksumfile_checked": "Checksum file already checked by AS for this run",
        "checksumfile_notchecked": "Checksum file not yet checked by AS for this run",
        "checksumfilecheck_start": "Data integrity checks starting...",
        "ic_pass": "Integrity check for runfolder %s passed. 'Checksums match' message present in md5checksum file: %s",
        "ic_fail": (
            "Integrity check for runfolder %s failed. 'Checksums do not match' message present in md5checksum file: %s"
        ),
        "unexpected_checksumfile_contents": (
            "Contents of the md5checksum file are unexpected for this runfolder %s. See: %s"
        ),
        "create_bcl2fastqlog_pass": "Created bcl2fastq2 logfile for run %s: %s",
        "create_bcl2fastqlog_fail": "Failed to create bcl2fastq2 logfile for run %s. Exception: %s. Script exited",
        "tso500_run": "%s is a %s",
        "write_tso_msg_to_bcl2fastqlog": (
            "TSO500 message successfully written to bcl2fastq2_output.log file for TSO run: %s"
        ),
        "bcl2fastqlog_empty": "BCL2FASTQ2 logfile is empty for run %s. Please see logfile %s",
        "bcl2fastqlog_absent": "BCL2FASTQ2 logfile does not exist for run %s. Please see logfile",
        "running_cd": "Running the following command for cluster density calculation: %s",
        "cd_success": "Cluster density calculation saved to %s%s",
        "cd_fail": "Cluster density calculation failed for: %s. Error: %s. Script exited",
        "fastq_valid": "Gzip --test determined that the fastq is valid: %s",
        "fastq_invalid": "Gzip --test determined that the fastq is not valid: %s. Stdout: %s. Stderr: %s",
    },
    "sw": {
        "runfolder_identified": "Identified runfolder: %s",
        "runfolder_processed": "Runfolder has been processed: %s",
        "no_users": "No users in user list for permissions level %s",
        "tso_backup": "Backing up TSO runfolder",
        "runfolder_prev_proc": "Runfolder already processed: %s. Skipping",
        "runfolder_requires_proc": "Runfolder requires processing: %s",
        "start_runfolder_proc": "Starting runfolder processing for: %s",
        "ua_file_present": "Upload started file present. Terminating",
        "ua_file_absent": "Upload started file not found. Continuing",
        "demux_complete": "Run has been previously successfully demultiplexed",
        "success_string_absent": "Run has previously been demultiplexed but no success string is present",
        "not_yet_demultiplexed": "Demultiplexing has not been performed",
        "bcl2fastqlog_empty": "Bcl2fastq log file exists but is empty",
        "nonexistent_files": "Not all files exist: %s",
        "view_users": "Users identifed that require VIEW project permissions: %s",
        "admin_users": "Users identifed that require ADMINISTER project permissions: %s",
        "creating_proj": "Executing project creation script: %s",
        "proj_creation_fail": "Failed to create project in DNAnexus for %s. Stderr: %s. Script exited",
        "uploading_files": "Uploading %s files",
        "upload_success": "%s files uploaded successfully",
        "upload_fail": "%s upload failed. See %s for detailed error log",
        "building_cmds": "Building dx run commands",
        "sample_identified": "Identified %s sample: %s",
        "splitting_tso_samplesheet": "Splitting SampleSheet for TSO run into batches containing %s samples each: %s",
        "tso_batches_count": "Creating %s SampleSheets",
        "decision_support_upload_required": "Sample %s requires upload to decision support tool",
        "decision_support_upload_notrequired": "Sample %s is a control so does not require decision support upload",
        "congenica_upload_required": "Sample %s requires upload to Congenica",
        "qiagen_upload_required": "Sample %s requires upload to QCII",
        "unrecognised_panno": "Sample in SampleSheet does not contain a recognised pan number: %s. Script exited",
        "recognised_panno": "Sample in SampleSheet contains a recognised pan number: %s, %s",
        "fastq_identified": (
            "The following fastq has been identified in the runfolder %s as matching the following strings: %s"
        ),
        "fastq_nonexistent": "No fastq could be intentified that matches the following strings: %s. Error: %s",
        "sample_excluded": "Sample excluded from samples dictionary due to missing fastqs: %s",
        "cmds_built": "Finished building dx run commands",
        "building_cmd": "Building %s cmd for %s",
        "insufficient_samples_for_cnv": (
            "Less than 3 samples detected for run %s for %s - CNV calling cannot be conducted"
        ),
        "pos_control": "Positive control sample detected: %s",
        "neg_control": "Negative control sample detected: %s",
        "writing_cmds": "Writing dx run commands to %s",
        "running_cmds": "Running dx run commands using dx run bash script",
        "dx_run_err": "Error when setting off dx run command for run %s. Command: %s. Stdout: %s. Stderr: %s",
        "dx_run_success": "dx run commands issued successfully for run %s",
        "ss_copy_success": "SampleSheet copied to runfolder: %s",
        "ss_copy_fail": "SampleSheet not copied to runfolder",
        "uploading_rf": (
            "Uploading rest of run folder to DNAnexus using upload_runfolder, "
            "ignoring: %s. Stdout stored in logfile: %s"
        ),
        "upload_rf_error": (
            "An error occurred when uploading the rest of the runfolder: %s. See %s and %s "
            "for further details. Script exited"
        ),
        "ss_missing": "SampleSheet is missing and is required for sample name parsing",
        "multiple_pipeline_names": (
            "Multiple pipeline names detected from panel config for sample list: %s. Scripts do not support different "
            "pipelines for the same run. Supported pipelines: %s"
        ),
        "pipeline_name": "Pipeline name identified as %s",
        "runtype_str": "Runtype name string created: %s",
        "wes_batch_nos_identified": "WES batch numbers %s identified",
        "wes_batch_nos_missing": (
            "WES batch numbers missing for run %s. Check for errors in the sample names. Script exited"
        ),
        "library_nos_identified": "Library numbers %s identified",
        "library_no_err": (
            "%s - Unable to identify library numbers. Check for underscores in the sample names. Script exited"
        ),
        "checking_fastq": "Checking fastq has been collected: %s",
        "sample_match": "Fastq in the BaseCalls directory matches the sample name in the SampleSheet: %s, %s",
        "sample_mismatch": "Fastq in the BaseCalls directory does not match any sample name in the SampleSheet: %s",
        "fastq_wrong_naming": (
            "The fastq has the wrong naming format and is being excluded from processing: %s. Exception: %s"
        ),
        "add_missing_sample": "Adding missing sample to the samples dictionary: %s",
        "undetermined_exists": "Undetermined fastq exists: %s",
        "undetermined_missing": "Undetermined fastq is missing: %s",
        "not_fastq": "File is not a zipped fastq: %s",
        "undetermined_identified": "Undetermined file identified to exclude from processing: %s",
    },
    "backup": {
        "checking_runfolder": "Checking the runfolder exists: %s",
        "nonexistent_runfolder": "The runfolder does not exist: %s. Script exited",
        "finding_project": "Searching for DNAnexus project: %s",
        "project_name": "Project name is: %s",
        "finding_project_id": "Searching for DNAnexus project ID using the runfolder name %s",
        "project_id": "Project ID is: %s",
        "proj_id_err": "Exception encountered whilst finding the project ID: %s",
        "building_command": "Building upload command",
        "added_command": "Added command to upload commands dictionary",
        "building_file_dict": "Adding the files contained within each folder to the file dictionary",
        "getting_folder_paths": (
            "Walking through the runfolder and creating a list of all folder paths within the runfolder"
        ),
        "getting_file_paths": "Walking through the folder paths and getting a list of files",
        "files_for_upload": "Files for upload: %s",
        "uploading_files": "Uploading files in folder: %s",
        "ignoring_files": "Excluding file from upload as it contains an ignore string (%s): %s",
        "files_exist": "All files in files_list exist as expected",
        "nonexistent_files": "The following files are expected to be present but do not exist: %s",
        "call_ua": "Calling upload agent on: %s",
        "upload_attempt": "Upload attempt %s",
        "iterations_needed": "%s upload iterations needed to upload the files in the folder %s",
        "command_iteration": "Building command for iteration %s of %s",
        "nexus_project_subdirectory": "DNAnexus project runfolder subdirectory is: %s",
        "counting_files": (
            "Counting the number of files that need to be uploaded have been uploaded, "
            "and check if any that should have been ignored are in DNAnexus"
        ),
        "files_uploaded": (
            "%s files should have been uploaded (excluding any with ignore terms in filename or path). %s files "
            "present in DNAnexus project that were uploaded by the automated scripts (contain the tag 'as_upload')"
        ),
        "check_ignore": (
            "%s files present in DNAnexus project containing one of the ignore terms. NB this may not be accurate if "
            "the ignore term is found in the result of dx find data (eg present in project name)"
        ),
    },
}
