# Toolbox

This module contains functions and classes that are shared across multiple scripts. If
any changes are made to these functions and classes, all scripts should be comprehensively tested.

## Protocol

The script contains many functions whose protocol can be identified by reading the individual docstrings. The main class in this module is the RunfolderObject() class which functions as follows:
1. Adds all runfolder-specific paths and qualities that need to be accessed by other modules as class attributes
2. add_runfolder_loggers(script) can be used to add runfolder-specific loggers to the RunfolderObject object as an attribute

## Configuration

Settings are imported from [ad_config.py](../config/ad_config.py).

## Usage

This script is configured to be used as a module import as per the following example:

```python
from toolbox import toolbox

# Create runfolder object
rf_obj = toolbox.RunfolderObject(folder_name, ad_config.timestamp)
```

## Logging

The RunfolderObject class adds loggers to the runfolder object using ad_logger.RunfolderLoggers.

## Testing

**N.B. Tests and test cases/files MUST be maintained and updated accordingly in conjunction with script development**

This script does not yet have a test suite.
