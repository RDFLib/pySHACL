# -*- coding: utf-8 -*-
#
import os
from os import path
import subprocess

here_dir = path.abspath(path.dirname(__file__))
abs_resources_dir = path.join(here_dir, 'resources')

check_resources = path.join(path.abspath(os.getcwd()), 'resources')
in_test_dir = False
if path.exists(check_resources) and path.isdir(check_resources):
    in_test_dir = True
else:
    in_test_dir = False
cmdline_files_dir = path.join(abs_resources_dir, 'cmdline_tests')

def test_cmdline():
    if not hasattr(subprocess, 'run'):
        print("Subprocess.run() not available, skip this test")
        assert True
        return True
    graph_file = path.join(cmdline_files_dir, 'd1.ttl')
    shacl_file = path.join(cmdline_files_dir, 's1.ttl')
    ont_file = path.join(cmdline_files_dir, 'o1.ttl')
    if in_test_dir:
        cmd = ['../bin/pyshacl']
    else:
        cmd = ['bin/pyshacl']
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
    graph_file = path.join(cmdline_files_dir, 'd1.ttl')
    shacl_file = "https://raw.githubusercontent.com/RDFLib/pySHACL/master/test/resources/cmdline_tests/s1.ttl"
    ont_file = "https://raw.githubusercontent.com/RDFLib/pySHACL/master/test/resources/cmdline_tests/o1.ttl"
    if in_test_dir:
        cmd = ['../bin/pyshacl']
    else:
        cmd = ['bin/pyshacl']
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