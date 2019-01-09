# -*- coding: utf-8 -*-
#
from os import path
import subprocess

here_dir = path.abspath(path.dirname(__file__))
cmdline_files_dir = path.join(here_dir, 'resources', 'cmdline_tests')

def test_cmdline():
    graph_file = path.join(cmdline_files_dir, 'd1.ttl')
    shacl_file = path.join(cmdline_files_dir, 's1.ttl')
    ont_file = path.join(cmdline_files_dir, 'o1.ttl')

    args = [
        '../bin/pyshacl',
        graph_file,
        '-s', shacl_file,
        '-i', 'rdfs',
        '-e', ont_file
    ]
    res = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    print("result = {}".format(res.returncode))
    print(res.stdout.decode('utf-8'))
    print(res.stderr.decode('utf-8'))
    assert res.returncode == 0

def test_cmdline_web():
    graph_file = path.join(cmdline_files_dir, 'd1.ttl')
    shacl_file = "https://raw.githubusercontent.com/RDFLib/pySHACL/master/test/resources/cmdline_tests/s1.ttl"
    ont_file = "https://raw.githubusercontent.com/RDFLib/pySHACL/master/test/resources/cmdline_tests/o1.ttl"

    args = [
        '../bin/pyshacl',
        graph_file,
        '-s', shacl_file,
        '-i', 'rdfs',
        '-e', ont_file
    ]
    res = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    print("result = {}".format(res.returncode))
    print(res.stdout.decode('utf-8'))
    print(res.stderr.decode('utf-8'))
    assert res.returncode == 0



if __name__ == "__main__":
    test_cmdline()
    test_cmdline_web()