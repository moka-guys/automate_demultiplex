import sys
import smtplib
import unittest
#import pytest
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


class TestUploadandSetoffWorkflows(unittest.TestCase):


    def setUp(self):
    # Enable usage of monkeypatched classes across all unit tests in this test class 
        self.monkeypatch = MonkeyPatch()

        # unhash to see the full diff in command line  
        #self.maxDiff = None
    
    def test_start_building_dx_run_cmds(self):
            
        now = "2018-03-29 10:26:23.473031"
        # create an instance of RunfolderProcessor
        # Using the testing folder run below
        folder = '999999_NB552085_0077_AHYNCMAFXY'
        # set monkeypatch to change the pointer of RunfodlerProcessor to MockRunfolderProcessor 
        self.monkeypatch.setattr(__name__+  '.RunfolderProcessor', MockRunfolderProcessor)
        test_runfolder_instance =  RunfolderProcessor(folder, now, debug_mode=config.debug)
        # run the test input from mio
        expected_list = test_runfolder_instance.start_building_dx_run_cmds(mio.list_of_processed_samples)
        # check if output of method matches known true output
        # use set to check if all the elements of the list are present 
        # but disregard the order
        assert set(expected_list) == set(mio.test_output_commands_list)
 
        
    
    def test_find_fastqs(self):
        now = "2018-03-29 10:26:23.473031"
        # create an instance of RunfolderProcessor
        # Using the testing folder run below
        folder = '999999_NB552085_0077_AHYNCMAFXY'
        # set monkeypatch to change the pointer of RunfodlerProcessor to MockRunfolderProcessor 
        self.monkeypatch.setattr(__name__+  '.RunfolderProcessor', MockRunfolderProcessor)
        test_runfolder_instance =  RunfolderProcessor(folder, now, debug_mode=config.debug)
        # run the test input from mio
        expected_list_of_processed_samples, expected_fastq_string = test_runfolder_instance.find_fastqs(mio.runfolder_fastq_path)
        # check if output of method matches known true output
        self.assertEqual (expected_fastq_string, mio.test_fastq_string)
        # use set to check if all the elements of the list are present 
        # but disregard the order
        assert set(expected_list_of_processed_samples) == set(mio.list_of_processed_samples)

