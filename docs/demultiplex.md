# Demultiplexing

The [demultiplex.py](../demultiplex.py) script performs demultiplexing, and also performs
samplesheet validation on runs that have not yet been demultiplexed to act as an early warning
system for samplesheet errors. It does this by calling the
[samplesheet_validator.py](../samplesheet_validator.py) module, which makes use of the
[seglh-naming](https://github.com/moka-guys/seglh-naming) library.

[demultiplex.py](../demultiplex.py) collects runfolders in a given directory and runs a set of
checks to determine whether demultiplexing is required for that runfolder.

## Protocol

The following criteria must be met:

1. The bcl2fastq logfile `bcl2fastq2_output.log` is absent (demultiplexing not yet performed).
bcl2fastq stdout and stderr streams are written to this file.
2. Sequencing is complete (presence of `RTAComplete.txt` file created by the sequencer when
sequencing is complete)
3. bcl2fastq is installed on the workstation
4. Samplesheet does not contain any errors that would cause demultiplexing to fail - checks are
carried out by the
[samplesheet_validator.py](samplesheet_validator.py) and the absence of error messages for specific
tests is checked:
   * Sample sheet is present
   * Samplesheet name is valid (validates using the
   [seglh-naming](https://github.com/moka-guys/seglh-naming) library)
   * Samplesheet is not empty
   * Samplesheet contains the minimum expected `[Data]` section headers:
   `Sample_ID, Sample_Name, index`
   * Sample name does not contain any illegal characters (in case this was not rectified after the
   early warning checks as this will cause bcl2fastq to fail)

If a runfolder meets these initial criteria:

* If the sequencer does not require an integrity check, it skips straight to `run_demultiplexing()`
* If the sequencer does require an integrity check the following requirements must be met for
`run_demultiplexing()` to be called:
  1. Checksum file generated by
  [integrity checking script
  ](https://github.com/moka-guys/integrity_checking/blob/master/sequencer_checksum.py)
must be present
  2. The run has not failed a previous integrity check performed by this script
  3. The md5 checksums in the checksum file match. This verifies the integrity between the
  workstation and sequencer

`run_demultiplexing()` then performs demultiplexing tasks:

* Create demultiplexing log file to prevent simultaneous attempt on the next run of the script
(bcl2fastq is slow to create the logfile)
* If the run is a tso run, creates a tso bcl2fastq log file but does not demultiplex
* Otherwise, demultiplexes all other runs that get this far using `bcl2fastq2 (v2.20)`

If the script has processed any runfolders, it renames the logfile with the runfolder names

## Configuration

Settings are imported from [ad_config.py](../ad_config.py).

## Logging

| Alias | Description | Filename | Location |
|------|----------|---------|-----------|
|Demultiplex Log|Records the decisions made for multiple runfolders each time the script is run|`TIMESTAMP_RUNFOLDER-NAME_demultiplex_script_log.txt`| /usr/local/src/mokaguys/automate_demultiplexing_logfiles/Demultiplexing_log_files/ |
|Bcl2fastq output| STDOUT and STDERR from bcl2fastq | `bcl2fastq2_output.log` | Within the runfolder |
|Demultiplex output| STDERR and STDOUT from demultiplexing script. Includes errors from the cronjob | `TIMESTAMP.txt` | /usr/local/src/mokaguys/automate_demultiplexing_logfiles/Demultiplexing_stdout |

## Alerts

Logs from this script containing the follow strings will trigger alerts to the #moka-alerts binfx
slack channel:

* demultiplex_fail
* smartsheet_fail
* samplesheet_warning

## Testin

**N.B. Tests and test cases/files MUST be maintained and updated accordingly in conjunction with**
**script development**

The script has a full test suite ([test_samplesheet_validator.py](
  ../test/test_samplesheet_validator.py), with test files stored in [/test/test_files](
    ../test/test_files)). These tests should be run before pushing any code to ensure all tests in
    the GitHub Actions workflow pass. Similarly, the following command should be run before pushing
    code to identify and rectify any style inconsistencies:

`flake8 . --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics`