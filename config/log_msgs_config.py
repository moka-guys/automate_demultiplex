"""
Config file for logging module. Contains settings specific to logging. The LOG_MSGS dictionary contains
both general messages which are used across multiple modules, and also logfile-specific messages:
- Ad_email
- Demultiplex
- ss_validator
- sw
- backup
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
        "runtype": "Run has been identified as a %s run: %s",
        "ad_version": "Automate_demultiplex release: %s",
        "pipeline_name": "Pipeline name identified as %s",
        "runtype_str": "Runtype name string created: %s",
        "library_nos_identified": "Library numbers %s identified",
        "unrecognised_panno": "Sample in SampleSheet does not contain a recognised pan number: %s. Script exited",
        "recognised_panno": "Sample in SampleSheet contains a recognised pan number: %s, %s",
        "sample_identified": "Identified %s sample: %s",
        "fastq_identified": (
            "The following fastq has been identified in the runfolder %s as matching the following strings: %s"
        ),
        "fastq_nonexistent": "No fastq could be intentified that matches the following strings: %s. Error: %s",
        "sample_excluded": "Sample excluded from samples dictionary due to missing fastqs: %s",
        "control_sample": "%s control sample detected: %s",
        "missing_panno": "Could not identify pan number from the sample name in the sample sheet: %s",
        "multiple_pipeline_names": (
            "Multiple pipeline names detected from panel config for sample list: %s. Scripts do not support different "
            "pipelines for the same run. Supported pipelines: %s"
        ),
        "ss_missing": "SampleSheet is missing and is required for sample name parsing",
        "fastq_valid": "Gzip testing determined that the fastq is valid: %s",
        "fastq_invalid": "Gzip testing determined that the fastq is not valid: %s. Error: %s",
        "demux_success": "Demultiplexing was successful for the run with all fastqs valid",
        "wes_batch_nos_identified": "WES batch numbers %s identified",
        "wes_batch_nos_missing": "WES batch numbers missing. Check for errors in the sample names. Script exited",
    },
    "ad_email": {
        "sending_email": "Sending the email message: %s",
        "email_success": "Email sent successfully",
        "email_fail": "Email not sent. Exception: %s",
        "html_success": "Successfully generated email HTML",
        "html_error": "There was a problem generating the email html file, with the following exception: %s",
    },
    "demux": {
        "previous_ss_check_fail": (
            "Previous SampleSheet check (both attempts) identified errors. "
            "Remove the flag files (at least sscheck_flagfile.txt) to re-process: %s"),
        "ss_check_required": "Samplesheet check not yet conducted",
        "ss_validator_version": "Calling samplesheet_validator v%s",
        "sschecks_passed": "SampleSheet passed in %s all checks %s",
        "sschecks_failed": (
            "SampleSheet check for %s failed with the following errors: %s. You may wait for the 2nd attempt check "
            "if it is initial check or please correct these, remove the "
            "SampleSheet check flag file(s), (and the checksums assessed string from the md5checksum file "
            "if present) to continue processing"
        ),
        "dev_umis_upload_flagfile": "Created upload flag file for development runs with UMIs: %s",
        "sscheck_success_msg_present": "The %s file contains success message",
        "sscheckfile_absent": "The %s is absent",
        "sscheck_success_msg_absent": "%s does not contain success message",
        "cmd_line_runfolder": "Runfolder %s has been supplied on the command line",
        "programmatic_runfolders": "Runfolders were gathered programmatically",
        "runfolder_names": "Runfolders identified for processing: %s",
        "script_success": "Runfolder has been successfully processed by the demultiplex script: %s",
        "demultiplexing_required": "Demultiplexing is required for this runfolder",
        "demultiplexing_start": "Demultiplexing started using the following command: %s",
        "demultiplexing_complete": "Demultiplexing completed successfully for %s",
        "demultiplexing_failed": "Demultiplexing failed - demultiplexing subprocess failed. Script exited. Stdout: %s. Stderr: %s",
        "demux_already_complete": "Demultiplexing already completed. Demultiplexing log found @ %s",
        "skipping_runfolder": "Upload flagfile present denoting runfolder has been uploaded - skipping runfolder: %s",
        "demux_not_complete": "Demultiplexing not yet completed. No demultiplex log found @ %s",
        "run_finished": "Run finished - Run copy completion file has been found @ %s",
        "run_incomplete": "Sequencing not yet complete (Run copy completion file absent) @ %s",
        "aviti_run_failed": "AVITI run has failed sequencing. Run Completion file has OutcomeFailed or OutcomeStopped - %s",
        "seq_with_ic": "This run was sequenced on a sequencer that requires integrity checking",
        "seq_without_ic": "This run was sequenced on a sequencer that does not require integrity checking",
        "checksumfile_present": "Checksums file present - checksums have been generated by integrity check scripts: %s",
        "checksumfile_absent": "Checksums file absent - checksums not yet generated by integrity check scripts for this run: %s",
        "checksumfile_checked": "Checksum file already checked by AS for this run",
        "checksumfile_notchecked": "Checksum file not yet checked by AS for this run",
        "checksumfilecheck_start": "Data integrity checks starting...",
        "ic_pass": "Integrity check passed. 'Checksums match' message present in md5checksum file: %s",
        "ic_fail": "Integrity check failed. 'Checksums do not match' message present in md5checksum file: %s",
        "unexpected_checksumfile_contents": "Contents of the md5checksum file are unexpected. See: %s",
        "create_demultiplexlog_pass": "Created demultiplex logfile: %s",
        "create_demultiplexlog_fail": "Failed to create demultiplex logfile. Script exited. Exception: %s",
        "demux_not_required": "Runfolder is a %s",
        "dev_run_umis": "Development run requires manual processing as it contains UMIs",
        "tso_run": "TSO run identified",
        "write_msg_to_demuxlogfile": "Message successfully written to demultiplex output log file: %s",
        "bclconvertlog_empty": "BCLCONVERT logfile is empty for run %s. Please see logfile %s",
        "running_cd": "Running the following command for cluster density calculation: %s",
        "cd_success": "Cluster density calculation saved to %s",
        "cd_fail": "Cluster density calculation failed. Error: %s. Script exited",
        "file_copy_success": "File successfully copied from %s to %s",
        "file_copy_fail": "Could not copy file - file does not exist: %s",
        "re_demultiplex": "Invalid fastqs were identified. Demultiplex log has been removed to trigger re-demultiplex",
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
        "demux_complete": "Run has been previously successfully processed by the demultiplexing script",
        "success_string_absent": "Run has previously been demultiplexed but no success string is present",
        "not_yet_demultiplexed": "Demultiplexing has not been performed",
        "demultiplexlog_empty": "Demultiplex log file exists but is empty",
        "nonexistent_files": "Not all files exist: %s",
        "view_users": "Users identifed that require VIEW project permissions: %s",
        "admin_users": "Users identifed that require ADMINISTER project permissions: %s",
        "creating_proj": "Executing project creation script: %s",
        "proj_creation_fail": "Failed to create project in DNAnexus for %s. Stderr: %s. Script exited",
        "proj_id_empty": "Project creation script completed successfully but returned empty project ID. Please ensure API key is valid",
        "uploading_files": "Uploading %s files",
        "upload_success": "%s files uploaded successfully",
        "upload_fail": "%s upload failed. See %s for detailed error log",
        "building_cmds": "Building dx run commands",
        "splitting_tso_samplesheet": "Splitting SampleSheet for TSO run into batches containing %s samples each: %s",
        "tso_batches_count": "Creating %s SampleSheets",
        "decision_support_upload_required": "Sample %s requires upload to decision support tool",
        "decision_support_upload_notrequired": "Sample %s is a control so does not require decision support upload",
        "cmds_built": "Finished building dx run commands",
        "building_cmd": "Building %s cmd for %s",
        "insufficient_samples_for_cnv": (
            "Less than 3 samples detected for %s - CNV calling cannot be conducted"
        ),
        "writing_cmds": "Writing dx run commands to %s",
        "running_cmds": "Running dx run commands using dx run bash script",
        "running_decision_cmds": "Running decision support commands using bash script",
        "dx_run_err": "Error when setting off dx run command. Command: %s. Stdout: %s. Stderr: %s",
        "decision_run_err": "Error when setting off decision support command. Command: %s. Stdout: %s. Stderr: %s",
        "dx_run_success": "Dx run commands issued successfully for run %s",
        "decision_run_success": "Decision support cmd is run successfully for run %s",    
        "uploading_rf": (
            "Uploading rest of run folder to DNAnexus using upload_runfolder, ignoring: %s. Stdout stored in logfile: %s"
        ),
        "upload_rf_error": (
            "An error occurred when uploading the rest of the runfolder: %s. See %s and %s for further details. Script exited"
        ),
        "library_no_err": "Unable to identify library numbers. Script exited. Check for underscores in the sample names.",
        "checking_fastq": "Checking fastq has been collected: %s",
        "sample_match": "Fastq in the BaseCalls directory matches the sample name in the SampleSheet: %s, %s",
        "sample_mismatch": "Fastq in the BaseCalls directory does not match any sample name in the SampleSheet: %s",
        "fastq_wrong_naming": "The fastq has the wrong naming format and is being excluded from processing: %s. Exception: %s",
        "add_missing_sample": "Adding missing sample to the samples dictionary: %s",
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
        "getting_folder_paths": "Walking through the runfolder and creating a list of all folder paths within the runfolder",
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
