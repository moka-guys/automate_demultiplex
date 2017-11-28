from checksumdir import dirhash
import os

class Nextseq_Integrity_Check():
    def __init__(self):
        # path to the temp runfolder
        self.temp_folder = ""
        # path to the runfolder on the workstation
        self.mapped_workstation_folder = ""
        # the filename which denote sequencing has finished
        self.RTA_complete = "RTAcomplete.txt"
        # the file to write the checksums to
        self.output_file = "md5checksum.txt"

    def look_for_folder(self):
        """
        Loop through each runfolder in the nextseq temp folder.
        If it's finished sequencing the RTAComplete.txt file will be present.
        Check the integrity checks have not already been performed
        If not then pass the path workstation runfolder and the sequencer runfolder to the run_integrity_check function which will return the md5 hashes
        Both of these are written to a file on the workstation share 
        """
        # for each runfolder in temp folder
        for runfolder in self.temp_folder:
            # build path to the runfolder
            runfolder_path = os.join(self.temp_folder, runfolder)
            # build paths on the workstation
            workstation_runfolder = os.join(self.mapped_workstation_folder, runfolder)

            # check the run has finished by presense of RTA_complete in the runfolder
            if self.RTA_complete in os.listdir(runfolder_path):
                # check integrity check has not already been calculated
                if self.output_file not in os.listdir(workstation_runfolder):
                    # pass the folder paths to the integrity check function
                    workstation_md5 = self.run_integrity_check(workstation_runfolder)
                    sequencer_md5 = self.run_integrity_check(runfolder_path)
                    # write the checksums to the output file
                    with open(os.join(workstation_runfolder, self.output_file), 'w') as outputfile:
                        outputfile.write("workstation checksum (" + workstation_runfolder + ")=" + workstation_md5)
                        outputfile.write("sequencer checksum (" + runfolder_path + ")=" + sequencer_md5)

    def run_integrity_check(self,runfolder_for_checksum):
       """
       This function is passed the paths to a directory.
       A checksum is generated and returned
       """
        # calculate md5 checksum using dirhash package
        return dirhash(runfolder_for_checksum, 'md5')

def main():
    md5=Nextseq_Integrity_Check()
    md5.look_for_folder()
    
if __name__ =="__main__":
    main()