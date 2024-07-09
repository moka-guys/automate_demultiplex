
# upload_runfolder script

Uploads an Illumina runfolder to DNAnexus.

## Protocol

1. Searches DNAnexus for the project given as an input. If the input is 'None', searches for a project matching self.rf_obj.runfolder_name
2. If upload_rest_of_runfolder is called, calls methods to upload the rest of the runfolder (the runfolder minus the fastqs and several QC files):
    * Checks the runfolder exists
    * Creates a dictionary of all files and folders requiring upload, ignoring any files specified in the ignore string. Folders are the keys and files in the folders are values in list format
    * Builds upload commands to upload the rest of the runfolder using the DNAnexus `ua` utility. The number of upload tries is set to 100 with the `--tries` flag. The upload agent itself can take multiple files separated by a space, with the full path required for each file, and it has a max number of uploads of 1000 per command. The function in the script generates per-folder upload commands, with a maximum of 100 files uploaded per command
    * Orthogonal tests are performed to verify the upload:
        - A count of files that should be uploaded (using the ignore terms if provided)
        - A count of files in the DNA Nexus project
        - (If relevant) A count of files in the DNA Nexus project containing a pattern to be ignored. NB this may not be accurate if the ignore term is found in the result of dx find data (eg present in project name)
    * Counts the number of files to be uploaded and checks if any were uploaded to DNAnexus that should have been ignored
3. If upload_files is called directly, uploads the provided files to the runfolder                
4. The script uploads logfiles produced by this repository to the DNAnexus project under `PROJECT:/RUNFOLDER/automated_scripts_logfiles`.

* N.B. the script does not upload the SampleSheet from the SampleSheets directory, unless it has been copied into the runfolder first *

## Configuration

Settings are imported from [ad_config.py](../config/ad_config.py).

## Usage

This tool requires the DNAnexus utilities `ua` (upload agent) and `dx` (DNAnexus toolkit) to be available in the system PATH. Python3 is required, and this tool uses packages from the standard library.

The script can be either imported as a module, or run directly from the command line.

### Command line

```bash
usage: Upload user-specified runfolder to DNAnexus, providing an auth token, project ID to upload to, and any file patterns that should be ignored

Uploads runfolder to DNAnexus

options:
  -h, --help            show this help message and exit
  -r RUNFOLDER_NAME, --runfolder_name RUNFOLDER_NAME
                        Workstation runfolder name
  --ignore IGNORE       Comma-separated list of patterns which prevents the file from being uploaded if any pattern is present in filename or filepath.
  -p PROJECT_ID, --project_id PROJECT_ID
                        The ID of an existing DNAnexus project for the given runfolder
```

### Module import

When run as a module import, the above inputs are supplied in the following format:

**N.B. nexus_identifiers is an optional input - if not supplied, the script will search for
the matching project in DNAnexus using the runfolder name**

```python
# Dictionary containing DNAnexus project name and id
nexus_identifiers = {
    "proj_name": project_name,
    "proj_id": project_id,
    }

self.upload_runfolder = UploadRunfolder(
    rf_obj.rf_loggers["backup"],
    rf_obj.runfolder_name,
    rf_obj.runfolderpath,
    rf_obj.upload_flagfile,
    nexus_identifiers
)

result = self.upload_runfolder.upload_files(
    file_upload_dict[filetype]["cmd"],
    file_upload_dict[filetype]["files_list"],
)

ignore = "DNANexus_upload_started,add_runfolder_to_nexus_cmds"

self.upload_runfolder.upload_rest_of_runfolder(ignore)
```

## Logging
| Alias | Description | Filename | Location |
| ------------------ | ------------------------------------------------------------------------------ | ----------------------------------------------------- | ---------------------------------------------------------------------------------- |
| backup | Records the logs from the upload runfolder script | `RUNFOLDERNAME_upload_runfolder.log` | `/usr/local/src/mokaguys/automate_demultiplexing_logfiles/upload_runfolder_script_logfiles/` |
| upload_agent | Denotes runfolder upload has started | `DNANexus_upload_started.txt` | Within the runfolder |

## Testing

**N.B. Tests and test cases/files MUST be maintained and updated accordingly in conjunction with script development**

This script does not yet have a test suite.
