# Demultiplexing

NGS runfolders that satisfy the following criteria are demultiplexed by `demultiplexing.py`:

1. `RTAcomplete.txt` is present, indicating that sequencing is complete.
1. `demultiplexlog.txt` is absent, indicating that demultiplexing has not been performed
1. A samplesheet named after the runfolder name is present in the `samplesheets/` folder

## Protocol
When a runfolder meets these criteria, the script calculated an md5 checksum to verify data integrity between the workstation and sequencer. Checksums for MiSeq runs are calculated by this script, whereas checksums for the NextSeq are calculated on the sequencer itself.

If the integrity check passes, samples are demlutiplexed using bcl2fastq2 (v2.20).

## Configuration

Settings are imported from `automate_demultiplex_config.py`.

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