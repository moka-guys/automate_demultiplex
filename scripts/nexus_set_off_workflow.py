'''
Created on 20 Feb 2017

STEPS
1. source /etc/profile.d/dnanexus.environment.sh
2. dx ls NGS144/Data/Intensities/BaseCalls/ > /home/mokaguys/Documents/development_area/list_of_fastqs.txt
3. set config settings in __init__
4. run bash script bash /home/mokaguys/Documents/development_area/setoff_workflow.sh
 
@author: aled
'''

import os

class set_off_workflow():
    ''' This class is fed a runfolder which may be ready to be uploaded to DNA Nexus''' 
    
    def __init__(self):
        #########################################CONFIG##############################################
        #what project do you want to run these jobs in
        self.project="003_170220_upload:"

        ### where in this project do you want the output?
        self.folder_in_project="NGS144"

        ### where (within the project folder) can the input files be found?
        self.input_location = self.folder_in_project+"/Data/Intensities/BaseCalls/"

        ### which project is the workflow that you want to run in?
        self.app_project="001_ToolsReferenceData:"
        ### what workflow?
        self.workflow="GATK3.5_v2.3_CM"
        ##############################################################################################

        # location of list of files
        self.list_of_fastqs_in_nexus="/home/mokaguys/Documents/development_area/list_of_fastqs.txt"
        # location of bash script which will set off workflow
        self.bashscript="/home/mokaguys/Documents/development_area/setoff_workflow.sh"


        # variables for running pipeline
        self.bash_script=""
        self.source_command = "#!/bin/bash\n. /etc/profile.d/dnanexus.environment.sh\n"
        self.base_command = "dx run "+self.app_project+"Workflows/"+self.workflow+" -y"
        self.fastq_R1 = " -istage-Byz9BJ80jy1k2VB9xVXBp0Fg.reads_fastqgz=" 
        self.fastq_R2 = " -istage-Byz9BJ80jy1k2VB9xVXBp0Fg.reads2_fastqgz="
        self.destination = " --dest="+self.project
        self.arg6 = " --brief --auth-token K2v2COMKM7NdjeHyWdINUSrCrHaJfnxZ"
        
       

    def  create_run_pipeline_command(self):
        '''loop through the list of fastqs to create a set of commands to initiate the pipeline and write to file'''
               
        #open bash script
        DNA_Nexus_bash_script = open(self.bashscript, 'w')
        #write source command
        DNA_Nexus_bash_script.write(self.source_command)

        # open list of input files
        list_of_fq=open(self.list_of_fastqs_in_nexus,'r')

        #loop through list of fastq files
        for fastq in list_of_fq:
            #take read one
            if "_R1_" in fastq:
                #assign read1
                read1 = self.input_location+fastq.rstrip()
                # assign read2 by replacing R1 with R2
                read2 = self.input_location+fastq.replace("_R1_", "_R2_").rstrip()
                # create the dx command
                command = self.base_command + self.fastq_R1 + self.project+ read1 + self.fastq_R2 + self.project + read2 + self.destination +self.folder_in_project+ self.arg6
                # write the command to file
                DNA_Nexus_bash_script.write(command+"\n")
        #close
        DNA_Nexus_bash_script.close()


if __name__ == '__main__':
   
    #create instance
    a = set_off_workflow()
    a.create_run_pipeline_command()    
