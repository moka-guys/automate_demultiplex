# Demultiplexing

NGS runs are demultiplexed by `demultiplexing.py`. This module processes NGS runfolders that satisfy the following criteria:

1. Sequencing has finished, indicated by the **presence** of `RTAcomplete.txt`
1. Demultiplexing has not been performed, indicated by the **absence** of `demultiplexlog.txt`
1. A samplesheet containing the runfolder name is present in the `samplesheets/` folder

## Protocol
When a runfolder meets these criteria, the script calculated an md5 checksum to verify data integrity between the workstation and sequencer. Checksums for MiSeq runs are calculated by this script, whereas checksums for the NextSeq are calculated on the sequencer itself.

If the integrity check passes, samples are demlutiplexed using bcl2fastq2 (v2.20).

## Configuration

All settings are imported from `automate_demultiplex_config.py`.

## Logging

| Alias | Description | Filename | Location
|------|----------|---------|-----------|
|Demultiplex Log|Records the decisions made for multiple runfolders each time the script is run|`TIMESTAMP_RUNFOLDER-NAMES_demultiplex_script_log.txt`| /usr/local/src/mokaguys/automate_demultiplexing_logfiles/Demultiplexing_log_files/
|Bcl2fastq output| STDOUT and STDERR from bcl2fastq | `demulitplexlog.txt` | Within the runfolder
|Demultiplex output| STDERR and STDOUT from demultiplexing script. Includes errors from the cronjob | `TIMESTAMP.txt` | /usr/local/src/mokaguys/automate_demultiplexing_logfiles/Demultiplexing_stdout

## Alerts

Logs from this script containing the follow strings will trigger alerts to the #moka-alerts binfx slack channel:

* demultiplex_fail
* smartsheet_fail