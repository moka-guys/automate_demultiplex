import sys
import os
sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir))
)
from upload_and_setoff_workflows import RunfolderProcessor


class MockRunfolderProcessor(RunfolderProcessor):

    def __init__(self, *args, **kwargs):
        super(MockRunfolderProcessor, self).__init__(*args, **kwargs)

    def run_tests(self):
        pass

    def already_uploaded(self):
        return False

    def has_demultiplexed(self):
        return True

    def upload_fastqs(self):
        return "UPLOAD_AGENT_PATH.txt"

    def upload_rest_of_runfolder(self):
        return "UPLOAD_PATH.txt"

    def upload_log_files(self):
        return "UPLOAD_LOGFILES.txt"

    def look_for_upload_errors(self, filepath, stage):
        pass

    def look_for_upload_errors_fastq(self, upload_agent_stdout_path):
        pass

    def run_dx_run_commands(self):
        pass

    def smartsheet_workflows_commands_sent(self):
        pass

    def send_opms_queries(self):
        pass

    def run_project_creation_script(self, project_bash_script_path):
        return "project-Fj4zZ200jYvx0FGP60vyykqY"

def mock_rename(original, new):
    pass