# Demutliplex.py tests

This directory contains test files used in the demultiplex test suite. 

test_runfolders contains runfolders used to test GetRunfolders().rundemultiplexrunfolders(), 
DemultiplexRunfolder.run_demultiplexing() and DemultiplexRunfolder.check_demultiplexing_required(), 
and GetRunfolders.loop_through_runs().

The test cases are described below.

## test_runfolders
| Runfolder                      | Details                                                                                                                                                                                                                                                                                       | Expected behaviour                                                                                           |
|--------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------------------|
| 999999_A01229_0000_00000TEST1  | bcl2fastq2_output.log (Demultiplexing already complete)                                                                                                                                                                                                                                       | demultiplexing_requried returns False                                                                        |
| 999999_A01229_0000_00000TEST2  | No flag files (Sequencing not finished)                                                                                                                                                                                                                                                       | demultiplexing_requried returns False                                                                        |
 | 999999_A01229_0000_00000TEST3  | RTAComplete.txt, invalid samplesheet present in test samplesheet dir with disallowed errors that would cause demultiplexing to fail (Sequencing complete but no processing has taken place yet)                                                                                               | demultiplexing_requried returns False                                                                        |
| 999999_M02631_0000_00000TEST4  | RTAComplete.txt, matching valid samplesheet present in test samplesheet dir, integrity check not required (Sequencing complete but no processing has taken place yet)                                                                                                                         | demultiplexing_requried returns True                                                                         |
| 999999_A01229_0000_00000TEST5  | RTAComplete.txt, matching valid samplesheet present in test samplesheet dir, integrity check required, but no checksum file (Sequencing complete but no processing has taken place yet)                                                                                                       | demultiplexing_requried returns False                                                                        |
| 999999_A01229_0000_00000TEST6  | RTAComplete.txt, matching valid samplesheet present in test samplesheet dir, integrity check required, md5checksum.txt present and contains integrity check fail string (Sequencing complete but no processing has taken place yet, previous integrity check has failed)                      | demultiplexing_requried returns False                                                                        |
| 999999_A01229_0000_00000TEST7  | RTAComplete.txt, matching valid samplesheet present in test samplesheet dir, integrity check required, md5checksum.txt present and contains matching checksums but no previously checked checksums string (Sequencing complete but no processing has taken place yet, integrity check passed) | demultiplexing_requried returns True                                                                         |
| 999999_A01229_0000_00000TEST8  | Matching valid samplesheet present in samplesheets dir containing TSO samples                                                                                                                                                                                                                 | run_demultiplexing returns False, self.run_processed == True                                                 |
| 999999_A01229_0000_00000TEST9  | Matching valid samplesheet that is not from a tso run                                                                                                                                                                                                                                         | run_demultiplexing returns True, self.run_processed == True (bcl2fastq command replaced by a dummy command)  |
| 999999_A01229_0000_0000TEST10  | RTAComplete.txt, samplesheet missing, integrity check required, md5checksum.txt present and contains matching checksums with a previously checked checksums string (Sequencing complete but no processing has taken place yet, integrity check passed) | demultiplexing_required returns False                                                                        |