import sys
import os
sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir))
)
from mock import mock, patch
import automate_demultiplex_config_test as config 

# This mock points all calls to automate_demultiplex_config to 
# automate_demultiplex_config_test to allow cloud based testing 
with mock.patch.dict('sys.modules', automate_demultiplex_config= config):
    import upload_and_setoff_workflows as uasw
    from upload_and_setoff_workflows import RunfolderProcessor, RunfolderObject
    import adlogger




# Any methods from RunfoldeProcessor you wish to mock out can be defined in here 
class MockRunfolderProcessor(RunfolderProcessor):

    def __init__(self, *args, **kwargs):
        super(MockRunfolderProcessor, self).__init__(*args, **kwargs)

    #def start_building_dx_run_cmds(self, list_of_processed_samples):
     #   return 'string'

    def upload_fastqs(self):
        return "test/data/UPLOAD_AGENT_PATH.txt"

    def upload_rest_of_runfolder(self):
        return "test/data/UPLOAD_PATH.txt"

    def upload_log_files(self):
        return "test/data/UPLOAD_LOGFILES.txt"

    def run_dx_run_commands(self):
        pass

    def smartsheet_workflows_commands_sent(self):
        pass

    def send_opms_queries(self):
        pass

    def run_project_creation_script(self):
        # 002_999999_NB552085_9993_automated_tests_TEST275F_ONC20004_WES44
        return "project-FjkQYxj02QvYZ5j03bzk2ZBp"

def mock_email(*args):
    pass

def mock_rename(original, new):
    pass




