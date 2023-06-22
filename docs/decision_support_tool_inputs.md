# Decision Support Tool Inputs

[decision_support_tool_inputs.py](../decision_support_tool_inputs.py) prints the required inputs for the congenica upload app for a sample workflow in a string format.

Inputs are specified in the format executionid.output_name. The execution IDs for the relevant workflow stages are retrieved using dx describe with the workflow analysis ID and stage ID. 

The script is currently configured to return the IDs for the BAM and VCF files for WES and Custom Panels samples. It prints the output in the correct format for the input arguments for the congenica upload app.

## Protocol


## Configuration

Settings are imported from [ad_config.py](../config/ad_config.py) and [panel_config.py](../config/panel_config.py).

## Usage

### Command line

```bash
usage: decision_support_tool_inputs.py [-h] -a ANALYSIS_ID -t {congenica} -p PROJECT

given an analysis-id will obtain the job ids for bam and vcf files for upload to the specified decision support tool

options:
  -h, --help            show this help message and exit
  -a ANALYSIS_ID, --analysis_id ANALYSIS_ID
                        workflow Analysis ID in format Analysis-abc123
  -t {congenica}, --tool {congenica}
                        decision support tool (currently only supports congenica)
  -p PROJECT, --project PROJECT
                        The DNAnexus project id in which the analysis is running
```



## Logging

| Alias | Description | Filename | Location |
| ------------------ | ------------------------------------------------------------------------------ | ----------------------------------------------------- | ---------------------------------------------------------------------------------- |
| decision_support | Records the logs from the script to a logfile specific to that DNAnexus project | `decision_support_script_log_RUNFOLDERNAME.log` | `/usr/local/src/mokaguys/automate_demultiplexing_logfiles/decision_support_tool_logfiles/` |


## Alerts

Logs from this script containing the follow strings will trigger alerts to the `moka-alerts` binfx slack channel:

* DST_FAIL

## Testing

**N.B. Tests and test cases/files MUST be maintained and updated accordingly in conjunction with script development**

This script does not yet have a test suite.
