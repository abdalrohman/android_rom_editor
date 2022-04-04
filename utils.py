#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# functions needed by project

import os
import shutil
import subprocess
import sys
import time
import zipfile

from loguru import logger

from config import load_config


def init_log(log_file=None):
  if log_file is not None:
    config = {
      "handlers": [
        {"sink": log_file,
         "format": "[{time:HH:mm:ss}] [{function}|{name}|{file}|{line}] took {elapsed} :: {message} ", 'backtrace': 'True', 'diagnose': 'True', 'enqueue': 'True', 'rotation': "12:00"
         },
        {"sink": sys.stdout,
         "format": "<g>[{time:HH:mm:ss}]</g> <level>{message}</level>", 'level': 'INFO'}
      ]
    }
    logger.configure(**config)
  else:
    config = {
      "handlers": [
        {"sink": sys.stdout,
         "format": "<g>[{time:HH:mm:ss}]</g> <level>{message}</level>", 'level': 'INFO'}
      ]
    }
    logger.configure(**config)


init_log('Log.txt')


def RunCommand(arg, verbose=False, **kwargs):
  """Runs the given command and returns the output.

  Args:
    arg: The command represented as a list of strings.
    verbose: Whether the commands should be shown. Default to the global
        verbosity if unspecified.
    kwargs: Any additional args to be passed to subprocess.Popen(), such as env,
        stdin, etc. stdout and stderr will default to subprocess.PIPE and
        subprocess.STDOUT respectively unless caller specifies any of them.

  Returns:
    The output string.

  Raises:
    RuntimeError: On non-zero exit from the command.
  """
  start_time = time.time()
  if verbose:
    logger.info("Running: {}", " ".join(arg))

  if 'stdout' not in kwargs and 'stderr' not in kwargs:
    kwargs['stdout'] = subprocess.PIPE
    kwargs['stderr'] = subprocess.STDOUT
  if 'universal_newlines' not in kwargs:
    kwargs['universal_newlines'] = True

  proc = subprocess.Popen(arg, **kwargs)
  output, _ = proc.communicate()

  runtime = (time.time() - start_time)
  if verbose:
    logger.info("Excution time: {} seconds", runtime)

  if output is None:
    output = ""

  if proc.returncode != 0:
    logger.exception(
      "Failed to run command '{}' (exit code {}):\n{}", " ".join(
        arg), proc.returncode, output
    )
    exit(1)

  return output, proc.returncode


def mkdir(dir_name):
  """like mkdir -p in gnu linux.
  ex: mkdir('test/1/2/3')
  :param dir_name: directories name
  """
  if not os.path.exists(dir_name):
    logger.info("Create [{}]", dir_name)
    os.makedirs(dir_name)
    return 0


def rmdir(dir_name):
  if os.path.exists(dir_name):
    logger.info("Remove [{}]", dir_name)
    shutil.rmtree(dir_name, ignore_errors=True)


def remove(file_name):
  if os.path.exists(file_name):
    logger.info("Remove [{}]", file_name)
    os.remove(file_name)


def is_wsl():
  """
  Detect if inside WSL
  Returns:
      bool: return True if shell in wsl
  """
  ret = subprocess.run(
    ['grep -qEi "(Microsoft|WSL)" /proc/version'], shell=True).returncode
  if ret == 0:
    return True
  else:
    return False


def check_wsl_ver():
  """
  check wsl version
  Returns:
      int: version number
  """
  wsl_exe = load_config('WSL', 'wsl_exe')
  cmd = [f"{wsl_exe} -l -v | iconv -f utf16 | grep -E" +
         r' "\b${WSL_DISTRO_NAME}\s+Running" ' + r"| tr -d '\r' | sed 's/.*\([[:digit:]]\)[[:space:]]*/\1/'"]
  version = RunCommand(cmd, shell=True)
  return version.rstrip()
