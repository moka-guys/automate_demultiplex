"""

"""
import pytest, datetime, os, logging
from demultiplex import GetListOfRuns, ReadyToStartDemultiplexing

LOGGER = logging.getLogger(__name__)

open('script_logfile.txt', 'w').close()


@pytest.fixture
def base_path():
    return os.path.join(os.getcwd(), '/test/test_files/')

def startdemultiplex_obj():
    scriptlog = 'script_logfile.txt'
    bcl2fastqlog = 'test_bcl2fastq2_output.log'
    for file in scriptlog, bcl2fastqlog:
        path = os.path.join(os.getcwd(), file)
        if os.path.isfile(path):
            os.remove(path)
    sd = ReadyToStartDemultiplexing(str('{:%Y%m%d_%H%M%S}'.format(datetime.datetime.now())), 'script_logfile.txt')
    sd.bcl2fastqlog = bcl2fastqlog
    sd.scriptlog = scriptlog
    sd.runfolder=''
    sd.runfolder_dir=os.getcwd()
    sd.email_subject = "string"
    sd.email_message="Please ignore this email. This is a demultiplex.py unit test"
    sd.log_flags = {'info': 'demultiplextest_info', 'fail': 'demultiplextest_fail',
                      'success': 'demultiplextest_success', 'test_warning': 'testsamplesheet_warning'}
    return sd

def getlistofruns_obj():
    glr = GetListOfRuns()
    return glr

# def test_check_demultiplexing_required():
#     pass
#
# def test_run_demultiplexing():
#     pass
#
# def test_bcl2fastq_log_present():
#     pass
#
# def test_validate_samplesheet():
#     pass
#
# def test_sequencing_complete():
#     pass
#
# def test_bcl2fastq_installed():
#     pass
#
# def test_disallowed_ss_errs():
#     pass
#
# def test_sequencer_requires_integritycheck():
#     pass
#
# def test_checksum_file_present():
#     pass
#
# def test_prior_integritycheck_failed():
#     pass
#
# def test_checksums_match():
#     pass
#
# def test_send_integritycheckfail_email():
#     pass


# DONE
def test_send_email_success():
    sd = startdemultiplex_obj()
    sd.email_subject = "DEMULTIPLEX TEST PASS - PLEASE IGNORE"
    sd.email_message = "Please ignore this email. This is a demultiplex.py unit test"
    assert sd.send_email()

# DONE
def test_send_email_fail():
    """Test email sending failure - incorrect credentials provided
    """
    sd = startdemultiplex_obj()
    sd.user = "abc"
    sd.email_subject = "DEMULTIPLEX TEST FAIL - PLEASE IGNORE"
    assert not sd.send_email()

# DONE
def test_create_bcl2fastqlog_pass():
    sd = startdemultiplex_obj()
    sd.create_bcl2fastqlog()
    assert os.path.isfile(sd.bcl2fastqlog)

# DONE
def test_create_tso_bcl2fastqlog_pass():
    bcl2fastqlog_path = '{}/{}'.format(os.getcwd(), 'test_bcl2fastq2_output.log')
    expected_message = 'TSO500 run. Does not need demultiplexing locally'
    sd = startdemultiplex_obj()
    sd.bcl2fastqlog_path = bcl2fastqlog_path
    sd.create_tso_bcl2fastqlog()
    assert os.path.isfile(bcl2fastqlog_path) # file contents
    with open(bcl2fastqlog_path) as f:
        assert expected_message in f.read()

# DONE
def test_create_tso_bcl2fastqlog_fail():
    bcl2fastqlog_path = 'test_dir/test_bcl2fastq2_output.log'
    sd = startdemultiplex_obj()
    sd.bcl2fastqlog_path = bcl2fastqlog_path
    sd.create_tso_bcl2fastqlog()
    assert not os.path.isfile(bcl2fastqlog_path)

# def test_run_bcl2fastq_success():
#     pass

# def test_run_bcl2fastq_fail():
#         pass

def test_logger_pass():
    """Check expected strings written to logfile. This means writing to syslog was also successful
    """
    message, tool = "Logging test string", "TEST_SCRIPT"
    expected_message = 'Log written - TEST_SCRIPT: Logging test string'
    sd = startdemultiplex_obj()
    assert sd.logger(message, tool)
    with open(sd.scriptlog) as f:
        assert expected_message in f.read()