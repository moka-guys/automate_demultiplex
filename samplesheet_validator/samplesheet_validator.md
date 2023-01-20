# Samplesheet Validator
Checks sample sheet naming and contents. Carries out a series of checks on the sample sheet and collecting any errors 
that it identifies (ValidSamplesheet.errors). It also identifies whether or not a run is a TSO run from the sample 
sheet (ValidSamplesheet.tso).

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

Therefore, samplesheets should conform with the following requirements:

## Configuration

Settings are imported from [ad_config.py](../ad_config.py)

## Logging
The script itself does not perform logging, however it collects error messages as it runs. When it is imported by the 
demultiplex.py and run, these error messages are output to a log file if there are any present.

## Alerts

N/A - see above

## Testing

**N.B. Tests and test cases/files MUST be maintained and updated accordingly in conjunction with script development**

The script has a full test suite ([test_samplesheet_validator.py](../test/test_samplesheet_validator.py), with test 
files stored in [/test/test_files](../test/test_files)). These tests should be run before pushing any code to ensure all tests in the GitHub Actions workflow pass. Similarly, the following
command should be run before pushing code to identify and rectify any style inconsistencies:

`flake8 . --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics`