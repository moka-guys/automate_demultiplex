import sys
import smtplib
import unittest
import pytest
from _pytest.monkeypatch import MonkeyPatch

from mock import mock, patch
 

import os
# This application is not a python package. Add parent directory to sys path to import custom modules
sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir))
)
import automate_demultiplex_config_test as config
import mock_inputs_and_outputs as mio

# mock classes to use for monkeypatching in tests
from mocks import MockRunfolderProcessor, mock_rename, mock_email

# This mock points all calls to automate_demultiplex_config to 
# automate_demultiplex_config_test to allow cloud based testing 
with mock.patch.dict('sys.modules', automate_demultiplex_config= config):
   import upload_and_setoff_workflows as uasw
   from upload_and_setoff_workflows import RunfolderProcessor, RunfolderObject


'''
    If you wish to patch a single method from a class OR patch an entire class 
    use the @patch
    # this works for mocking the whole class
    # @patch('test_upload_and_setoff_workflows.RunfolderProcessor', MockRunfolderProcessor) 
    # patch star_building_dx_run_cmds method only with a mock
    #@patch.object(RunfolderProcessor, 'start_building_dx_run_cmds', mock_start_building_dx_run_cmds) 
'''

@pytest.fixture(scope='function')
def test_runfolder():
    ''' This function creates an mock instance of RunfolderProcessor 
        to be used in testing as a function '''
    now = "2018-03-29 10:26:23.473031"
    folder = '999999_NB552085_0077_AHYNCMAFXY'
    monkeypatch = MonkeyPatch()
    monkeypatch.setattr(__name__+  '.RunfolderProcessor', MockRunfolderProcessor)
    test_runfolder_instance =  RunfolderProcessor(folder, now, debug_mode=config.debug)
    return test_runfolder_instance

# Call the test_runfolder function and 
# apply it to all the tests in this class 
@pytest.mark.usefixtures('test_runfolder')
class TestUploadandSetoffWorkflows():
    # unhash to see the full diff in command line  
    #self.maxDiff = None
    
    def test_start_building_dx_run_cmds(self, test_runfolder):
        # GIVEN a mock instance of RunFolderProcessor with known input data 
        # WHEN this method is run
        # THEN check if the returned list is equal to the test data 
        expected_list = test_runfolder.start_building_dx_run_cmds(mio.list_of_processed_samples)
        assert set(expected_list) == set(mio.test_output_commands_list)
 
           
    def test_find_fastqs(self, test_runfolder):
        # GIVEN a mock instance of RunFolderProcessor with known input data 
        # WHEN this method is run
        # THEN compare the characters in each string, ingore the order
        # this step is needed for tests to function in GitHub Actions 
        # as well as locally
        expected_list_of_processed_samples, expected_fastq_string = test_runfolder.find_fastqs(mio.runfolder_fastq_path) 
        assert ''.join(sorted(expected_fastq_string)).strip() == ''.join(sorted(mio.test_fastq_string)).strip()
        assert set(expected_list_of_processed_samples) == set(mio.list_of_processed_samples)

    def test_build_nexus_project_name(self, test_runfolder):
        # GIVEN a mock instance of RunFolderProcessor with known input data  
        # WHEN this method is run
        # THEN check if the returned list is equal to the test data 
        expected_nexus_project_name = test_runfolder.build_nexus_project_name(mio.wes_number, mio.library_batch)
        assert expected_nexus_project_name == mio.nexus_project_name

    def test_capture_any_WES_batch_numbers(self, test_runfolder):
        # GIVEN a mock instance of RunFolderProcessor with known input data 
        # WHEN this method is run 
        # THEN check if the returned list is equal to the test data 
        expected_wes_numbers = test_runfolder.capture_any_WES_batch_numbers(mio.list_of_processed_samples)
        assert expected_wes_numbers == mio.wes_number

 