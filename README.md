# Automate Demultiplex

Scripts for routine analysis of clinical next generation sequencing (NGS) data at Viapath Genetics:

1. [demultiplex.py](demultiplex.py) - Demultiplex Illumina NGS data using `bcl2fastq2` [(guide)](docs/demultiplex.md)
2. [upload_and_setoff_workflows.py](upload_and_setoff_workflows.py) - Upload NGS data to DNANexus and trigger in-house 
workflows [(guide)](docs/upload_and_setoff_workflows.md)

The following modules are core dependencies:

* [automate_demultiplex_config.py](automate_demultiplex_config.py) - Configuration for all automate demultiplex scripts
* [decision_support_tool_inputs.py](decision_support_tool_inputs.py) - Print inputs required by decision support tool 
upload applications on DNANexus
* [samplesheet_validator.py](samplesheet_validator.py) - Validates naming and contents of samplesheets prior to 
demultiplexing. Uses the [seglh-naming](https://github.com/moka-guys/seglh-naming) package
* [adlogger.py](ad_logger.py) - Logging module, currently only used by 
[upload_and_setoff_workflows.py](upload_and_setoff_workflows.py)
* [git_tag.py](git_tag.py) - Retrieve git tag (script version) from the repository

Please read further documentation in [docs/](docs/) to learn more about each script.

## Seglh-naming installation

The [seglh-naming](https://github.com/moka-guys/seglh-naming) package should be installed using the requirements.txt 
file:

`pip install -r requirements.txt`

## Logging

Logfiles produced by automate demultiplex scripts are uploaded to the DNANexus project under 
`PROJECT:/RUNFOLDER/Logfiles`. See `docs/` for each script's logfile details.

## Alerts

Alerts are sent to the #moka-alerts binfx slack channel. In the event of a critical failure an email is sent to the 
moka-guys mailing list.

## Scheduling

Scripts are triggered by a cronjob on the linux workstation which can be updated using `sudo crontab -e`.

## License

Copyright 2022 Synnovis

Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with 
the License. You may obtain a copy of the License at

[http://www.apache.org/licenses/LICENSE-2.0](http://www.apache.org/licenses/LICENSE-2.0)

Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an 
"AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the 
specific language governing permissions and limitations under the License.