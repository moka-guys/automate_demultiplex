import os
import automate_demultiplex_config as config
import logging
import logging.handlers


def get_runfolder_log_config(runfolder, timestamp):
    #  Demultiplex script log has timestamp that differs from current time. Find first.
    any_demultiplex_logs = [
        os.path.join(config.demultiplex_logfiles, filename)
        for filename in os.listdir(config.demultiplex_logfiles)
        if runfolder.runfolder_name in filename
    ]
    demultiplex_log = any_demultiplex_logs.pop() if any_demultiplex_logs else None

    # Configuration for ADLoggers. Provides mapping between logger shorthand name and the logfile filepath.
    log_config = {
        "script": os.path.join(config.upload_agent_logfile, timestamp + "_.txt"),
        "project": os.path.join(
            config.DNA_Nexus_project_creation_logfolder + runfolder.runfolder_name + ".sh"
        ),
        "dx_run": runfolder.runfolder_dx_run_script,
        "demultiplex": demultiplex_log,
        "fastq_upload": os.path.join(runfolder.runfolderpath, config.upload_started_file),
        "backup": os.path.join(config.backup_runfolder_logfile, runfolder.runfolder_name + ".log",),
    }

    return log_config


class LOGFILE:
    def __init__(self, name, filepath):
        self.name = name
        self.filepath = filepath


class ADLoggers:

    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    def __init__(self, project, dx_run, demultiplex, fastq_upload, backup, script=None):
        # Logfiles the demultiplex script writes to
        self.script = self._get_ad_logger("automate_demultiplex", script)
        self.backup = self._get_ad_logger("backup_runfolder", backup)
        self._fastq_upload = (
            fastq_upload  # Fastq upload file created later using `add_fastq_upload`
        )
        # Logfiles not written to or bash files created by script. File_only skips file handler
        #  creation but still provides convenience attributes .name and .filename
        self.project = self._get_ad_logger("create_project", project, file_only=True)
        self.dx_run = self._get_ad_logger("dx_run", dx_run, file_only=True)
        self.demultiplex = self._get_ad_logger("demultiplex", demultiplex, file_only=True)

        # Container for all logfiles
        self.all = [self.script, self.project, self.dx_run, self.demultiplex, self.backup]

    def set_fastq_upload(self):
        self.fastq_upload = self._get_ad_logger("fastq_upload", self._fastq_upload)
        self.all.append(self.fastq_upload)

    def list_logfiles(self):
        return [logger.filepath for logger in self.all]

    def _get_file_handler(self, filepath):
        fh = logging.FileHandler(filepath, mode="a")
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(self.formatter)
        return fh

    def _get_syslog_handler(self):
        slh = logging.handlers.SysLogHandler(address="/dev/log")
        slh.setLevel(logging.DEBUG)
        slh.setFormatter(self.formatter)
        return slh

    def _get_ad_logger(self, name, filepath, file_only=False):
        """Returns automate demultiplex logger"""
        if file_only or filepath is None:
            return LOGFILE(name, filepath)
        logger = logging.getLogger(name)
        logger.filepath = filepath
        logger.setLevel(logging.DEBUG)
        logger.addHandler(self._get_file_handler(filepath))
        logger.addHandler(self._get_syslog_handler())
        return logger


if __name__ == "__main__":
    loggers = ADLoggers(None, None, None, None, None, script="test.log")
    print("Writing test to {} and syslog".format(loggers.script.filepath))
    loggers.script.info("This is a test")
    for logger in loggers.all:
        print(logger.name, logger.filepath)
