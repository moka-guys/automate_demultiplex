# Backup runfolder script

Uploads an Illumina runfolder to DNAnexus.

## Protocol

* The script parses the input parameters, asserting that the given runfolder exists.
* If the `--project_id` option is given, the script attempts to find a matching DNAnexus project. Otherwise, it looks for a single project matching the runfolder name. If more or less than 1 project matches, the script logs an error and exits.
* The runfolder is traversed and a list of files in each folder is obtained. If any comma-separated strings passed to the `--ignore` argument are present within the filepath, or filename the file is excluded.
* The DNAnexus `ua` utility is used to upload files in batches of 100 at a time. The number of upload tries is set to 100 with the `--tries` flag.
* Orthogonal tests are performed to:
    * A count of files that should be uploaded (using the ignore terms if provided)
    * A count of files in the DNA Nexus project
    * (If relevant) A count of files in the DNA Nexus project containing a pattern to be ignored. NB this may not be accurate if the ignore term is found in the result of dx find data (eg present in project name)
* Logs from this and the script are written to a logfile, named "runfolder_backup_runfolder.log". A destination for this file can be passed to the `--logpath` flag.

Logfiles produced by automate demultiplex scripts are uploaded to the DNAnexus project under `PROJECT:/RUNFOLDER/Logfiles`.

## Configuration

Settings are imported from [ad_config.py](../config/ad_config.py).

## Usage

This tool requires the DNAnexus utilities `ua` (upload agent) and `dx` (DNAnexus toolkit) to be available in the system PATH. Python3 is required, and this tool uses packages from the standard library.

The script can be either imported as a module, or run directly from the command line.

### Command line

```bash
usage: python3 -m backup_runfolder [-h] -r RUNFOLDER_NAME [-a AUTH_TOKEN] [--ignore IGNORE] [-p PROJECT_ID]

options:
  -h, --help            show this help message and exit
  -r RUNFOLDER_NAME, --runfolder_name RUNFOLDER_NAME
                        Workstation runfolder name
  -a AUTH_TOKEN, --auth_token AUTH_TOKEN
                        A string or file containing a DNAnexus authorisation key used to access the DNAnexus project. If not specified, the config-specified authtoken will be used by default
  --ignore IGNORE       Comma-separated list of patterns which prevents the file from being uploaded if any pattern is present in filename or filepath.
  -p PROJECT_ID, --project_id PROJECT_ID
                        The ID of an existing DNAnexus project for the given runfolder
```

### Module import

When run as a module import, the above inputs are supplied in the following format:

```python
# Dictionary containing dnanexus project name and id
nexus_identifiers = {
    "proj_name": project_name,
    "proj_id": project_id,
    }

UACaller(
    runfolder_name,
    ignore,
    self.rf_obj.rf_loggers,  # RunfolderLoggers object (created by ad_logger.py)
    self.rf_obj.dnanexus_apikey,
    nexus_identifiers,  # Optional
)
```

nexus_identifiers is an optional input - if not supplied, the script will search for
the matching project in DNAnexus using the runfolder name.

## Logging
| Alias | Description | Filename | Location |
| ------------------ | ------------------------------------------------------------------------------ | ----------------------------------------------------- | ---------------------------------------------------------------------------------- |
| backup | Records the logs from the backup runfolder script | `RUNFOLDERNAME_backup_runfolder.log` | `/usr/local/src/mokaguys/automate_demultiplexing_logfiles/backup_runfolder_script_logfiles/` |
| upload_agent | Records upload agent logs (stdout and stderr of the upload agent) | `DNANexus_upload_started.txt` | Within the runfolder |

## Alerts

Logs from this script containing the follow strings will trigger alerts to the `moka-alerts` binfx slack channel:

* BR_FAIL

## Testing

**N.B. Tests and test cases/files MUST be maintained and updated accordingly in conjunction with script development**

This script does not yet have a test suite.
