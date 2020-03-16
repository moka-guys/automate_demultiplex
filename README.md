# Automate Demultiplex

Scripts for routine analysis of clinical next generation sequencing (NGS) data at Viapath Genetics:

1. [demultiplex.py](demultiplex.py) - Demultiplex Illumina NGS data using `bcl2fastq2` [(guide)](docs/demultiplexing.md)
1. [upload_and_setoff_workflows.py](upload_and_setoff_workflows.py) - Upload NGS data to DNANexus and trigger in-house workflows [(guide)](docs/upload_and_setoff.md)

The following modules are core dependencies:

* [automate_demultiplex_config.py](automate_demultiplex_config.py) - Configuration for all automate demultiplex scripts
* [decision_support_tool_inputs.py](decision_support_tool_inputs.py) - Print inputs required by decision support tool upload applications on DNANexus
* [adlogger.py](ad_logger.py) - Logging module for automate demultipex script

## Logging

Logfiles produced by automate demultiplex scripts are uploaded to the DNANexus project under `PROJECT:/RUNFOLDER/Logfiles`. See `docs/` for each script's logfile details.

## Alerts

Alerts are sent to the #moka-alerts binfx slack channel. In the event of a critical failure an email is sent to the moka-guys mailing list.

## Scheduling

Scripts are triggered by a cronjob on the linux workstation which can be updated using `sudo crontab -e`.

## License

TBC