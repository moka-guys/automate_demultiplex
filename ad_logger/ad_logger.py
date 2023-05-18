# coding=utf-8
"""
Automate demultiplex logging.

Currently only the 'script", 'upload_agent' and 'backup' logfiles are
configured to be writeable to by this script. These logfiles are written to by
the upload and setoff workflows script.

        self.script = self._get_ad_logger('automate_demultiplex", script)
        self.upload_agent = self._get_ad_logger('upload_agent", upload_agent)
        self.backup = self._get_ad_logger('backup_runfolder", backup)
"""
import sys
import logging
import logging.handlers
import config.ad_config as ad_config
import ad_logger.log_config as log_config


class AdLoggers(object):
    """
    Access runfolder-associated logfiles, which are also uploaded to DNAnexus
    as part of the automate demultiplex scripts. (upload_agent file is not
    uploaded because it is being written to as the upload is taking place)

    Args:
        demultiplex(str):   Path to logfile of decisions made during
                            demultiplexing script
                            *projname*_demultiplex_script_log.txt
        upload_agent(str):  Upload agent logfile. Stores Logs relating to
                            runfolder upload.
                            *runfolderpath*/DNANexus_upload_started.txt
        backup(str):        Path to logfile for runfolder backup.
                            *projname*_backup_runfolder.log
        project(str):       Path to DNAnexus project creation bash script
                            create_nexus_project_*projname*.sh
        dx_run(str):        Path to dx run commands.
                            *projname*_dx_run_commands.sh
        upload_script(str): upload_and_setoff_workflows script logfile.
                            *projname*_upload_and_setoff_workflow.log
    """

    _formatter = logging.Formatter(ad_config.LOGGING_FORMATTER)

    def __init__(self, timestamp, runfolder_obj=None):
        """
        Args:
            logger_name(str): Logger name
            logfile_path(str): Logfile path
        """
        self.timestamp = timestamp
        self.runfolder_obj = runfolder_obj
        self.logfiles_config = self.get_logfiles_config()
        self.log_flags = log_config.LOG_FLAGS
        self.loggers = self.get_loggers()  # Collect all loggers
        self.msgs = log_config.LOG_MSGS

    def get_loggers(self):
        """
        Assign loggers using log ad_config
        """
        all_loggers = []

        for key in self.logfiles_config:
            setattr(
                AdLoggers, key,
                self._get_logger(key, self.logfiles_config[key])
            )
            all_loggers.append(getattr(AdLoggers, key))
        return all_loggers

    def get_logfiles_config(self):
        """Return an ADLogger ad_config for a runfolder.

        Returns:
            log_config(dict): A dictionary of arguments for ADLoggers
        """
        # Configuration for ADLoggers. Dictionary where keys are
        # ADLoggers.__init__ arguments and values are logfile paths.
        if self.runfolder_obj:
            # Runfolder-specific logfiles
            logfiles_config = {
                "usw_rf": self.runfolder_obj.upload_runfolder_logfile,
                "demultiplex_rf": (
                    self.runfolder_obj.demultiplex_runfolder_logfile
                    ),
                "upload_agent": self.runfolder_obj.upload_agent_logfile,
                "backup": self.runfolder_obj.backup_runfolder_logfile,
                "project": self.runfolder_obj.project_creation_logfile,
                "dx_run": self.runfolder_obj.runfolder_dx_run_script,
            }
        else:
            logfiles_config = {
                # Upload and setoff workflows script logfile
                "usw_script": (
                    ad_config.LOGFILES["upload_script"] % self.timestamp
                    ),
                "demultiplex_script": (
                    ad_config.LOGFILES["demultiplex_script_logfile"] %
                    self.timestamp
                    ),
            }
        return logfiles_config

    def shutdown_logs(self):
        """
        To prevent duplicate filehandlers and system handlers close and remove
        all handlers for all log files that have a python logging object
        """
        for logger in self.loggers:
            for handler in logger.handlers[:]:
                logger.removeHandler(handler)
                handler.close()

    def _get_file_handler(self, filepath):
        file_handler = logging.FileHandler(filepath, mode="a", delay=True)
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(self._formatter)
        return file_handler

    def _get_syslog_handler(self):
        syslog_handler = logging.handlers.SysLogHandler(address="/dev/log")
        syslog_handler.setLevel(logging.DEBUG)
        syslog_handler.setFormatter(self._formatter)
        return syslog_handler

    def _get_stream_handler(self):
        stream_handler = logging.StreamHandler(sys.stdout)
        stream_handler.setLevel(logging.DEBUG)
        stream_handler.setFormatter(self._formatter)
        return stream_handler

    def _get_logger(self, name, filepath):
        """
        Returns a Python logging object

        Args:
            name(str): Logger name
            filepath(str): Logfile path
        """
        logger = logging.getLogger(name)
        logger.filepath = filepath
        logger.setLevel(logging.DEBUG)
        logger.addHandler(self._get_file_handler(filepath))
        logger.addHandler(self._get_syslog_handler())
        logger.addHandler(self._get_stream_handler())
        return logger
