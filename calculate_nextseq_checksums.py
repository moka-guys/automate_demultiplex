from checksumdir import dirhash # package to calculate checksums
import os # package to use and manipulate file paths
import datetime # for timestamp
import time # for sleep
import Tkinter # to open a window/message box
import tkMessageBox
import threading # to run a function in the background

class Nextseq_Integrity_Check():
    def __init__(self):
        # path to the temp runfolder
        self.temp_folder = "D://Illumina//NextSeq Control Software Temp"
        # path to the runfolder on the workstation
        self.mapped_workstation_folder = "Z://"
        # the filename which denote sequencing has finished
        self.RTA_complete = "RTAComplete.txt"
        # the file to write the checksums to
        self.output_file = "md5checksum.txt"
        # folder containing files which denote checksum is being calculated
        self.checksum_in_progress = "C://Users//sbsuser//integrity_check//checksums_inprogress"
        # variables for the runfolder paths
        self.workstation_runfolder = ""
        self.sequencer_runfolder = ""
        # message to display when the checksums are complete
        self.message_box_message=""
        # message box messages
        self.checksum_match="Integrity check complete please close this and continue"
        self.checksum_error="Problem with integrity check please speak to a Bioinformatician"
        
        

    def look_for_folder(self):
        """
        Loop through each runfolder in the nextseq temp folder.
        If it's finished sequencing the RTAComplete.txt file will be present.
        Check the integrity checks have not already been calculated
        Check the integrity checks is not currently being calculated
        Open a message box to display the a message that the nextseq shouldn't be used but is updated when complete
        """
        # for each runfolder in temp folder
        for runfolder in os.listdir(self.temp_folder):
            # build path to the runfolder
            self.sequencer_runfolder = os.path.join(self.temp_folder, runfolder)
            # build paths on the workstation
            self.workstation_runfolder = os.path.join(self.mapped_workstation_folder, runfolder)
            # create name for file to denote checksum in progress
            checksum_in_progress_file=runfolder+".txt"
            
    
            # check the run has finished by presense of RTA_complete in the runfolder
            if self.RTA_complete in os.listdir(self.sequencer_runfolder):
                # check integrity check has not already been calculated
                if self.output_file not in os.listdir(self.workstation_runfolder):
                    # check the checksum is not currently being calculated:
                    if checksum_in_progress_file not in os.listdir(self.checksum_in_progress):
                        # create a file to denote checksum in progress
                        with open(os.path.join(self.checksum_in_progress,checksum_in_progress_file),'w') as checksum_in_progress_file_path:
                            # create a timestamp
                            now=datetime.datetime.now()
                            # convert timestamp to string and write to file.
                            checksum_in_progress_file_path.write(str(now))
                        
                        # open a message box to say checksums being processed
                        window = Tkinter.Tk()
                        # set some properties of the message box
                        # message box size
                        window.minsize(width=666,height=66) 
                        # message box title
                        window.title("Performing data integrity check") 
                        # create a label for inside the message box
                        label = Tkinter.Label(window, text = "Performing data integrity check- please don't use the NextSeq")
                        # pack this label into box
                        label.pack()
                        # using threding run the function which calculates checksums in background
                        thread = threading.Thread(target = self.run_integrity_check)
                        thread.start() # start parallel computation
                        # montior this thread
                        while thread.is_alive():
                            # update the window
                            window.update()
                            time.sleep(5)
                        # see if the message box should show an error, or show info
                        if self.message_box_message == self.checksum_error:
                            # if an error display a error message box
                            tkMessageBox.showerror("Integrity Check Complete",self.message_box_message)
                        else:
                            # if ok display a info message box
                            tkMessageBox.showinfo("Integrity Check Complete",self.message_box_message)
                        

    def run_integrity_check(self):
       """
       This function uses self variables for the filepaths and calculates the checksums on directories
       The checksums are written to a file on the workstation for the demultiplexing script
       The checksums are also tested in this script to enable a warning message to be displayed to the scientists should the checksums not match
       """
       # calculate md5 checksums using dirhash package
       workstation_checksum = dirhash(self.workstation_runfolder, 'md5')
       sequencer_checksum = dirhash(self.sequencer_runfolder, 'md5')
       
       # write the checksums to the output file
       with open(os.path.join(self.workstation_runfolder, self.output_file), 'w') as outputfile:
           outputfile.write("workstation checksum (" + self.workstation_runfolder + ")=" + workstation_checksum+"\n")
           outputfile.write("sequencer checksum (" + self.sequencer_runfolder + ")=" + sequencer_checksum)
       
       # check the checksums match
       if workstation_checksum == sequencer_checksum:
          # if they do display complete message
          self.message_box_message = self.checksum_match
       else:
          # if they don't match display a message to speak to a bioinformatician
          self.message_box_message = self.checksum_error

def main():
    md5=Nextseq_Integrity_Check()
    md5.look_for_folder()
    
if __name__ =="__main__":
    main()