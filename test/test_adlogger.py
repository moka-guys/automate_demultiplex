# class TestLogging():
#     """ Test Logging class """
#     @classmethod
#     def class_attributes(cls):
#         cls.scriptlog_path = scriptlog_path
#         cls.temp_dir = temp_dir

#     @pytest.fixture
#     def logger(cls):
#         logger = Logging(cls.scriptlog_path).logger
#         return logger

#     @pytest.fixture(autouse=True)
#     def run_before_and_after_tests(cls):
#         """Fixture to execute asserts before and after a test is run - resets class variables and
#         removes temp dirs"""
#         # SETUP -
#         cls.class_attributes()  # Get class attributes
#         os.makedirs(cls.temp_dir)  # Create temp dir for script to create file in. Removed by
#                                     # teardown class
#         open(cls.scriptlog_path, 'w').close()  # Create test scriptlog file
#         yield  # Where the testing happens
#         # TEARDOWN - cleanup after each test
#         if os.path.isdir(cls.temp_dir):
#             shutil.rmtree(cls.temp_dir)  # Remove dir and all flag files created

#     @pytest.fixture
#     def expected_message(cls):
#         return 'demultiplextest_info - INFO - Logging test string'

#     def test_logger_pass(cls, logger, expected_message):
#         """Check expected strings written to logfile. This means writing to syslog was also
#         successful"""
#         logger.info("Logging test string", extra={'flag': 'demultiplextest_info'})
#         with open(cls.scriptlog_path) as f:
#             assert expected_message in f.read()
