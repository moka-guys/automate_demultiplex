import os
import automate_demultiplex_config as config
from DNANexus_upload_agent import process_runfolder

print test()
#TODO add tests for demultiplexing



## all functions in upload agent script
# # set up runfolder variables
# setup_variables(runfolder, now)
# # build dictionary of panel settings
# set_panel_dictionary()
# # perform upload agent test
# test_upload_agent()
# # test dx toolkit installation
# test_dx_toolkit()

# # check if already uploaded and demultiplkexing finished sucessfully
# already_uploaded() 
# demultiplex_completed_successfully():

# find_fastqs():
# # build the file path with WES batch and NGS run numbers
# capture_any_WES_batch_numbers()
# capture_library_batch_numbers()
# build_nexus_project_name()
# # create nexus project
# create_project()
# # send list to module to trigger upload
# upload_fastqs()
# # check fastqs uploaded successfully
# look_for_upload_errors_fastq()
# nexus_fastq_paths()
# nexus_bedfiles()
# start_building_dx_run_cmds()
# create_mokawes_command
# create_mokapipe_command
# create_mokaonc_command
# build_iva_input_command
# sapientia_input_command
# create_mokaamp_command
# create_rpkm_command
# create_joint_variant_calling_command
# run_sapientia_command
# run_iva_command
# add_to_depends_list
# create_multiqc_command
# run_peddy_command
# create_smartsheet_command
# smartsheet_workflows_commands_sent
# write_dx_run_cmds()
# run_dx_run_commands()
# smartsheet_workflows_commands_sent()
# write_opms_queries_mokawes()
# write_opms_queries_oncology()
# write_opms_queries_mokapipe()
# send_opms_queries()
# upload_rest_of_runfolder()
# upload_log_files()
# look_for_upload_errors()