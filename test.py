import os
import re
import subprocess
import datetime
import smtplib
from email.message import Message
from shutil import copyfile
import requests
# import config file
import automate_demultiplex_config as config
# import function which reads the git tag
import git_tag as git_tag
from upload_and_setoff_workflows import process_runfolder,runfolder_object


#TODO add tests for demultiplexing



class test_process_runfolder():
    def __init__(self,):
        self.runfolder=""

    def run_tests(self):
        self.test_runfolder_object()
        self.test_set_panel_dictionary()
        self.test_perform_test()
        self.test_find_fastqs()
        self.test_capture_any_WES_batch_numbers()
        self.test_capture_library_batch_numbers()
        self.test_build_nexus_project_name()
        self.test_write_create_project_script()

    def test_runfolder_object(self):
        test_runfolder_obj = runfolder_object("abc123")
        assert len(vars(test_runfolder_obj)) == 6
        assert test_runfolder_obj.runfolder_name == "abc123"
        assert config.runfolders in test_runfolder_obj.fastq_folder_path  and "abc123" in test_runfolder_obj.fastq_folder_path  and config.fastq_folder in test_runfolder_obj.fastq_folder_path 
        print "runfolder class tested"

    def test_set_panel_dictionary(self):
        """
        set_panel_dictionary builds a dictionary where each key is a pannumber and the value is a dictionary of settings.
        At first for each panel a dictionary of default settings is built (from config file) 
        Defaults are overwritten where appropriate (using config.panel_settings)
        This function asserts:
         - There are the correct number of settings for each panel 
         - If default settings are correct 
         - If defaults have been overwritten
         - If allpanels are present
        """
        test_instance = process_runfolder("abc123", str(datetime.datetime.now()),True)
        
        panel_dictionary = test_instance.set_panel_dictionary()
        for panel in panel_dictionary:
            assert len(panel_dictionary[panel].keys()) == len(config.default_panel_properties)
        # test default setting
        assert not panel_dictionary["Pan2684"]["peddy"]
        # test non-default setting
        assert panel_dictionary["Pan2684"]["capture_type"] == "Amplicon"
        # check all pannumbers are present
        assert len(panel_dictionary.keys()) == len(config.panel_list)
        print "panel_dictionary tested"
    

    def test_perform_test(self):
        """
        perform_test takes a stdout and tool name and returns False if expected string (as per config file) not in stdout
        """
        test_instance = process_runfolder("abc123",str(datetime.datetime.now()),True)
        # upload agent expect to pass
        assert test_instance.perform_test(config.upload_agent_expected_stdout,"ua")
        # upload agent expect to fail
        assert not test_instance.perform_test(config.dx_sdk_test_expected_stdout,"ua")
        # dx toolkit expect to pass
        assert test_instance.perform_test(config.dx_sdk_test_expected_stdout,"dx_toolkit")
        # dx toolkit expect to fail
        assert not test_instance.perform_test(config.upload_agent_expected_stdout,"dx_toolkit")
        # demultiplex_success expect to pass
        assert test_instance.perform_test(config.demultiplex_success_string,"demultiplex_success")
        # demultiplex_success  expect to fail
        assert not test_instance.perform_test(config.upload_agent_expected_stdout,"demultiplex_success")
        
        # Now check for presencse/absence of files
        real_file_path = os.path.realpath(__file__)
        fake_file_path = os.path.join(os.path.dirname(os.path.realpath(__file__)),"nowaythisfilecanexist.txt")
        # check for presence of file demultiplex_started - expect pass
        assert test_instance.perform_test(real_file_path,"demultiplex_started")
        # check for presence of file demultiplex_started - expect fail
        assert not test_instance.perform_test(fake_file_path,"demultiplex_started")
        # check for presence of file already_uploaded - expect pass
        assert test_instance.perform_test(real_file_path,"already_uploaded")
        # check for presence of file already_uploaded - expect fail
        assert not test_instance.perform_test(fake_file_path,"already_uploaded")

        print "test_perform_test tested"
    
    def test_find_fastqs(self):
        
        # create runfolder object
        test_instance = process_runfolder("999999_NB552085_9999_automated_tests",str(datetime.datetime.now()),True)
        list_of_processed_samples, fastq_string, not_processed = test_instance.find_fastqs(test_instance.runfolder_obj.fastq_folder_path)
        
        # check undertermined sample hasn't been included to be processed
        assert "Undetermined" not in list_of_processed_samples
        # check all pan numbers in 
        for fastq in list_of_processed_samples:
            assert  "Pan" + fastq.split("_Pan")[1].split("_")[0] in config.panel_list
        assert len(list_of_processed_samples) == 10 
        # len of fastq string is one more because it starts with an extra space
        assert len(fastq_string.split(" ")) == len(list_of_processed_samples) + 1
        for fastq in not_processed:
            assert  "Pan" + fastq.split("_Pan")[1].split("_")[0] not in config.panel_list
        #print list_of_processed_samples
        print "find_fastqs tested"

        
    def test_capture_any_WES_batch_numbers(self):
        # create runfolder object
        test_instance = process_runfolder("999999_NB552085_9999_automated_tests",str(datetime.datetime.now()),True)
        list_of_fastqs = ['ONC151_02_EK6418_1837319_SWIFT5_Pan1190_S2_L001_R1_001.fastq.gz', 'NGS292_32_224051_AB_F_NGSEQ1cys_Pan1965_S32_R1_001.fastq.gz', 'NGS292_04_223687_SO_F_BRCAv2_Pan1449_S4_R2_001.fastq.gz', 'NGS292_32_224051_AB_F_NGSEQ1cys_Pan1965_S32_R2_001.fastq.gz', 'ONC151_01_NTCcon_SWIFT5_Pan1190_S1_R1_001.fastq.gz', 'TEST275F_60_216178_SC_M_WES44_Pan493_S1_R2_001.fastq.gz', 'ONC151_01_NTCcon_SWIFT5_Pan1190_S1_R2_001.fastq.gz', 'NGS292_04_223687_SO_F_BRCAv2_Pan1449_S4_R1_001.fastq.gz', 'ONC151_02_EK6418_1837319_SWIFT5_Pan1190_S2_L001_R2_001.fastq.gz', 'TEST275F_60_216178_SC_M_WES44_Pan493_S1_R1_001.fastq.gz']
        assert test_instance.capture_any_WES_batch_numbers(list_of_fastqs) == "WES44"
        list_of_fastqs = ['ONC151_02_EK6418_1837319_SWIFT5_Pan1190_S2_L001_R1_001.fastq.gz', 'NGS292_32_224051_AB_F_NGSEQ1cys_Pan1965_S32_R1_001.fastq.gz']
        assert not test_instance.capture_any_WES_batch_numbers(list_of_fastqs)
        print "capture_any_WES_batch_numbers tested"
        

    def test_capture_library_batch_numbers(self):
        # create runfolder object
        test_instance = process_runfolder("999999_NB552085_9999_automated_tests",str(datetime.datetime.now()),True)
        correct_file_names = ['ONC151_02_EK6418_1837319_SWIFT5_Pan1190_S2_L001_R1_001.fastq.gz', 'NGS292_32_224051_AB_F_NGSEQ1cys_Pan1965_S32_R1_001.fastq.gz', 'NGS292_04_223687_SO_F_BRCAv2_Pan1449_S4_R2_001.fastq.gz', 'TEST275F_60_216178_SC_M_WES44_Pan493_S1_R2_001.fastq.gz', 'ONC151_01_NTCcon_SWIFT5_Pan1190_S1_R2_001.fastq.gz']
        assert test_instance.capture_library_batch_numbers(correct_file_names) == "TEST275F_NGS292_ONC151"
        silly_file_names = ["abc123-silly-file-name", "silly-file-name-2"]
        assert test_instance.capture_library_batch_numbers(silly_file_names) == "would raise value error!"
        print "capture_library_batch_numbers tested"

    def test_build_nexus_project_name(self):
        wes_number = "WESNUMBER"
        library_batch = "LIBRARY_BATCH"
        runfolder_name = "abc123"
        test_instance = process_runfolder(runfolder_name,str(datetime.datetime.now()),True)
        
        #test_instance.build_nexus_project_name(wes_number,library_batch)
        dest_cmd, test_instance.runfolder_obj.nexus_path, test_instance.runfolder_obj.nexus_project_name = test_instance.build_nexus_project_name(wes_number,library_batch)
        assert dest_cmd == config.NexusProjectPrefix + runfolder_name + "_" + library_batch + "_" + wes_number + ":/"
        wes_number = None
        #test_instance.build_nexus_project_name(wes_number,library_batch)
        dest_cmd, test_instance.runfolder_obj.nexus_path, test_instance.runfolder_obj.nexus_project_name = test_instance.build_nexus_project_name(wes_number,library_batch)
        assert dest_cmd == config.NexusProjectPrefix + runfolder_name + "_" + library_batch + ":/"
        print "build_nexus_project_name tested"
    
    def test_write_create_project_script(self):
        wes_number = "WESNUMBER"
        library_batch = "LIBRARY_BATCH"
        runfolder_name = "abc123"
        test_instance = process_runfolder(runfolder_name,str(datetime.datetime.now()),True)
        test_instance.build_nexus_project_name(wes_number,library_batch)
        test_instance.write_create_project_script()
        with open(config.DNA_Nexus_project_creation_logfolder + test_instance.runfolder_obj.runfolder_name + ".sh",'r') as bash_creation_script:
            for line in bash_creation_script.readlines():
                print line
        print "write_create_project_script tested"

#for runfolder_name in config.upload_test_folders:
#for runfolder_name in ["999999_NB552085_9999_automated_tests"]:
test_process_runfolder().run_tests()


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