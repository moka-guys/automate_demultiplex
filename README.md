# Automate Demultiplex Scripts

This repository contains the main scripts for routine analysis of clinical next generation sequencing (NGS) data at Viapath Genetics. These are as follows, and the documentation for each script can be found in [docs/](docs/) or using the links below:

1. [demultiplex.py](demultiplex.py) - Demultiplex (excluding TSO runs) and calculate cluster density for Illumina NGS data using `bcl2fastq2`
[(guide)](demultiplex/README.md)
2. [setoff_workflows.py](setoff_workflows.py) - Upload NGS data to DNAnexus and trigger in-house workflows [(guide)](setoff_workflows/README.md)
3. [congenica_inputs.py](congenica_inputs.py) - This script is called from the dx run script for samples requiring congenica upload (the dx run script is created by setoff_workflows.py). The script prints the inputs required by the congenica upload apps in DNAnexus [(guide)](congenica_inputs/README.md)


# Modules

The following modules are utilised by the above scripts, with the documentation for each within the corresponding subdirectory.

* [ad_email](ad_email) - Email sending module [(guide)](ad_email/README.md)
* [ad_logger](ad_logger) - This module contains classes that create logging objects that write messages to the syslog, stream and log files. Used by other modules [(guide)](ad_logger/README.md)
* [config](config) - Contains configuration files [(guide)](config/README.md):
    - [ad_config](config/ad_config.py) - Contains general configuration
    - [log_msgs_config](config/log_msgs_config.py) - Contains messages used by [ad_logger](ad_logger)
    - [panel_config](config/panel_config.py) - Contains panel specific configuration
* [samplesheet_validator](samplesheet_validator) - Validates naming and contents of samplesheets prior to demultiplexing. Uses the [seglh-naming](https://github.com/moka-guys/seglh-naming) package [(guide)](samplesheet_validator/README.md)
* [toolbox](toolbox) - Contains classes and functions shared [(guide)](toolbox/README.md)
* [upload_runfolder](upload_runfolder) - Uploads an Illumina runfolder to DNAnexus [(guide)](upload_runfolder/README.md)

# Setup

Dependencies, which include the [seglh-naming](https://github.com/moka-guys/seglh-naming) package, should be insalled using the requirements.txt file:

```bash
pip3 install -r requirements.txt
```

Before running the script, the conda environment must be activated as follows:
```bash
conda activate python3.10.6
```

# Pytest

[test](test) contains test data and test scripts (these use pytest).

Tests can be executed using the following command. It is important to include the ignore flag to prevent pytest from scanning for tests through all test files, which slows down the tests considerably

```bash
pytest -v --ignore=test/demultiplex_test_files/ --cov=.
```

**N.B. Tests and test cases/files MUST be maintained and updated accordingly in conjunction with script development**
**These tests should be run before pushing any code to ensure all tests in the GitHub Actions workflow pass.**

Currently the test suite covers the following scripts/modules:
* [ad_email](ad_email)
* [ad_logger](ad_logger)
* [demultiplex.py](demultiplex.py)
* [samplesheet_validator](samplesheet_validator)

Suites for the following scripts/modules still require development:
* [setoff_workflows.py](setoff_workflows.py)
* [congenica_inputs.py](congenica_inputs.py)
* [upload_runfolder](upload_runfolder)
* [toolbox](toolbox)

Test datasets are stored in [/test/data](../test/data)

## Alerts

In production mode, alerts are sent to the moka-alerts binfx slack channel, whilst in testing mode they are sent to the moka-poo slack channel.

Alerts at level ERROR and above will appear in the relevant channel.

## Scheduling

Scripts are triggered by a cronjob on the linux workstation which can be updated using
`sudo crontab -e`.
