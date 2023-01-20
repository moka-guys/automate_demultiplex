# coding=utf-8
""" Automate demultiplex logging.

Currently only the 'script', 'upload_agent' and 'backup' logfiles are configured to be writeable to
by this script. These logfiles are written to by the upload and setoff workflows script.


        self.script = self._get_ad_logger('automate_demultiplex', script)
        self.upload_agent = self._get_ad_logger('upload_agent', upload_agent)
        self.backup = self._get_ad_logger('backup_runfolder', backup)
"""
import sys
import logging
import logging.handlers
import ad_config as config


# class ADLoggers(object):
#     """Access all logfiles uploaded to DNANexus as part of automate demultiplex scripts.

#     Args:
#         project(str): Path to DNAnexus create project bash script
#         dx_run(str): Path to dx run commands
#         demultiplex(str): Path to logfile of decisions made during demultiplexing script
#         upload_agent(str): Path to DNANexus_Upload_started.txt in runfolder
#         backup(str): Path to logfile for backing up rest of runfolder.
#         script(str): Path to logfile for python script that calls ADLogger.
#     """
# # Logfiles to be written to by demultiplex.py
#         self.demultiplex = self._get_ad_logger("demultiplex", demultiplex)
#         # Logfiles to be written to by upload_and_setoff_workflows
#         self.script = self._get_ad_logger('automate_demultiplex', script)
#         self.upload_agent = self._get_ad_logger('upload_agent', upload_agent)
#         self.backup = self._get_ad_logger('backup_runfolder', backup)
#         # Get mock objects for files that are uploaded to DNANexus but not written to by loggers.
#         self.project = self._get_ad_logger("create_project", project, file_only=True)
#         self.dx_run = self._get_ad_logger("dx_run", dx_run, file_only=True)

# self.scriptlog = os.path.join(config.upload_script_logpath,
#                               f"{self.timestamp}_upload_and_setoff_workflow.log")
# adlogger_config["project"] = os.path.join(config.dnanexus_projectcreation_logfolder,
#                                           f"{runfolder.runfolder_name}.sh")
# adlogger_config["dx_run"] = runfolder.runfolder_dx_run_script
# adlogger_config["upload_agent"] = os.path.join(runfolder.runfolderpath,
#                                                config.upload_started_filename)
# adlogger_config["backup"] = os.path.join(config.backup_runfolder_logfile,
#                                          f"{runfolder.runfolder_name}_backup_runfolder.log")

class AdLogger(object):
    """Create logger instance"""

    formatter = logging.Formatter(config.logging_formatter)  # Log string format

    def __init__(self, logger_name, logfile_path):
        """
        Args:
            logger_name(str): Logger name
            logfile_path(str): Logfile path
        """
        self.logger_name = logger_name
        self.logfile_path = logfile_path
        self.logger = self._get_logger()

    def _get_logger(self):
        """ Returns a Python logging object """
        logger = logging.getLogger(self.logger_name)
        logger.setLevel(logging.DEBUG)
        logger.addHandler(self._get_file_handler())
        logger.addHandler(self._get_syslog_handler())
        logger.addHandler(self._get_stream_handler())
        return logger

    def _get_file_handler(self):
        file_handler = logging.FileHandler(self.logfile_path, mode="a", delay=True)
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(self.formatter)
        return file_handler

    def _get_syslog_handler(self):
        syslog_handler = logging.handlers.SysLogHandler(address="/dev/log")
        syslog_handler.setLevel(logging.DEBUG)
        syslog_handler.setFormatter(self.formatter)
        return syslog_handler

    def _get_stream_handler(self):
        stream_handler = logging.StreamHandler(sys.stdout)
        stream_handler.setLevel(logging.DEBUG)
        stream_handler.setFormatter(self.formatter)
        return stream_handler

    def shutdown_logs(self):
        """
        To prevent duplicate filehandlers and system handlers close and remove handlers
        """
        logger_handlers = self.logger.handlers[:]

        for handler in logger_handlers:
            handler.close()
            self.logger.removeHandler(handler)
        # while logger.hasHandlers():
        #     logger.handlers.clear()

        logging.shutdown()
