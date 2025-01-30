# Automate demultiplex logging

This module creates objects that are used to write messages to the syslog, stream and log files. It is imported by other scripts within the repository.

## Protocol

The script has some standalone functions:

* get_logging_formatter() returns the formatter used for logging across all scripts
* set_root_logger() sets up the root logger and adds a stream handler and syslog handler (we only want to add these handlers once, to the root logger, otherwise the log messages written to the terminal / syslog will be duplicated for each logger added)
* shutdown_logs(logger) is used to close and remove all handlers for a logging object

### AdLogger Class

The AdLogger class creates a Python logging object with custom attributes and a file handler, syslog handler and stream handler.

### SensitiveFormatter Class

This removes sensitive information (authentication keys) in log messages (preventing them from being entered into rapid7) using regex. It inherits the properties and methods from logging.Formatter. It is used by the AdLogger class. 

### RunfolderLoggers Class

Creates a RunfolderLoggers object that contains various loggers required by the script that calls it. The loggers created are dictated by the logfiles_config dict provided as input. The class adds an AdLogger object for each logger specified in the logfiles_config and assigns it as an attribute. In this way the RunfolderLoggers object attributes can be used to write to the log files.

## Usage

This script is configured to be used as a module import as per the following examples:

### Example 1 - script-level loggers
```python
self.script_logger = ad_logger.AdLogger(  # Create script level loggers
    __package__, "sw", toolbox.return_scriptlog_config()['sw']
).get_logger()

self.script_logger.info(
    self.script_logger.log_msgs["runfolder_identified"], folder
)
```

### Example 2 - runfolder-level loggers
```python

logfiles_config = {
    "sw": sw_runfolder_logfile,
    "demux": demultiplex_runfolder_logfile,
    "backup": upload_runfolder_logfile,
    "bclconvert2": bclconvertlog_file,
    "ss_validator": samplesheet_validator_logfile,
}

loggers_obj = ad_logger.RunfolderLoggers(__package__, runfolder_name, logfiles_config)
loggers = loggers_obj.get_loggers()

loggers["sw"].info(
    loggers["sw"].log_msgs["recognised_panno"],
    sample_name,
    pannum,
)
```

## Logging

No log is written to as this module is creating the logger.

## Alerts

No alerts are triggered by this module, as it is creating the logger that writes the logs that are used for rapid7 pattern detection.

## Testing

**N.B. Tests and test cases/files MUST be maintained and updated accordingly in conjunction with script development**

This script has a full test suite:
* [test_ad_logger.py](../test/test_ad_logger.py)
  
These tests should be run before pushing any code to ensure all tests in the GitHub Actions workflow pass.
