import shlex
import subprocess


def exec_cmd(cmd):
    """
    Splits the cmd arguments and returns a Popen() object

    :param str cmd: the raw command as text

    :returns: the initialized process to run the command
    :rtype: subprocess.Popen
    """
    args = shlex.split(cmd)
    return subprocess.Popen(args, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
