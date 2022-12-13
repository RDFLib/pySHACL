# -*- coding: utf-8 -*-
#
import os
import platform
import subprocess
import sys

from os import getenv, path
from sys import stderr


print(os.environ, file=stderr)
PATH = getenv("PATH", "")
PP = getenv('PYTHONPATH', "")
here_dir = path.abspath(path.dirname(__file__))
ENV_VARS = {"PATH": PATH, "PYTHONPATH": ':'.join((here_dir, PP))}
PH = getenv('PYTHONHOME', "")
if PH:
    ENV_VARS['PYTHONHOME'] = PH
VE = getenv('VIRTUAL_ENV', "")
if VE:
    ENV_VARS['VIRTUAL_ENV'] = VE
    virtual_bin = path.join(VE, "bin")
    ENV_VARS['PATH'] = ':'.join((virtual_bin, PATH))
abs_resources_dir = path.join(here_dir, 'resources')
cmdline_files_dir = path.join(abs_resources_dir, 'cmdline_tests')

check_resources = path.join(path.abspath(os.getcwd()), 'resources')
in_test_dir = False
if path.exists(check_resources) and path.isdir(check_resources):
    in_test_dir = True
else:
    in_test_dir = False

if in_test_dir:
    lib_dir = os.path.abspath(os.path.join(here_dir, os.pardir))
    ENV_VARS["PYTHONPATH"] = ':'.join((lib_dir, PP))

it = ENV_VARS["PYTHONPATH"].split(":")
print(it, file=stderr, flush=True)
scr_dir = "scripts-{}.{}".format(sys.version_info[0], sys.version_info[1])
if in_test_dir:
    scr_dir = path.join('..', scr_dir)
check_scrdir = path.join(path.abspath(os.getcwd()), scr_dir)
if path.exists(check_scrdir) and path.isdir(check_scrdir):
    has_scripts_dir = True
else:
    has_scripts_dir = False

bin_dir = "bin"
if in_test_dir:
    bin_dir = path.join('..', bin_dir)
check_bindir = path.join(path.abspath(os.getcwd()), bin_dir)
if path.exists(check_bindir) and path.isdir(check_bindir):
    has_bin_dir = True
else:
    has_bin_dir = False

cli_script = "pyshacl/cli.py"
if in_test_dir:
    cli_script = path.join('..', cli_script)
check_cli_script = path.join(path.abspath(os.getcwd()), cli_script)
if path.exists(check_cli_script) and path.isfile(check_cli_script):
    has_cli_script = True
else:
    has_cli_script = False

if has_scripts_dir:
    pyshacl_command = ["{}/pyshacl".format(scr_dir)]
elif has_bin_dir:
    pyshacl_command = ["{}/pyshacl".format(bin_dir)]
elif has_cli_script:
    pyshacl_command = ["python3", cli_script]
else:
    pyshacl_command = ["pyshacl"]


def test_cmdline():
    if not hasattr(subprocess, 'run'):
        print("Subprocess.run() not available, skip this test")
        assert True
        return True
    if platform.system() == "Windows":
        print("Commandline tests cannot run on Windows.")
        assert True
        return True
    if os.environ.get("PYBUILD_NAME", None) is not None:
        print("We don't have access to scripts dir during pybuild process.")
        assert True
        return True
    graph_file = path.join(cmdline_files_dir, 'd1.ttl')
    shacl_file = path.join(cmdline_files_dir, 's1.ttl')
    ont_file = path.join(cmdline_files_dir, 'o1.ttl')
    cmd = pyshacl_command
    args = [graph_file, '-s', shacl_file, '-i', 'rdfs', '-e', ont_file]
    res = subprocess.run(cmd + args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=ENV_VARS)
    print("result = {}".format(res.returncode))
    print(res.stdout.decode('utf-8'))
    print(res.stderr.decode('utf-8'))
    assert res.returncode == 0


