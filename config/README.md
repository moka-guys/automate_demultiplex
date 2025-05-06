# Config

This module contains python configuration files, which are imported by other modules within the repository

## Protocol

### Ad_config

Automate demultiplex configuration. Contains general settings, and the following classes collating the settings required per module:

- AdEmailConfig
- AdLoggerConfig
- DemultiplexConfig
- SWConfig
- ToolboxConfig
- URConfig

### Log_msgs_config

Config file for logging module (imported by ad_logger module). Contains settings specific to logging. The LOG_MSGS dictionary contains both general messages which are used across multiple modules, and also logfile-specific messages:
- Ad_email
- Demultiplex
- ss_validator
- sw
- backup

### Panel_config

The panel config file contains the panel numbers and panel properties, which are used by the setoff_workflows script.

The PANEL_DICT is built up in stages using various other dictionaries to reduce repetition. The base dictionary is the DEFAULT_DICT, which is incorporated into the CAPTURE_PANEL_DICT, which are then imported into the PANEL_DICT. The dictionaries POLYEDGE_INPUTS and CONGENICA_CREDENTIALS are also imported into the PANEL_DICT.

Panel number lists are created from the PANEL_DICT, assimilating pan numbers from the PANEL_DICT which meet the required criteria to be included in that list.

- SNP does not have R numbers (test_number) as it is an identity check for the GMS SMS
- Panels for WES (analysed in Congenica) and TSO500 (analysed in QCII), and ArcherDX (analysed in Archer software), are applied at the point of analysis, so R and M numbers (test_number) for these are not listed below. These pan numbers do not necessarily refer to bed files but rather project configuration (e.g. DNAnexus instances, project layout etc.)
- Development runs have two options for pan numbers, one for runs that require standard processing with bcl2fastq and one for runs that require manual processing as they have UMIs

| Dictionary key | Details |
|----------------|----------|
| panel_name    | Name of capture panel |
| pipeline   |  Name of pipeline |
| runtype  | Type of run |
| sample_prefix | Expected string at front of sample name |
| capture_pan_num | Pan number of capture panel bedfile (used for RPKM). False if RPKM not run |
| hsmetrics_bedfile | bedfile filename, or False |
| sambamba_bedfile | bedfile filename, or False. Coverage BED |
| variant_calling_bedfile | bedfile filename, or False |
| FH  | True if requires PRS analysis, False if not |
| rpkm_bedfile | bedfile filename, or False |
| capture_type | Amplicon or Hybridisation |
| multiqc_coverage_level | Value |
| clinical_coverage_depth | Value, or False. Used as input for sambamba |
| coverage_min_basecall_qual | Value or False. Sambamba minimum base quality |
| coverage_min_mapping_qual | Value or False. Sambamba minimum mapping quality |
| masked_reference | projectid:fileid, or False |
| test_number | R or M number, or false if no specific number |
| congenica_project | False = no upload. Number = normal. SFTP = sftp upload |
| congenica_credentials | 'Viapath' or 'StG'. False = Congenica app not used |
| congenica_IR_template | 'priority' or 'non-priority'. False = Congenica app not used |
| polyedge | False if app not required, subdictionary containing app inputs if it is required |
| ed_readcount_bedfile | False if app not required, panel bed file if required |
| ed_bam_str | String to use to search for BAM files
| ed_samplename_str | String to use to name Exomedepth ouptut
| ed_cnvcalling_bedfile | None if app not required, R-number specific bedfile if required |
| dry_lab | True if required to share with dry lab, None if not |
| dry_lab_only | Used to determine whether to include the TSO pan number in the duty_csv pan number list |
| drylab_dnanexus_id | False if not required to share with other users, user ID string if needs sharing |
| umis  | True if run has UMIs |

## Usage

This script is configured to be used as a module import as per the following examples:
```python
from config import ad_config
```

## Logging

No log is written to as this module contains only configuration files.

## Testing

This module has no tests.
