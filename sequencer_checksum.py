from checksumdir import dirhash # package to calculate checksums
import os # package to use and manipulate file paths
import datetime # for timestamp
import time # for sleep
import Tkinter # to open a window/message box
import tkMessageBox
import threading # to run a function in the background

class Nextseq_Integrity_Check():
	def __init__(self):
		
		# temp folder on the nextseq
		self.nextseqtemp_folder = "D://Illumina//NextSeq Control Software Temp"
			
		# path to the mapped workstation share
		self.mapped_workstation_folder = "Z://"
		
		# the filename which denote sequencing has finished
		self.RTA_complete = "RTAComplete.txt"
		
		# the file to write the checksums to
		self.output_file = "md5checksum.txt"
		
		# folder containing files which denote checksum is being calculated
		self.checksum_in_progress = "C://Users//sbsuser//integrity_check//checksums_inprogress"

		# folder containing files which denote checksum is being calculated
		self.run_in_progress = "C://Users//sbsuser//integrity_check//run_inprogress"
		
		# variable to hold the name of the runfolder
		self.runfolder = ""

		# variables for the runfolder paths
		self.workstation_runfolder = ""
		self.sequencer_runfolder = ""

		# files to ignore from checksum
		self.exclude = ["RTAStart.bat", "CorrectedIntMetrics.bin", "EmpiricalPhasingMetrics.bin", "ErrorMetrics.bin", "EventMetrics.bin", "ExtractionMetrics.bin", "PFGridMetrics.bin", "QMetrics.bin", "RegistrationMetrics.bin", "TileMetrics.bin", "000_000_000_na_rtabat.trans", "FilesAdded.csv", "FilesCopied.csv", "md5checksum.txt"]
		# flag to set testing		
		self.testing = False

		# if testing overwrite the paths to that of the testing 
		if self.testing:
			# drive letter given to usb stick
			self.mapped_drive = "E://"
			# path to the fake nextseqtemp folder
			self.nextseqtemp_folder = self.mapped_drive + "integrity_testing//sequencer_temp"
			# path to the fake workstation folder
			self.mapped_workstation_folder = self.mapped_drive + "integrity_testing//workstation"
			# path to the fake checksums_inprogress folder
			self.checksum_in_progress = self.mapped_drive + "integrity_testing//checksums_inprogress"	
			# path to the fake run in progress folder
			self.run_in_progress = self.mapped_drive + "integrity_testing//run_inprogress"

	def look_for_folder(self):
		"""
		This script runs every hour.
		The script needs to detect when a run has started, and display a window which remains until the integrity test has been performed.
		Display a window to say not to do anything until sequencing is complete and integrity checks done.
		When checksums are done, display a message box displaying pass/fail messages.
		"""

		# for each runfolder in temp folder
		for temp_runfolder in os.listdir(self.nextseqtemp_folder):
			# look to see if the run has already been caught by this script at a previous time
			if temp_runfolder in os.listdir(self.run_in_progress):
				# skip this temp_runfolder
				if self.testing:
					print "run already being monitored. stopping"
				else:
					pass

			# if this is the start of a run:
			else:
				# assign run folder name
				self.runfolder = temp_runfolder
				# create a file to denote this run is being monitored
				with open(os.path.join(self.run_in_progress,temp_runfolder),'w') as new_run_marker:
					# write timestamp to file
					new_run_marker.write(str(datetime.datetime.now()))
				
				# call function which opens a window to say run in progress - don't do anything until a message box appears denoting integrity check has been performed
				# this function will close when the run ends and the checksum has been calculated
				self.open_window()

				# call function to assess result of checksum and display message box
				# if checksums match (integrity test pass) return a info box
				if self.check_checksums():
					# create root window which can then be hidden
					root = Tkinter.Tk()
					# hide 
					root.withdraw()
					tkMessageBox.showinfo("Integrity check complete","Integrity check passed")
					# if checksums don't match (integrity test FAIL) return a error box
				else:
					# create root window which can then be hidden
					root = Tkinter.Tk()
					# hide 
					root.withdraw()
					tkMessageBox.showerror("Integrity check complete","Integrity check failed - please do not use this sequencer and inform the Bioinformatics team immediately")


	def open_window(self):
		"""
		This function uses TKinter to create a window which remains until a process has finished.
		This process is complete when the run has finished and checksums have been calculated.
		The window closes and is replaced by the info or error in look_for_folder boxes.
		"""
		# create a object for pop up box
		window = Tkinter.Tk()
		# set some properties of the message box
		# message box size
		window.minsize(width=666,height=66) 
		# message box title
		window.title("Please wait") 
		# create a label for inside the message box
		label = Tkinter.Label(window, text = "Please don't use this sequencer or close this window until a message box stating \"Integrity check passed\" is displayed")
		# display the label in the window
		label.pack()
		# using threading run the function run_has_finished which closes when the checksums have been generated
		thread = threading.Thread(target = self.run_has_finished)
		# start parallel computation
		thread.start() 
		# montior this thread
		while thread.is_alive():
			# update the window
			window.update()
			time.sleep(5)
		#close this window then all checksums are present.
		window.destroy()


	def run_has_finished(self):
		"""
		This function looks at the runfolder, assesses if the run has finished and the data transferred.
		If required the checksums are generated, or if not the script waits until the checksums have been generated (by the demultiplexing script).
		"""
		# build path to the runfolder
		self.sequencer_runfolder = os.path.join(self.nextseqtemp_folder, self.runfolder)
		# build paths on the workstation
		self.workstation_runfolder = os.path.join(self.mapped_workstation_folder, self.runfolder)
		#flag to denote run and data transfer has finished
		finished = False
		# while variable finished is false
		while not finished:
			# check the run has finished and transferred (presence of RTA_complete in the runfolder and on workstation)
			if self.RTA_complete in os.listdir(self.sequencer_runfolder) and self.RTA_complete in os.listdir(self.workstation_runfolder):
					# if it's a testing run print a message
					if self.testing:
						print "run finished - skipping 2 hour wait"
					else:
						# sleep 2 hours to ensure all file transfers are done
						time.sleep(7200)
					
					# call function which triggers the checksum calculations
					self.prepare_checksum_calculations()
					# now all checksums are done change flag to true so the loop finishes and the window is closed
					finished = True
			
			# if run has not finished 
			else:
				# if a testing run, wait 20 seconds and print a message
				if self.testing:
					print "waiting 20 seconds for sequencing and data transfer to finish"
					time.sleep(20)
				# if not testing wait longer
				else:
					# wait 10 minutes
					time.sleep(600)
		if self.testing:
			print "checksums done"
			

	def prepare_checksum_calculations(self):
		"""
		The checksums are calculated by this script.
		This function checks the runfolder has not already been checksummed, marks the folder as being checksummed and then calls the function to generate the checksums.
		"""
		if self.testing:
			print "in prepare_checksum_calculations"
		# create name for file to denote checksum in progress
		checksum_in_progress_file=self.runfolder+".txt"
		# check integrity check has not already been calculated, or isn't currently being calculated
		if self.output_file not in os.listdir(self.workstation_runfolder) and checksum_in_progress_file not in os.listdir(self.checksum_in_progress):
			# create a file to denote checksum in progress
			with open(os.path.join(self.checksum_in_progress,checksum_in_progress_file),'w') as checksum_in_progress_file_path:
				# create a timestamp
				now=datetime.datetime.now()
				# convert timestamp to string and write to file.
				checksum_in_progress_file_path.write(str(now))

			# call function to generate checksum for workstation and sequencer runfolders
			self.run_integrity_check()
		# if a testing run print statement to explain stopping
		elif self.testing:
			print "checksums already generated or in process of being generated. stopping"
						

	def run_integrity_check(self):
		"""
		This function uses self variables for the filepaths and calculates the checksums on directories.
		It looks for the presense of any files which should be ignored as they are not copied from temp to output.
		The checksums are written to a file on the workstation for the demultiplexing script.
		"""
		if self.testing:
			print "starting integrity checking"

		# calculate the checksum, using the to_exclude list
		workstation_checksum = dirhash(self.workstation_runfolder, 'md5',excluded_files=self.exclude)
		sequencer_checksum = dirhash(self.sequencer_runfolder, 'md5',excluded_files=self.exclude)
		
		if self.testing:
			print "workstation checksum = " + workstation_checksum
			print "sequencer checksum = " + sequencer_checksum	   

		# write the checksums to the output file (on workstation)
		with open(os.path.join(self.workstation_runfolder, self.output_file), 'w') as outputfile:
			outputfile.write("workstation checksum (" + self.workstation_runfolder + ")=" + workstation_checksum + "\n")
			outputfile.write("sequencer checksum (" + self.sequencer_runfolder + ")=" + sequencer_checksum + "\n")


	def checksums_done(self):
		"""
		This function is used to detect if the checksum file is present in the workstation runfolder - used for miseq runs which are calculated by the demultiplexing script.
		Returns False until checksum file is detected.
		"""
		# assess if the checksum file is present in the workstation runfolder
		while self.output_file not in os.listdir(self.workstation_runfolder):
			#return false
			return False
		# retrun true when detected
		return True
		

	def check_checksums(self):
		"""
		This function receives the path to a file which should contain the checksums for both copies of a run folder.
		Each line contains the checksum and some information about the folder which that checksum relates to
		The checksums are extracted from the lines and compared
		If they match the function returns true else it returns false.
		All error reporting is done outside this function
		"""
		if self.testing:
			print "checking the checksums match"
		# open the file containing the md5 checksums
		with open(os.path.join(self.workstation_runfolder, self.output_file), 'r') as checksum_file:
			# read the checksums into a list
			checksums = checksum_file.readlines()
		# each line contains the location of each checksum with an equals sign and then the checksum.
		# split on equals to capture just the checksum (and remove any new line characters incase they result in a differenece)
		self.workstation_checksum = checksums[0].split("=")[1].rstrip()
		self.sequencer_checksum = checksums[1].split("=")[1].rstrip()
		# if the checksums match
		if self.workstation_checksum == self.sequencer_checksum:
			# if md5checksums match return to say test passed
			if self.testing:
				print "checksums match"
			return True
		else:
			#otherwise return false
			if self.testing:
				print "checksums don't match"
			return False


def main():
	md5=Nextseq_Integrity_Check()
	md5.look_for_folder()
	
if __name__ =="__main__":
	main()