def test_cmdline_fail():
    if not hasattr(subprocess, 'run'):
        print("Subprocess.run() not available, skip this test")
        assert True
        return True
    if platform.system() == "Windows":
        print("Commandline tests cannot run on Windows.")
        assert True
        return True
    if os.environ.get("PYBUILD_NAME", None) is not None:
        print("We don't have access to scripts dir during pybuild process.")
        assert True
        return True
    graph_file = path.join(cmdline_files_dir, 'd2.ttl')
    shacl_file = path.join(cmdline_files_dir, 's1.ttl')
    ont_file = path.join(cmdline_files_dir, 'o1.ttl')
    cmd = pyshacl_command
    args = [graph_file, '-s', shacl_file, '-i', 'rdfs', '-e', ont_file]
    res = subprocess.run(cmd + args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=ENV_VARS)
    print("result = {}".format(res.returncode))
    print(res.stdout.decode('utf-8'))
    print(res.stderr.decode('utf-8'))
    assert res.returncode == 1


def test_cmdline_table():
    graph_file = path.join(cmdline_files_dir, 'd1.ttl')
    shacl_file = path.join(cmdline_files_dir, 's1.ttl')
    args = [graph_file, '-s', shacl_file, '-f', 'table']
    res = subprocess.run(pyshacl_command + args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=ENV_VARS)
    output_table = res.stdout.decode('utf-8')
    assert "+-----+-----------+---------------------------+---------------------------+" \
           "---------------------------+--------------------------+---------------------------+" \
           "---------------------------+" in output_table
    assert "| 1   | Violation | http://example.com/ex#Hum | http://example.com/exOnt# " in output_table


def test_cmdline_web():
    if not hasattr(subprocess, 'run'):
        print("Subprocess.run() not available, skip this test")
        assert True
        return
    if platform.system() == "Windows":
        print("Commandline tests cannot run on Windows.")
        assert True
        return
    if os.environ.get("PYBUILD_NAME", None) is not None:
        print("We don't have access to scripts dir during pybuild process.")
        assert True
        return
    DEB_BUILD_ARCH = os.environ.get('DEB_BUILD_ARCH', None)
    DEB_HOST_ARCH = os.environ.get('DEB_HOST_ARCH', None)
    if DEB_BUILD_ARCH is not None or DEB_HOST_ARCH is not None:
        print("Cannot run web requests in debhelper tests.")
        assert True
        return
    graph_file = path.join(cmdline_files_dir, 'd1.ttl')
    shacl_file = "https://raw.githubusercontent.com/RDFLib/pySHACL/master/test/resources/cmdline_tests/s1.ttl"
    ont_file = "https://raw.githubusercontent.com/RDFLib/pySHACL/master/test/resources/cmdline_tests/o1.ttl"
    cmd = pyshacl_command
    args = [graph_file, '-s', shacl_file, '-i', 'rdfs', '-e', ont_file]
    res = subprocess.run(cmd + args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=ENV_VARS)
    print("result = {}".format(res.returncode))
    print(res.stdout.decode('utf-8'))
    print(res.stderr.decode('utf-8'))
    assert res.returncode == 0


def test_cmdline_jsonld():
    if not hasattr(subprocess, 'run'):
        print("Subprocess.run() not available, skip this test")
        assert True
        return
    if platform.system() == "Windows":
        print("Commandline tests cannot run on Windows.")
        assert True
        return
    if os.environ.get("PYBUILD_NAME", None) is not None:
        print("We don't have access to scripts dir during pybuild process.")
        assert True
        return
    DEB_BUILD_ARCH = os.environ.get('DEB_BUILD_ARCH', None)
    DEB_HOST_ARCH = os.environ.get('DEB_HOST_ARCH', None)
    if DEB_BUILD_ARCH is not None or DEB_HOST_ARCH is not None:
        print("Cannot run web requests in debhelper tests.")
        assert True
        return
    graph_file = path.join(cmdline_files_dir, 'd1.jsonld')
    shacl_file = "https://raw.githubusercontent.com/RDFLib/pySHACL/master/test/resources/cmdline_tests/s1.ttl"
    ont_file = "https://raw.githubusercontent.com/RDFLib/pySHACL/master/test/resources/cmdline_tests/o1.ttl"
    cmd = pyshacl_command
    args = [graph_file, '-df', 'json-ld', '-s', shacl_file, '-i', 'rdfs', '-e', ont_file]
    res = subprocess.run(cmd + args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=ENV_VARS)
    print("result = {}".format(res.returncode))
    print(res.stdout.decode('utf-8'))
    print(res.stderr.decode('utf-8'))
    assert res.returncode == 0


if __name__ == "__main__":
    test_cmdline()
    test_cmdline_fail()
    test_cmdline_table()
    test_cmdline_web()
    test_cmdline_jsonld()
