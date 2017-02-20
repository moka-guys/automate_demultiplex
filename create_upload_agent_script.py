'''
This script takes a flow cell and a project and uploads all fastqs which match the criteria to said project.
1. complete the config section in __init__
2. run this script.
3. then run bash /home/mokaguys/Documents/development_area/<flowcell>.sh"

'''
import os
class upload():
	def __init__(self):
		################################CONFIG################################
		# which run do you want to upload
		self.flowcell="170116_NB551068_0027_AHFJMLBGX2"
		
		# which project do you want to upload to?
		self.nexusproject="003_170220_upload"
		
		#which string must the fastq file name ?
		self.fastq_filter="_CM_S" # if want all use "fastq"
		#self.fastq_filter="fastq" # if want all use "fastq"
		
		# where do you want to put the uploaded files?
		self.nexusdestination="/Data/Intensities/BaseCalls/"
		
		# where do you want to save the bash script containing the upload commands?
		self.upload_script_path="/home/mokaguys/Documents/development_area/"
		#######################################################################
		
		# variables used for upload
		self.source_command = "#!/bin/bash\nsource /etc/profile.d/dnanexus.environment.sh\n"
		self.upload_agent_path = "/home/mokaguys/Documents/apps/dnanexus-upload-agent-1.5.17-linux/ua"
		self.auth = " -a XyMlsVImvuBoClLXnZo8QnIKy5sX4tyh"
		self.nexusprojectstring = "  --project  "
		self.dest = " --folder /"
		self.fastqfilepath="/Data/Intensities/BaseCalls/"
		self.compress =" --do-not-compress --upload-threads 10 "
		
		# path to the runfolders
		self.runfolders = "/media/data1/share/"
		
		# empty list to hold fastqs
		self.fastq_list=[]
		
	def get_list_of_fastqs(self):
		### loop through the run folder to get a list of fastq files
		for file in os.listdir(self.runfolders+self.flowcell+self.fastqfilepath):
			if file.endswith("fastq.gz"):
				if file.startswith("Undetermined"):
					# skip undertermined fastq
					pass
				# only upload fastqs which match this pattern
				if self.fastq_filter in file:
					self.fastq_list.append(file)

	def create_command(self):
		# capture the NGS run number (first element of the file name)
		run=""
		for fastq in self.fastq_list:
			if run == "":
				run=fastq.split("_")[0]
		if run == "":
			raise ValueError("run number cannot be found")

		# set the string which states where to upload files to
		self.dest=self.dest+run+self.nexusdestination
		# build string setting the project to upload to
		self.nexusprojectstring=self.nexusprojectstring+self.nexusproject
		#open a file to write to
		bashscript=open(self.upload_script_path+self.flowcell+".sh",'w')
		#write source command
		bashscript.write(self.source_command)
		# loop through fastqs
		for fastq in self.fastq_list:
			#write upload command
			# eg /home/mokaguys/Documents/apps/dnanexus-upload-agent-1.5.17-linux/ua -a 79KDFRITp9OY7ltyE0YuOJq6IH2i5YRp -p 003_161207_CustomPanelProject --progress --do-not-compress /media/data1/share/161014_NB551068_0010_AHM3CGBGXY/Data/Intensities/BaseCalls/NGS136_25_164793_SS_CM_S25_R1_001.fastq.gz
			bashscript.write(self.upload_agent_path+self.auth+self.nexusproject+self.dest+self.compress+self.runfolders+self.flowcell+self.fastqfilepath+fastq+"\n")
		bashscript.close()


if __name__=="__main__":
	u=upload()
	u.get_list_of_fastqs()
	u.create_command()
		