# Toolbox

This module contains functions and classes that are shared across multiple scripts. If any changes are made to these functions and classes, all scripts should be comprehensively tested.

## Protocol

The script contains many functions whose protocol can be identified by reading the individual docstrings. The classes in this module are listed below:
1. RunfolderObject:
    * An object with runfolder-specific properties
    * get_runfolder_loggers() function returns a dictionary of logger.Logging objects for the runfolder

2. RunfolderSamples
    * An object with properties derived from the samples names in the samplesheet

3. SampleObject
    * An object with sample-specific attributes


## Configuration

Settings are imported from [ad_config.py](../config/ad_config.py).

## Usage

This script is configured to be used as a module import as per the following example:

```python
from toolbox import toolbox

rf_obj = toolbox.RunfolderObject(folder_name, ad_config.timestamp)

loggers = rf_obj.get_runfolder_loggers(__package__)

rf_samples_obj = RunfolderSamples(rf_obj, loggers["demux"])

sample_obj = SampleObject(
    sample_name,
    rf_samples_obj.pipeline,
    rf_samples_obj.logger,
    rf_samples_obj.fastq_dir_path,
    rf_samples_obj.nexus_paths,
    rf_samples_obj.nexus_runfolder_suffix
)
```

## Testing

**N.B. Tests and test cases/files MUST be maintained and updated accordingly in conjunction with script development**

This script does not yet have a test suite.
