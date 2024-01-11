# Testing module

This module contains pytest scripts for testing the various modules within this repository. It also contains the data that is used for these test cases.

* [automate_demultiplexing_logfiles](data/automate_demultiplexing_logfiles/) - this contains subdirectories for storing logfiles created during testing (these folders are copied over to a temporary directory at the start of each test)
* [demultiplex_test_files](data/demultiplex_test_files/) - test cases used by test_demultiplex.py
* [samplesheets](data/samplesheets) - samplesheet test cases, used by test_samplesheet_validator.py and test_demultiplex.py
* 

## Running the tests

Tests can be executed using the following command. It is important to include the ignore flag to prevent pytest from scanning for tests through all test files, which slows down the tests considerably

```bash
python3 -m pytest -v --cov=. --ignore=test/demultiplex_test_files/
```

## Demultiplex.py tests

This directory contains test files used in the demultiplex test suite.



test_runfolders contains runfolders used to test GetRunfolders().rundemultiplexrunfolders(), 
DemultiplexRunfolder.run_demultiplexing() and DemultiplexRunfolder.check_demultiplexing_required(), 
and GetRunfolders.loop_through_runs().

The test cases are described below.


### Test SampleSheets

Lone samplesheet test cases are detailed below. These have been created for the purpose of testing samplesheet related functions in the demultiplex script (valid_samplesheet and no_disallowed_sserrs). The test cases are as follows:

#### [Valid SampleSheets](data/samplesheets/valid)

| SampleSheet name | Run Type |
| ---- | -------- |
| 210408_M02631_0186_000000000-JFMNK_SampleSheet.csv | SNP |  # DONE
| 210917_NB551068_0409_AH3YNFAFX3_SampleSheet.csv | Custom Panel |  # DONE
| 221021_A01229_0145_BHGGTHDMXY_SampleSheet.csv | TSO500 |  # DONE
| 221024_A01229_0146_BHKGG2DRX2_SampleSheet.csv | WES Skin |  # DONE

#### [Invalid SampleSheets](data/samplesheets/invalid/)
# TODO check if these cover all cases

| SampleSheet Name | Details | Expected behaviour |
| ---- | ------- | ------------------ |
| 21aA08_A01229_0040_AHKGTFDRXY_SampleSheet.csv | Empty SampleSheet with invalid name (letter in date) |
| 21108_A01229_0040_AHKGTFDRXY_SampleSheet.csv | Empty SampleSheet with invalid name (date too short) |
| 220413_A01229_0032_AHGKBIEKFR_SampleSheet.csv | Empty SampleSheet |
| 200817_NB068_0009_AH3YERAFX3_SampleSheet.csv | Custom Panel SampleSheet with invalid name (invalid sequencer ID), invalid contents (invalid header, invalid sample names, non-matching sample names, invalid pan number, invalid runtype) |  # DONE
| 210513_M02631_0236_000000000-JFMNK_SampleSheet.csv | SNP SampleSheet with invalid characters in the sample name |
| 220404_B01229_0348_HFGIFEIOPY_SampleSheet.csv | TSO SampleSheet with invalid name (invalid sequencer ID), invalid contents (invalid header, invalid sample names, non-matching sample names, invalid pan number, invalid runtype) | # DONE
| 220408_A02631_0186_000000000-JLJFE_SampleSheet.csv | SNP SampleSheet with invalid contents (invalid header, invalid sample names, non-matching sample names, invalid pan number, invalid runtype) |  # DONE
| 2110915_M02353_0632_000000000-K242J_SampleSheet.csv | SNP  SampleSheet with invalid name (date too long), invalid contents (invalid header, invalid sample names, non-matching sample names, invalid pan number, invalid runtype) |  # DONE

### test_runfolders
| Runfolder                     | Details                                                                                                                                                                                                                                                                                                                                                                        | Expected behaviour                                                                                          |
| ----------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ----------------------------------------------------------------------------------------------------------- |
| 999999_A01229_0000_00000TEST1 | bcl2fastq2_output.log (Demultiplexing already complete)                                                                                                                                                                                                                                                                                                                        | demultiplexing_requried returns False                                                                       |
| 999999_A01229_0000_00000TEST2 | No flag files (Sequencing not finished)                                                                                                                                                                                                                                                                                                                                        | demultiplexing_requried returns False                                                                       |
| 999999_A01229_0000_00000TEST3 | RTAComplete.txt, invalid samplesheet present in test samplesheet dir with disallowed errors that would cause demultiplexing to fail (Sequencing complete but no processing has taken place yet)                                                                                                                                                                                | demultiplexing_requried returns False                                                                       |
| 999999_M02631_0000_00000TEST4 | RTAComplete.txt, matching valid samplesheet present in test samplesheet dir, InterOp and RunInfo.xml files for Picard CollectIlluminaLaneMetrics calculation, integrity check not required (Sequencing complete but no processing has taken place yet)                                                                                                                         | demultiplexing_requried returns True                                                                        |
| 999999_A01229_0000_00000TEST5 | RTAComplete.txt, matching valid samplesheet present in test samplesheet dir, integrity check required, but no checksum file (Sequencing complete but no processing has taken place yet)                                                                                                                                                                                        | demultiplexing_requried returns False                                                                       |
| 999999_A01229_0000_00000TEST6 | RTAComplete.txt, matching valid samplesheet present in test samplesheet dir, integrity check required, md5checksum.txt present and contains integrity check fail string (Sequencing complete but no processing has taken place yet, previous integrity check has failed)                                                                                                       | demultiplexing_requried returns False                                                                       |
| 999999_A01229_0000_00000TEST7 | RTAComplete.txt (sequencing complete) , matching valid samplesheet present in test samplesheet dir, InterOp and RunInfo.xml files for Picard CollectIlluminaLaneMetrics calculation, integrity check required, md5checksum.txt present and contains matching checksums but no previously checked checksums string (Sequencing complete but no processing has taken place yet, integrity check passed) | demultiplexing_required returns True                                                                        |
| 999999_A01229_0000_00000TEST8 | Matching valid samplesheet present in samplesheets dir containing TSO samples                                                                                                                                                                                                                                                                                                  | run_demultiplexing returns False, self.run_processed == True                                                |
| 999999_A01229_0000_00000TEST9 | RTAComplee.txt (sequencing complete), Matching valid samplesheet present in samplesheets dir containing non-TSO | run_demultiplexing returns True, self.run_processed == True (bcl2fastq2 command replaced by a dummy command) |
| 999999_A01229_0000_0000TEST10 | RTAComplete.txt (sequencing complete), samplesheet missing, integrity check not required (md5checksum.txt present and contains matching checksums with a previously checked checksums string - processing has taken place, integrity check passed)                                                                                                                             | demultiplexing_required returns False                                                                       |
| 999999_A01229_0000_0000TEST11 | RTAComplete.txt, samplesheet present and contains TSO samples, integrity check required (md5checksum.txt present and contains matching checksums but no previously checked checksums string - no processing has taken place)                                                                                                                                                   |                                                                                                             | demultiplexing_required returns True |
