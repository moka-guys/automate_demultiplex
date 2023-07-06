# Automate Demultiplex Scripts

This repository contains the main scripts for routine analysis of clinical next generation sequencing (NGS) data at Viapath Genetics. These are as follows, and the documentation for each script can be found in [docs/](docs/) or using the links below:

1. [demultiplex.py](demultiplex.py) - Demultiplex Illumina NGS data using `bcl2fastq2`
[(guide)](docs/demultiplex.md)
2. [upload_and_setoff_workflows.py](upload_and_setoff_workflows.py) - Upload NGS data to DNAnexus and trigger in-house workflows [(guide)](docs/upload_and_setoff_workflows.md)
3. [decision_support_tool_inputs.py](decision_support_tool_inputs.py) - This script is called from the dx run script for samples requiring congenica upload (the dx run script is created by upload_and_setoff_workflows.py). The script prints the inputs required by the decision support tool upload apps in DNAnexus


# Modules

The following modules are utilised by the above scripts, with the documentation for each within the corresponding subdirectory.

* [ad_email](ad_email) - Email sending module
* [ad_logger](ad_logger) - This module contains classes that create logging objects that write messages to the syslog, stream and log files.
* [backup_runfolder](backup_runfolder) - Uploads an Illumina runfolder to DNAnexus
* [config] - contains configuration files
* [samplesheet_validator](samplesheet_validator) - Validates naming and contents of samplesheets prior to demultiplexing. Uses the [seglh-naming](https://github.com/moka-guys/seglh-naming) package
* [shared_functions](shared_functions) - Contains classes and functions shared
across multiple scripts
* [test][test] - Contains test data and test scripts (these use pytest)


# Setup

Dependencies, which include the [seglh-naming](https://github.com/moka-guys/seglh-naming) package, should be insalled using the requirements.txt file:

```bash
pip3 install -r requirements.txt
```

# Pytest

Tests can be executed using the following command. It is important to include the ignore flag to prevent pytest from scanning for tests through all test files, which slows down the tests considerably

```bash
python3 -m pytest -v --cov=. --ignore=test/demultiplex_test_files/
```

**N.B. Tests and test cases/files MUST be maintained and updated accordingly in conjunction with script development**
**These tests should be run before pushing any code to ensure all tests in the GitHub Actions workflow pass.**

Currently the test suite covers the following scripts/modules:
* [ad_email](ad_email)
* [ad_logger](ad_logger)
* [demultiplex.py](demultiplex.py)
* [samplesheet_validator](samplesheet_validator)

Suites for the following scripts/modules still require development:
* [upload_and_setoff_workflows.py](upload_and_setoff_workflows.py)
* [decision_support_tool_inputs.py](decision_support_tool_inputs.py)
* [backup_runfolder](backup_runfolder)
* [shared_functions](shared_functions)

Test datasets are stored in [/test/data](../test/data)


## Alerts

In producion mode, alerts are sent to the moka-alerts binfx slack channel, whilst in testing mode they are sent to the moka-poo slack channel.

## Scheduling

Scripts are triggered by a cronjob on the linux workstation which can be updated using
`sudo crontab -e`.
