# Automate demultiplex logging

This module creates objects that are used to write messages to the syslog, stream and log files.

It also has a sensitive formatter incorporated, which removes authentication keys from the both the stream and the syslog (preventing them from being entered into rapid7) using regex.

## Protocol

AdLoggers object creates a SensitiveFormatter to remove auth keys, then adds all loggers specified in the input logfiles config to the AdLoggers object (file, syslog and stream handlers). AdLoggers also has a shutdown_logs function to allow loggers to be removed preventing duplication of logging handlers.

## Usage

This script is configured to be used as a module import as per the following examples:

Example 1 - script level loggers
```python
script_logger = ad_logger.AdLogger(  # Create script level loggers
    'demultiplex', 'demultiplex', toolbox.return_scriptlogfile('demultiplex')
).get_logger()

script_logger.info(
    script_logger.log_msgs["script_start"],
    git_tag(),
    os.path.basename(os.path.dirname(__file__)),
)
```

Example 2 - runfolder level loggers
```python

logfiles_config = {
    "usw": upload_runfolder_logfile,
    "demultiplex": demultiplex_runfolder_logfile,
    "upload_agent": upload_agent_logfile,
    "backup": backup_runfolder_logfile,
    "project": proj_creation_script,
    "dx_run": runfolder_dx_run_script,
}

loggers = ad_logger.RunfolderLoggers(logfiles_config)

loggers.usw.info(
    loggers.usw.log_msgs["recognised_panno"],
    sample_name,
    pannum,
)
```

## Logging

No log is written to as this module is creating the logger.

## Alerts

No alerts are triggered by this module, as it is creating the logger that sends the alerts to rapid7.

## Testing

**N.B. Tests and test cases/files MUST be maintained and updated accordingly in conjunction with script development**

This script has a full test suite:
* [test_ad_logger.py](../test/test_ad_logger.py)
  
These tests should be run before pushing any code to ensure all tests in the GitHub Actions workflow pass.
