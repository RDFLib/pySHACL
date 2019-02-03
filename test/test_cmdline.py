# -*- coding: utf-8 -*-
#
import sys
import os
from os import path
import subprocess

here_dir = path.abspath(path.dirname(__file__))
abs_resources_dir = path.join(here_dir, 'resources')
cmdline_files_dir = path.join(abs_resources_dir, 'cmdline_tests')

check_resources = path.join(path.abspath(os.getcwd()), 'resources')
in_test_dir = False
if path.exists(check_resources) and path.isdir(check_resources):
    in_test_dir = True
else:
    in_test_dir = False

scr_dir = "scripts-{}.{}".format(sys.version_info[0], sys.version_info[1])
if in_test_dir:
    scr_dir = path.join('..', scr_dir)
check_scrdir = path.join(path.abspath(os.getcwd()), scr_dir)
has_scripts_dir = False
if path.exists(check_scrdir) and path.isdir(check_scrdir):
    has_scripts_dir = True
else:
    has_scripts_dir = False

if has_scripts_dir:
    pyshacl_command = "{}/pyshacl".format(scr_dir)
else:
    if in_test_dir:
        pyshacl_command = "../bin/pyshacl"
    else:
        pyshacl_command = "bin/pyshacl"

def test_cmdline():
    if not hasattr(subprocess, 'run'):
        print("Subprocess.run() not available, skip this test")
        assert True
        return True
    graph_file = path.join(cmdline_files_dir, 'd1.ttl')
    shacl_file = path.join(cmdline_files_dir, 's1.ttl')
    ont_file = path.join(cmdline_files_dir, 'o1.ttl')
    cmd = [pyshacl_command]
    args = [
        graph_file,
        '-s', shacl_file,
        '-i', 'rdfs',
        '-e', ont_file
    ]
    res = subprocess.run(cmd+args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    print("result = {}".format(res.returncode))
    print(res.stdout.decode('utf-8'))
    print(res.stderr.decode('utf-8'))
    assert res.returncode == 0
    return True

def test_cmdline_web():
    if not hasattr(subprocess, 'run'):
        print("Subprocess.run() not available, skip this test")
        assert True
        return
    DEB_BUILD_ARCH = os.environ.get('DEB_BUILD_ARCH', None)
    DEB_HOST_ARCH = os.environ.get('DEB_HOST_ARCH', None)
    if DEB_BUILD_ARCH is not None or DEB_HOST_ARCH is not None:
        print("Cannot run web requests in debhelper tests.")
        assert True
        return True
    graph_file = path.join(cmdline_files_dir, 'd1.ttl')
    shacl_file = "https://raw.githubusercontent.com/RDFLib/pySHACL/master/test/resources/cmdline_tests/s1.ttl"
    ont_file = "https://raw.githubusercontent.com/RDFLib/pySHACL/master/test/resources/cmdline_tests/o1.ttl"
    cmd = [pyshacl_command]
    args = [
        graph_file,
        '-s', shacl_file,
        '-i', 'rdfs',
        '-e', ont_file
    ]
    res = subprocess.run(cmd+args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    print("result = {}".format(res.returncode))
    print(res.stdout.decode('utf-8'))
    print(res.stderr.decode('utf-8'))
    assert res.returncode == 0
    return True

if __name__ == "__main__":
    test_cmdline()
    test_cmdline_web()