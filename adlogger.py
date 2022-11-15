"""adlogger.py

Automate demultiplex logging.
"""
import logging
import logging.handlers
import os

import automate_demultiplex_config as config


def get_runfolder_log_config(runfolder, timestamp):
    """Return an ADLogger config for a runfolder.

    Args:
        runfolder(upload_and_setoff_workflows.RunfolderObject): A runfolder
        timestamp(str): Timestamp as str("{:%Y%m%d_%H%M%S}".format(datetime.datetime.now()))
    Returns:
        log_config(dict): A dictionary of arguments for ADLoggers
    """

    # Find the demultiplex logfile for the runfolder.
    # Logfile name contains demultiplex timestamp which is unknown at this point.
    # Search for any demultiplex logfiles matching the runfodler name and return the first.
    any_demultiplex_logs = [
        os.path.join(config.demultiplex_logfiles, filename)
        for filename in os.listdir(config.demultiplex_logfiles)
        if runfolder.runfolder_name in filename
    ]
    demultiplex_log = any_demultiplex_logs.pop() if any_demultiplex_logs else None

    # Configuration for ADLoggers.
    # Dictionary where keys are ADLoggers.__init__ arguments and values are logfile paths.
    log_config = {
        "script": os.path.join(config.upload_and_setoff_workflow_logfile, timestamp + "_upload_and_setoff_workflow.log"),
        "project": os.path.join(
            config.DNA_Nexus_project_creation_logfolder + runfolder.runfolder_name + ".sh"
        ),
        "dx_run": runfolder.runfolder_dx_run_script,
        "demultiplex": demultiplex_log,
        "upload_agent": os.path.join(
            runfolder.runfolderpath, config.upload_started_file
        ),
        "backup": os.path.join(
            config.backup_runfolder_logfile,
            runfolder.runfolder_name + "_backup_runfolder.log",
        ),
    }

    return log_config


class DataOnlyLogger:
    """Carry name and filepath for logfiles that are not written to.

    Args:
        name(str): Logfile shorthand name
        filepath(str): Logfile filepath
    """
    def __init__(self, name, filepath):
        self.name = name
        self.filepath = filepath


class ADLoggers():
    """Access all logfiles uploaded to DNANexus as part of automate demultiplex scripts.

    Args:
        project(str): Path to DNANexus create project bash script
        dx_run(str): Path to dx run commands
        demultiplex(str): Path to logfile of decisions made during demultiplexing script
        fastq_upload(str): Path to DNANexus_Upload_started.txt in runfolder
        backup(str): Path to logfile for backing up rest of runfolder.
        script(str): Path to logfile for python script that calls ADLogger.
    """
    # Define log string format for all loggers
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    def __init__(self, project, dx_run, demultiplex, upload_agent, backup, script=None):
        # Logfiles to be written to by upload_and_setoff_workflows
        self.script = self._get_ad_logger('automate_demultiplex', script)
        self.upload_agent = self._get_ad_logger('upload_agent', upload_agent)
        self.backup = self._get_ad_logger('backup_runfolder', backup)
        # Get mock objects for files that are uploaded to DNANexus but not written to by loggers.
        self.project = self._get_ad_logger("create_project", project, file_only=True)
        self.dx_run = self._get_ad_logger("dx_run", dx_run, file_only=True)
        self.demultiplex = self._get_ad_logger(
            "demultiplex", demultiplex, file_only=True
        )

        # Container for all logfiles
        self.all = [
            self.script,
            self.project,
            self.dx_run,
            self.demultiplex,
            self.backup,
        ]

    def shutdown_logs(self):
        """
        To prevent duplicate filehandlers and system handlers close and remove all handlers
        """
        script_handlers = self.script.handlers[:]
        for handler in script_handlers:
            handler.close()
            self.script.removeHandler(handler)
        upload_agent_handlers = self.upload_agent.handlers[:]
        for handler in upload_agent_handlers:
            handler.close()
            self.upload_agent.removeHandler(handler)

        logging.shutdown()

    def list_logfiles(self):
        return [logger.filepath for logger in self.all]

    def _get_file_handler(self, filepath):
        fh = logging.FileHandler(filepath, mode='a', delay=True)
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(self.formatter)
        return fh

    def _get_syslog_handler(self):
        slh = logging.handlers.SysLogHandler(address='/dev/log')
        slh.setLevel(logging.DEBUG)
        slh.setFormatter(self.formatter)
        return slh

    def _get_ad_logger(self, name, filepath, file_only=False):
        """Returns a python logging object for automate demultiplex scripts.

        Args:
            name(str): Logger name
            filepath(str): Logfile path
            file_only(bool): If true, return an object with the .name and .filepath attributes only
                Useful to attach logfiles that require upload to DNANexus but are not written to.
        """
        if file_only or filepath is None:
            return DataOnlyLogger(name, filepath)
        logger = logging.getLogger(name)
        logger.filepath = filepath
        logger.setLevel(logging.DEBUG)
        logger.addHandler(self._get_file_handler(filepath))
        logger.addHandler(self._get_syslog_handler())
        return logger


if __name__ == '__main__':
    # Example ADLogger instance
    loggers = ADLoggers(None, None, None, None, None, script='test.log')
    # Example logging with script
    loggers.script.info(
        "This is a test. Writing to {} and syslog.".format(loggers.script.filepath)
    )

    # Example listing all logfile paths
    for logger in loggers.all:
        print(logger.name, logger.filepath)
