import automate_demultiplex_config as config
import logging
import logging.handlers

class LOGFILE():
    def __init__(self, name, filepath):
        self.name = name
        self.filepath = filepath

class ADLoggers():

    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    def __init__( self, project, dx_run, demultiplex, fastq_upload, backup, script=None):
        self.script = self._get_ad_logger('automate_demultiplex', script)
        self.project = self._get_ad_logger('create_project', project, file_only=True)
        self.dx_run = self._get_ad_logger('dx_run', dx_run, file_only=True)
        self.demultiplex = self._get_ad_logger('demultiplex', demultiplex, file_only=True)
        self.fastq_upload = self._get_ad_logger('fastq_upload', fastq_upload, file_only=True)
        self.backup = self._get_ad_logger('backup_runfolder', backup, file_only=True)
        # Container for all logfiles
        self.all = [self.script, self.project, self.dx_run, self.demultiplex, self.fastq_upload, self.backup]

    def list_logfiles(self):
        return [ logger.filepath for logger in self.all ]

    def _get_file_handler(self, filepath):
        fh = logging.FileHandler(filepath)
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(self.formatter)
        return fh

    def _get_syslog_handler(self):
        slh = logging.handlers.SysLogHandler(address = '/dev/log')
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

if __name__ == '__main__':
    loggers = ADLoggers(None, None, None, None, None, script='test.log')
    print('Writing test to {} and syslog'.format(loggers.script.filepath))
    loggers.script.info('This is a test')
    for logger in loggers.all:
        print(logger.name, logger.filepath)