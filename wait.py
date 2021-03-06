################################################################################
# wait.py
#
# Copyright (C) 2016 Justin Paul <justinpaulthekkan@gmail.com>
#
# @author: Justin Paul
#
# This program is free software: you can redistribute it and/or modify
# it as long as you retain the name of the original author and under
# the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
################################################################################
import os
import sys
import time
import getopt
import shutil
import socket
import subprocess

def wait_for_database(options, arguments):
    base_dir = os.path.dirname(sys.argv[0])
    if base_dir in [".", ""]: base_dir = os.getcwd()

    if os.path.isfile(os.path.join(base_dir, "metadata.json")):
        mfile = open(os.path.join(base_dir, "metadata.json"), "r")
        metadata = eval(mfile.read())
        mfile.close()
    else:
        print "Mandatory file %s cannot be located in %s." %("metadata.json", base_dir)
        sys.exit(1)

    timeout = int(options.get("--timeout", 3600))
    delay = int(options.get("--delay", 240))
    wait_time = int(options.get("--wait", 60))

    fmw_home = options.get("-f")
    db_conn = options.get("-c", metadata.get("database").get("connect-string"))
    dba_user = options.get("--dba_user", "SYS")
    dba_pass = options.get("--dba_password", metadata.get("database").get("sys-password"))
    db_prfix = db_prfix = options.get("-m", "TEST")
    pwd_file = options.get("-w", "")
    if os.path.isfile(pwd_file):
        with open(pwd_file, "r") as bfile:
            fcontents = bfile.read().splitlines()
        dba_pass = fcontents[0]

    command = [os.path.join(fmw_home, "oracle_common", "bin", "rcu"),
               '-silent', '-listSchemas', '-connectString', db_conn,
               '-dbUser', dba_user, '-dbRole', 'sysdba', '-schemaPrefixes', db_prfix]
    
    now=time.time()
    later = time.time()
    while int(later - now) < timeout:
        process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        (out, err) = process.communicate(input=dba_pass)
        logdir = os.path.dirname(os.path.dirname(out.splitlines()[1].split()[2]))
        if os.path.isdir(logdir): shutil.rmtree(logdir, True)
        if "ERROR - RCU-" in out:
            later = time.time()
            time.sleep(delay)
        else:
            break

    time.sleep(wait_time)

def wait_for_socket(options, arguments):
    base_dir = os.path.dirname(sys.argv[0])
    if base_dir in [".", ""]: base_dir = os.getcwd()

    if os.path.isfile(os.path.join(base_dir, "metadata.json")):
        mfile = open(os.path.join(base_dir, "metadata.json"), "r")
        metadata = eval(mfile.read())
        mfile.close()
    else:
        print "Mandatory file %s cannot be located in %s." %("metadata.json", base_dir)
        sys.exit(1)

    host = options.get("-h")
    port = int(options.get("-p", metadata.get("wls").get("as-port")))
    timeout = int(options.get("--timeout", 3600))
    delay = int(options.get("--delay", 60))
    socket_timeout = int(options.get("--socket_timeout", 5))
    wait_time = int(options.get("--wait", 0))
    
    now=time.time()
    later = time.time()
    while int(later - now) < timeout:
        try:
            conn=socket.socket()
            conn.settimeout(socket_timeout)
            conn.connect((host, port))
            conn.close()
            break
        except socket.error:
            later = time.time()
            time.sleep(delay)
        except:
            print "ERROR: An unexpected error has occurred."
            sys.exit(2)
    time.sleep(wait_time)

if __name__ == "__main__":
    options, arguments = getopt.getopt(sys.argv[1:], "?f:h:p:c:w:",
                                       ["timeout=", "delay=", "wait=",
                                        "socket_timeout=", "dba_user=",
                                        "dba_password="])
    options = dict(options)

    if "-?" in options:
        print "Usage: python %s %s %s %s %s" %("wait.py",
        "[-?] -h host -p port -c db_connect_string [-w password_file]",
        "[--wait wait_secs] [--timeout timeout_in_secs] [--delay delay_in_secs]",
        "[--socket_timeout socket_timeout_in_secs] [--dba_user dba_user]",
        "[--dba_password dba_password]")
        sys.exit(0)

    if "-c" in options:
        wait_for_database(options, arguments)

    if "-h" in options:
        wait_for_socket(options, arguments)
