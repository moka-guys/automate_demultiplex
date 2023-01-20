# """Test upload_and_setoff_workflows.py"""

# import sys
# import smtplib
# import os
# # This application is not a python package. 
# # Add parent directory to sys path to import custom modules
# sys.path.append(
#     os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir))
# )
# import ad_config as config
# import upload_and_setoff_workflows as uasw
# from upload_and_setoff_workflows import RunfolderProcessor
# from mocks import MockRunfolderProcessor, mock_rename, mock_email

# def test_runfolder_processor(monkeypatch):
#     """Test upload_and_setoff_workflows.py protocol while replacing functions in
#     uasw.RunfolderProcessor with those in MockRunfolderProcessor.

#     As RunfolderProcessor carries most methods used to process NGS runfolders, this test suite 
#     allows us to test specific functions while skipping expensive operations like creating 
#     runfolders, running the NGS workflows or sending emails.
#     """

#     # Patch RunfolderProcessor to use any functions specified in MockRunfolderProcessor
#     monkeypatch.setattr(uasw, "RunfolderProcessor", MockRunfolderProcessor)
#     # Patch os.rename to skip moving logfiles
#     monkeypatch.setattr(os, "rename", mock_rename)
#     # Patch smtplib to stop emails being sent
#     monkeypatch.setattr(smtplib.SMTP, "sendmail", mock_email)

#     # Run the protocol for processing NGS runfolders. This is equivalent to:
#     # `python upload_and_setoff_workflows.py`
#     runs = uasw.SequencingRuns()
#     runs.set_runfolders()
#     runs.loop_through_runs()