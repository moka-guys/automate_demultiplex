# Automate demultiplex logging

This module creates an AdLoggers object which is used to write messages to the syslog,
stream and log files.

It also has a sensitive formatter incorporated, which removes authentication keys from the both the stream and the syslog (preventing them from being entered into rapid7) using regex.

## Protocol

AdLoggers object creates a SensitiveFormatter to remove auth keys, then adds all loggers specified in the input logfiles config to the AdLoggers object (file, syslog and stream handlers). AdLoggers also has a shutdown_logs function to allow loggers to be removed preventing duplication of logging handlers.

## Configuration

This module has is own configuration file which contains settings specific to logging: [log_config.py](log_config.py).

## Usage

This script is configured to be used as a module import as per the following examples:

Example 1 - script level loggers
```python
import 
# Create script level loggers
script_logger = ad_logger.return_scriptlogger("usw", ad_config.TIMESTAMP)

script_logger.usw.info(
    script_logger.usw.log_msgs["script_start"],
    git_tag(),
    "script.py",
    extra={"flag": script_logger.usw.log_flags["info"] % "usw"},
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

loggers = ad_logger.AdLoggers(logfiles_config)

rf_obj.rf_loggers.usw.info(
    loggers.log_msgs["recognised_panno"],
    sample_name,
    pannum,
    extra={"flag": loggers.log_flags["info"] % "usw"},
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
