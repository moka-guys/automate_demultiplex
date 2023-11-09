# Toolbox

This module contains functions and classes that are shared across multiple scripts. If
any changes are made to these functions and classes, all scripts should be comprehensively tested.



* return_scriptlog_config() returns the script-level logfile configuration (dictionary containing logger names and logfile paths).
* return_rflog_config(runfoldername) returns the runfolder-level logfile configuration (dictionary containing runfolder logger names and logfile paths).