# Samplesheet Validator

Checks sample sheet naming and contents. Carries out a series of checks on the sample sheet and collects any errors 
that it identifies (SamplesheetCheck.errors_list). It also identifies whether or not a run is a TSO run from the sample 
sheet (SamplesheetCheck.tso).

Script is called by [demultiplex.py](../demultiplex.py)

## Protocol

Runs a series of checks on the sample sheet, collects any errors identified. Checks whether: 
* Sample sheet is present
* Samplesheet name is valid (validates using the [seglh-naming](https://github.com/moka-guys/seglh-naming/) library)
* Sequencer ID is in the list of allowed sequencer IDs in the config file (`sequencer_ids`)
* Samplesheet is not empty
* Samplesheet contains the minimum expected `[Data]` section headers: `Sample_ID, Sample_Name, index`
* `Sample_ID` and `Sample_Name` match 
* Sample name does not contain any illegal characters
* Sample name is valid (validates using the [seglh-naming](https://github.com/moka-guys/seglh-naming/) library)
* Pan numbers are in the list of allowed pan numbers in the config file (`panel_list`)
* Runtypes in the sample name are in the list of allowed runtypes in config file (`runtype_list`)
* Samplesheet contains any TSO samples

## Configuration

Settings are imported from [ad_config.py](../config/ad_config.py) and [panel_config](../config/panel_config.py).

## Usage

### Command line

```bash
usage: Used to validate a samplesheet using the seglh-naming conventions

Given an input samplesheet, will validate the samplesheet using seglh-naming conventions and output a logfile

options:
  -h, --help            show this help message and exit
  -s SAMPLESHEET_PATH, --samplesheet_path SAMPLESHEET_PATH
                        Path to samplesheet requiring validation
  -r RUNFOLDER_NAME, --runfolder_name RUNFOLDER_NAME
                        Name of runfolder, required for naming logfile
```
### Module import

```python
from samplesheet_validator import samplesheet_validator

sscheck_obj = samplesheet_validator.SamplesheetCheck(
    samplesheet_path, runfolder_name, ss_validator_logger
)
```

## Logging

Logging is performed using [ad_logger](../ad_logger/ad_logger.py). The following logs are written to:

| Alias | Description | Filename | Location |
| ------------------ | ------------------------------------------------------------------------------ | ----------------------------------------------------- | ---------------------------------------------------------------------------------- |
| ss_validator | Records runfolder-level logs for the samplesheet_validator script | `RUNFOLDERNAME_samplesheet_validator_script.log` | `/usr/local/src/mokaguys/automate_demultiplexing_logfiles/samplesheet_validator_script_logfiles/` |

The script also collects the error messages as it runs, which can be used by other modules when this script is used as an import.

## Testing

**N.B. Tests and test cases/files MUST be maintained and updated accordingly in conjunction with script development**

Test datasets are stored in [/test/data](../test/data). The script has a full test suite:
* [test_samplesheet_validator.py](../test/test_samplesheet_validator.py)

These tests should be run before pushing any code to ensure all tests in the GitHub Actions workflow pass.
