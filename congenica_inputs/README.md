# Decision Support Tool Inputs

[congenica_inputs.py](congenica_inputs.py) prints the required inputs for the Congenica upload app for a sample workflow in a string format.

Inputs are specified in the format executionid.output_name. The execution IDs for the relevant workflow stages are retrieved using dx describe with the workflow analysis ID and stage ID. 

The script is currently configured to return the IDs for the BAM and VCF files for WES and Custom Panels samples. It prints the output in the correct format for the input arguments for the Congenica upload app.

## Protocol

1. Creates a file dictionary of Congenica upload inputs if the workflow is a workflow that required Congenica upload
2. Sets the commands for retrieving the job ID for the VCF and BAM workflow stages
3. Gets the job IDs for the VCF and BAM workflow stages using the created commands 
4. Creates the input string for the Congenica app using the obtained job IDs and DNAnexus job output names
5. Prints the input string

## Configuration

Settings are imported from [ad_config.py](../config/ad_config.py) and [panel_config.py](../config/panel_config.py).

## Usage

This tool requires the `ua` (upload agent) and `dx` (DNAnexus toolkit) utility to be available in the system PATH. Python3 is required, and this tool uses packages from the standard library.

The script can be either imported as a module, or run directly from the command line.

### Command line

```bash
usage: Called from within the dx run commands to produce part of the dx run string for the Congenica uploads

Given an analysis-id, will obtain the job ids for bam and vcf files for upload to Congenica

options:
  -h, --help            show this help message and exit
  -a ANALYSIS_ID, --analysis_id ANALYSIS_ID
                        workflow Analysis ID in format Analysis-abc123
  -p PROJECT, --project PROJECT
                        The DNAnexus project name in which the analysis is running
  -r RUNFOLDER_NAME, --runfolder_name RUNFOLDER_NAME
                        Workstation runfolder name
```

## Logging

Logging is performed using [ad_logger](../ad_logger/ad_logger.py). The following logs are written to:

| Alias | Description | Filename | Location |
| ------------------ | ------------------------------------------------------------------------------ | ----------------------------------------------------- | ---------------------------------------------------------------------------------- |
| decision_support | Records the logs from the script to a logfile specific to that DNAnexus project | `RUNFOLDERNAME_decision_support_script.log` | `/usr/local/src/mokaguys/automate_demultiplexing_logfiles/decision_support_script_logfiles/` |

## Testing

**N.B. Tests and test cases/files MUST be maintained and updated accordingly in conjunction with script development**

This script does not yet have a test suite.
