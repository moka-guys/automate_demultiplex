
# class TestEmail():
#     """ Test Email class """
#     @classmethod
#     def class_attributes(cls):
#         cls.email_subject = "DEMULTIPLEX TEST - PLEASE IGNORE"
#         cls.email_message = "Please ignore this email. This is a demultiplex.py unit test"
#         cls.scriptlog_path = scriptlog_path
#         cls.temp_dir = temp_dir

#     @pytest.fixture(autouse=True)
#     def run_before_and_after_tests(cls):
#         """Fixture to execute asserts before and after a test is run - resets class variables and removes tem
#         dirs"""
#         # SETUP -
#         cls.class_attributes()  # Get class attributes
#         cls.temp_dir = temp_dir
#         os.makedirs(cls.temp_dir)  # Create temp dir for script to create file in. Removed by teardown class
#         yield  # Where the testing happens
#         # TEARDOWN - cleanup after each test
#         if os.path.isdir(cls.temp_dir):
#             shutil.rmtree(cls.temp_dir)  # Remove dir and all flag files created

#     def test_send_email_success(cls):
#         email_obj = Email(cls.scriptlog_path, cls.email_subject, cls.email_message)
#         assert email_obj.send_email()

#     def test_send_email_fail(cls):
#         """Test email sending failure - incorrect credentials provided
#         """
#         email_obj = Email(cls.scriptlog_path, cls.email_subject, cls.email_message)
#         email_obj.user = "abc"
#         assert not email_obj.send_email()

