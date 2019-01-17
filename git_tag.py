import subprocess
import os


def git_tag():
    '''rather than hard code the script release, read it directly from the repository'''
    #  set the command which prints the git tags for the folder containing the script that is being executed. The tag looks like "v22-3-gccfd" so needs to be parsed. use awk to create an array "a", splitting on "-". The print the first element of the array
    cmd = "git -C " + os.path.dirname(os.path.realpath(__file__)) + " describe --tags | awk '{split($0,a,\"-\"); print a[1]}'"
    #  use subprocess to execute command
    proc = subprocess.Popen([cmd], stderr=subprocess.PIPE, stdout=subprocess.PIPE, shell=True)
    out, err = proc.communicate()
    #  return standard out, removing any new line characters
    return out.rstrip()

if __name__ == "__main__":
    git_tag()