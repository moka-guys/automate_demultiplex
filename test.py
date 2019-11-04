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
        self.test_execute_subprocess_command()
        # self.test_test_upload_agent()
        # self.test_test_dx_toolkit()
        # self.test_run_tests()
        # self.test_set_panel_dictionary()
        # self.test_perform_test()
        # self.test_find_fastqs()
        # self.test_capture_any_WES_batch_numbers()
        # self.test_capture_library_batch_numbers()
        # self.test_build_nexus_project_name()
        self.test_write_create_project_script()
        # self.test_run_project_creation_script()
        self.test_upload_fastqs()
        self.test_look_for_upload_errors_fastq()
        self.test_start_building_dx_run_cmds()


    def test_runfolder_object(self):
        """
        This function tests the creation of a run folder object using the runfolder_object class
        The class is instantiated with a fake runfolder name and the properties are assessed
        """
        test_runfolder_obj = runfolder_object("abc123")
        # test correct number of properties in the object they are as expected
        assert len(vars(test_runfolder_obj)) == 6
        assert test_runfolder_obj.runfolder_name == "abc123"
        assert test_runfolder_obj.nexus_project_name == ""
        assert test_runfolder_obj.nexus_path == ""
        assert config.runfolders in test_runfolder_obj.fastq_folder_path  and "abc123" in test_runfolder_obj.fastq_folder_path  and config.fastq_folder in test_runfolder_obj.fastq_folder_path 
        print "runfolder class tested"
    
    def test_execute_subprocess_command(self):
        """
        Test the function which calls subprocess.Popen. This takes a command and returns a tuple of (stdout ,stderr)
        If debug mode is true this function returns a string which is used to test other functions
        """
        # issue simple echo hello world command with debug = false
        command = "hello_world"
        out, err = process_runfolder("abc123", str(datetime.datetime.now()),False).execute_subprocess_command("echo " + command)
        assert command in out
        assert err == ""
        # repeat with debug = true
        out, err = process_runfolder("abc123", str(datetime.datetime.now()),True).execute_subprocess_command("echo " + command)
        assert config.demultiplex_success_string in out and config.upload_agent_expected_stdout in out
        assert err == "err"
        print "execute_subprocess_command tested"

    def test_run_tests(self):
        """
        All the functions applied here are tested elsewhere
        """
        pass

    def test_test_upload_agent(self):
        """
        the test_upload_agent function recieves the output of a function which assesses the presense of the expected string in stdout and returns true or false
        Both scenarios are tested here
        """
        assert process_runfolder("abc123", str(datetime.datetime.now()),True).test_upload_agent(True)
        assert not process_runfolder("abc123", str(datetime.datetime.now()),True).test_upload_agent(False)
        

    def test_test_dx_toolkit(self):
        """
        the test_dx_toolkit function recieves the output of a function which assesses the presense of the expected string in stdout and returns true or false
        Both scenarios are tested here
        """
        assert process_runfolder("abc123", str(datetime.datetime.now()),True).test_dx_toolkit(True)
        assert not process_runfolder("abc123", str(datetime.datetime.now()),True).test_dx_toolkit(False)

    def test_set_panel_dictionary(self):
        """
        set_panel_dictionary builds and returns a dictionary where each key is a pannumber and the value is a dictionary of settings.
        At first for each panel a dictionary of default settings is built (from config file) 
        Defaults are overwritten where appropriate (using config.panel_settings)
        This function asserts:
         - There are the correct number of settings for each panel 
         - If default settings are correct 
         - If defaults have been overwritten
         - If allpanels are present
        """
        # create instance of class
        test_instance = process_runfolder("abc123", str(datetime.datetime.now()), True)
        # capture created dictionary
        panel_dictionary = test_instance.set_panel_dictionary()
        # check each panel has all the expected properties
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
        """
        The find_fastqs function takes the path to the fastq folder and returns a tuple of:
            list of samples to be processed (based on pan number)
            string of all fastq paths (for the upload agent)
            list of samples that aren't processed (based on pan number)
        A mock runfolder is used and each of the above are assessed
        """
        # create runfolder object
        test_instance = process_runfolder("999999_NB552085_9999_automated_tests",str(datetime.datetime.now()),True)
        list_of_processed_samples, fastq_string, not_processed = test_instance.find_fastqs(test_instance.runfolder_obj.fastq_folder_path)
        
        # check undertermined sample hasn't been included to be processed
        assert "Undetermined" not in list_of_processed_samples
        # check fastqs in list_of_processed_samples should be there
        for fastq in list_of_processed_samples:
            assert  "Pan" + fastq.split("_Pan")[1].split("_")[0] in config.panel_list
            assert "-Pan" not in fastq
        # check all samples which should be processed have been identified
        assert len(list_of_processed_samples) == 10 
        # check length of fastq string correlates - nb len of fastq string is one more because it starts with an extra space
        assert len(fastq_string.split(" ")) == len(list_of_processed_samples) + 1
        # check the fastqs that were identified as not to process shouldn't be processed
        for fastq in not_processed:
            # the test that miseq fastqs are ignored is above - checking-Pan not in processed samples - these may have valid pannumber
            if "-Pan" not in fastq:
                assert  "Pan" + fastq.split("_Pan")[1].split("_")[0] not in config.panel_list


        print "find_fastqs tested"

        
    def test_capture_any_WES_batch_numbers(self):
        """
        The capture_any_WES_batch_numbers function takes a list of fastqs and returns a string of WES batch numbers identified in the filename or returns False
        Lists of filenames are provided and assessed for expected results 
        """
        # create runfolder object
        test_instance = process_runfolder("999999_NB552085_9999_automated_tests",str(datetime.datetime.now()),True)
        # create list of samples including > 1 sample with a "WES44 in name" 
        list_of_fastqs = ['ONC151_02_EK6418_1837319_SWIFT5_Pan1190_S2_L001_R1_001.fastq.gz', 'NGS292_32_224051_AB_F_NGSEQ1cys_Pan1965_S32_R1_001.fastq.gz', 'NGS292_04_223687_SO_F_BRCAv2_Pan1449_S4_R2_001.fastq.gz', 'NGS292_32_224051_AB_F_NGSEQ1cys_Pan1965_S32_R2_001.fastq.gz', 'ONC151_01_NTCcon_SWIFT5_Pan1190_S1_R1_001.fastq.gz', 'TEST275F_60_216178_SC_M_WES44_Pan493_S1_R2_001.fastq.gz', 'ONC151_01_NTCcon_SWIFT5_Pan1190_S1_R2_001.fastq.gz', 'NGS292_04_223687_SO_F_BRCAv2_Pan1449_S4_R1_001.fastq.gz', 'ONC151_02_EK6418_1837319_SWIFT5_Pan1190_S2_L001_R2_001.fastq.gz', 'TEST275F_60_216178_SC_M_WES44_Pan493_S1_R1_001.fastq.gz']
        assert test_instance.capture_any_WES_batch_numbers(list_of_fastqs) == "WES44"
        # pass a list with no WES samples - should return False
        list_of_fastqs = ['ONC151_02_EK6418_1837319_SWIFT5_Pan1190_S2_L001_R1_001.fastq.gz', 'NGS292_32_224051_AB_F_NGSEQ1cys_Pan1965_S32_R1_001.fastq.gz']
        assert not test_instance.capture_any_WES_batch_numbers(list_of_fastqs)
        print "capture_any_WES_batch_numbers tested"
        

    def test_capture_library_batch_numbers(self):
        """
        The capture_library_batch_numbers function takes a list of fastqs
        Returns either a string of library batch numbers extracted from filename or returns False (only if no underscores in filenames)
        This test provides lists of filenames and assessed for expected results 
        """
        # create runfolder object
        test_instance = process_runfolder("999999_NB552085_9999_automated_tests",str(datetime.datetime.now()),True)
        correct_file_names = ['ONC151_02_EK6418_1837319_SWIFT5_Pan1190_S2_L001_R1_001.fastq.gz', 'NGS292_32_224051_AB_F_NGSEQ1cys_Pan1965_S32_R1_001.fastq.gz', 'NGS292_04_223687_SO_F_BRCAv2_Pan1449_S4_R2_001.fastq.gz', 'TEST275F_60_216178_SC_M_WES44_Pan493_S1_R2_001.fastq.gz', 'ONC151_01_NTCcon_SWIFT5_Pan1190_S1_R2_001.fastq.gz']
        assert test_instance.capture_library_batch_numbers(correct_file_names) == "TEST275F_NGS292_ONC151"
        silly_file_names = ["abc123-silly-file-name", "silly-file-name-2"]
        assert not test_instance.capture_library_batch_numbers(silly_file_names) 
        print "capture_library_batch_numbers tested"

    def test_build_nexus_project_name(self):
        """
        The build_nexus_project_name function takes wes_number (str or None), library_batch (str) and a run folder name (str)
        It returns the strings; project_path, project_name and a destination 
        If wes_number is None, this is not included in the output. assess output with and without wes_number
        """
        # set variables
        wes_number = "WESNUMBER"
        library_batch = "LIBRARY_BATCH"
        runfolder_name = "abc123"
        test_instance = process_runfolder(runfolder_name,str(datetime.datetime.now()),True)
        
        # call function providing wes_number
        # check all outputs are as expected
        dest_cmd, nexus_path, nexus_project_name = test_instance.build_nexus_project_name(wes_number,library_batch)
        assert dest_cmd == config.NexusProjectPrefix + runfolder_name + "_" + library_batch + "_" + wes_number + ":/"
        assert nexus_path == runfolder_name + "_" + library_batch + "_" + wes_number + "/Data/Intensities/BaseCalls"
        assert nexus_project_name == config.NexusProjectPrefix + runfolder_name + "_" + library_batch + "_" + wes_number
        assert dest_cmd == nexus_project_name + ":/"
        
        # call function with NO wes_number
        # check all outputs are as expected
        wes_number = None
        dest_cmd, nexus_path, nexus_project_name = test_instance.build_nexus_project_name(wes_number,library_batch)
        assert dest_cmd == config.NexusProjectPrefix + runfolder_name + "_" + library_batch + ":/"
        assert nexus_path == runfolder_name + "_" + library_batch  + "/Data/Intensities/BaseCalls"
        assert nexus_project_name == config.NexusProjectPrefix + runfolder_name + "_" + library_batch
        assert dest_cmd == nexus_project_name + ":/"
        print "build_nexus_project_name tested"
    
    def test_write_create_project_script(self):
        """
        The write_create_project_script writes a bash script containing commands to create and share the project using the nexus sdk
        The function returns the path to this script which is read by ths function
        The dx run command is tested and all users have correct permissions is tested.

        """
        ### set up test 
        wes_number = "WESNUMBER"
        library_batch = "LIBRARY_BATCH"
        runfolder_name = "abc123"
        # Create instance of class
        test_instance = process_runfolder(runfolder_name, str(datetime.datetime.now()), True)
        # call function to build nexus project name -update the instance runfolder_obj
        dest, test_instance.runfolder_obj.nexus_path,test_instance.runfolder_obj.nexus_project_name =  test_instance.build_nexus_project_name(wes_number, library_batch)
        ### perform test
        # # capture path returned by fumction 
        bash_script_path = test_instance.write_create_project_script()
        # check file exists
        assert os.path.isfile(bash_script_path)
        # open script as read only into list
        with open(bash_script_path,'r') as bash_creation_script:
            bash_script_lines =  bash_creation_script.readlines()
        # test the line where project is created contains the prod organisation (billed to)
        for line in bash_script_lines:
            if "dx new" in line:
                assert config.prod_organisation in line
        # check each user with view access has been shared with view permissions
        for user in config.view_users:
            seen = False
            for line in bash_script_lines:
                if user in line and user != config.prod_organisation:
                    seen = True
                    assert "VIEW" in line
                # prod-organisation is in two lines, ignore the dx new line (tested above)
                elif user in line and user == config.prod_organisation and "dx new" not in line:
                    seen = True
            assert seen
        # repeat for admin users
        for user in config.admin_users:
            seen = False
            for line in bash_script_lines:
                if user in line:
                    assert "ADMIN" in line
                    seen = True
            assert seen
        
        # finally compare to script with expected contents
        example_file_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "test_materials/create_nexus_project.sh")
        with open(example_file_path,'r') as example_file:
            example_file_list=example_file.readlines()
        # loop through the lines in newly created script - compare lines with example file
        for linenumber in range(0,len(bash_script_lines)):
            assert bash_script_lines[linenumber] == example_file_list[linenumber]
        print "write_create_project_script tested"

    def test_run_project_creation_script(self):
        """
        The run_project_creation_script module takes the path to the bash script (created elsewhere), calls the subprocess function and returns the projectid from stdout
        when debug mode is on the subprocess command is not run and the stdout is replaced with the function input, allowing us to test different scenarios
        Here we pass a stdout where we expect the function to pass and another where we expect it to fail.
        """
        # create instance of class
        test_instance = process_runfolder("abc123",str(datetime.datetime.now()),True)
        # give a string which should pass the test
        input = "project-abc123"
        projectid = test_instance.run_project_creation_script(input)
        assert projectid == input
        # give a string which should fail the test (returning False when debug mode is on)
        input = "not_the_P_word"
        assert not test_instance.run_project_creation_script(input)
        print "run_project_creation_script tested"
    
    def test_upload_fastqs(self):
        """
        The function upload_fastqs uses variables set in the find_fastq function - here these variables are set in the class instance
        the function builds an upload agent command string which is the passed to the subprocess function
        When debug mode is true the command is returned without calling subprocess
        """
        # create instance and set variables used by function
        test_instance = process_runfolder("abc123",str(datetime.datetime.now()),True)
        test_instance.fastq_string = " path/to/file1 path/to/file2"
        test_instance.runfolder_obj.nexus_path = "Data/Intensities/BaseCalls"
        test_instance.runfolder_obj.nexus_project_name = "002_runfoldername_NGS999"
        upload_command = test_instance.upload_fastqs()
        # assert uplaod command is as per expected
        assert upload_command == 'ua_status=1; while [ $ua_status -ne 0 ]; do /usr/bin/ua --auth-token  --project 002_runfoldername_NGS999  --folder /Data/Intensities/BaseCalls --do-not-compress --upload-threads 10 path/to/file1 path/to/file2; ua_status=$?; if [[ $ua_status -ne 0 ]]; then echo "temporary issue when uploading file fastq files"; fi ; done'
        print "upload_fastq tested"

    def test_look_for_upload_errors_fastq(self):
        """
        The function look_for_upload_errors_fastq() recieves a path to the file containing stdout captured from the upload of fastqs
        The ua command will repeat the command until upload complete
        This file is opened and read into a list and each line assessed for presense of an predefined error message
        There are three options: 
        1) error message present but upload complete
        2) error message not complete
        3) error message not present
        """
        # create instance and set variables used by function
        test_instance = process_runfolder("abc123",str(datetime.datetime.now()),True)
        #path to file with error message
        example_file_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "test_materials/fq_upload_disrupted.txt")
        assert test_instance.look_for_upload_errors_fastq(example_file_path) == "disrupted but complete"
        assert test_instance.look_for_upload_errors_fastq(example_file_path) != "fail"
        assert test_instance.look_for_upload_errors_fastq(example_file_path) != "no error"
        #path to file with error message
        example_file_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "test_materials/fq_upload_fail.txt")
        assert test_instance.look_for_upload_errors_fastq(example_file_path) != "disrupted but complete"
        assert test_instance.look_for_upload_errors_fastq(example_file_path) == "fail"
        assert test_instance.look_for_upload_errors_fastq(example_file_path) != "no error"
        #path to file with error message
        example_file_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "test_materials/fq_upload_ok.txt")
        assert test_instance.look_for_upload_errors_fastq(example_file_path) != "disrupted but complete"
        assert test_instance.look_for_upload_errors_fastq(example_file_path) != "fail"
        assert test_instance.look_for_upload_errors_fastq(example_file_path) == "no error"
        print "look_for_upload_errors_fastq tested"
    
    def test_start_building_dx_run_cmds(self):
        """
        This function recieves a list of samples to be processed and calls a number of other functions which return the dx run commands for each sample.
        It also detects any run-wide commands that are required
        All dx run commands are stored in a list which is returned.
        Each function which returns a dx run command will be tested seperately.
        Therefore this test needs to check the correct modules are called. 
        """
        # create instance and set variables used by function
        test_instance = process_runfolder("abc123",str(datetime.datetime.now()),True)
        
        # test a panel that has mokawes iva and peddy - expect entries for/
        #  source command,mokawes command,depends_list command ,build iva command, run iva command, depends_list command, peddy command, multiqc command, upload multiqc command, smartsheet command
        to_process_list=["wes_iva_peddy_Pan493_R1_01.fastq"]
        command_list = test_instance.start_building_dx_run_cmds(to_process_list)
        print command_list
        assert test_instance.source_command == command_list[0]
        print len(command_list)
        assert len(command_list) == 10
        for line in command_list:
            assert "congenica" not in line
            assert config.mokapipe_path not in line
            assert config.mokaamp_path not in line
            assert config.mokaonc_path not in line
        assert len(test_instance.start_building_dx_run_cmds.rpkm_list) == 0
        #print "start_building_dx_run_cmds tested"
        
        # test a panel that has mokawes sapientia and peddy
        to_process_list=["wes_sap_peddy_Pan3237_R1_01.fastq"]
        command_list = test_instance.start_building_dx_run_cmds(to_process_list)
        print command_list
        assert test_instance.source_command == command_list[0]
        print len(command_list)
        assert len(command_list) == 10
        for line in command_list:
            assert "ingenuity" not in line
            assert config.mokapipe_path not in line
            assert config.mokaamp_path not in line
            assert config.mokaonc_path not in line
        assert len(test_instance.start_building_dx_run_cmds.rpkm_list) == 0
        
        # test a panel that has mokapipe iva and RPKM
        to_process_list=["wes_sap_peddy_Pan1449_R1_01.fastq"]
        command_list = test_instance.start_building_dx_run_cmds(to_process_list)
        print command_list
        assert test_instance.source_command == command_list[0]
        print len(command_list)
        assert len(command_list) == 10
        for line in command_list:
            assert "ingenuity" not in line
            assert config.mokawes_path not in line
            assert config.mokaamp_path not in line
            assert config.mokaonc_path not in line
        assert len(test_instance.start_building_dx_run_cmds.rpkm_list) == 1
        
        # test a panel that has mokapipe sap and RPKM
        to_process_list=["wes_sap_peddy_Pan3237_R1_01.fastq"]
        command_list = test_instance.start_building_dx_run_cmds(to_process_list)
        print command_list
        assert test_instance.source_command == command_list[0]
        print len(command_list)
        assert len(command_list) == 10
        for line in command_list:
            assert "ingenuity" not in line
            assert config.mokapipe_path not in line
            assert config.mokaamp_path not in line
            assert config.mokaonc_path not in line
            assert config.config.RPKM_path not in line
        # test a panel that has mokapipe iva and no RPKM

        # test a panel that has mokaamp and iva
        # test a panel that has mokaamp and sap
        # check for multiqc
        # check for create smartsheet
        print "start_building_dx_run_cmds tested"

test_process_runfolder().run_tests()


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