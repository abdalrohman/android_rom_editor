#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import os
import shutil
import subprocess
import sys
import time

from loguru import logger

from config import load_config
from utils import RunCommand, init_log, remove

init_log('Log.txt')

mke2fs = load_config('LINUX', 'mke2fs')
mke2fs_conf = load_config('LINUX', 'mke2fs_conf')
e2fsdroid = load_config('LINUX', 'e2fsdroid')
img2simg = load_config('LINUX', 'img2simg')
brotli_tool = load_config('LINUX', 'brotli')
img2sdat = load_config('PYTHON', 'img2sdat')
config_dir = os.path.join(load_config('MAIN', 'main_project'), 'config')
build_dir = os.path.join(load_config('MAIN', 'main_project'), 'build')
out_dir = os.path.join(load_config('MAIN', 'main_project'), 'output')


def dump_data(file):
  """
  search for data from output of tune2fs command
  """
  uuid_searche = 'Filesystem UUID:'
  inode_size_searche = 'Inode size:'
  reserved_percent_searche = 'Reserved block count:'
  block_size_searche = 'Block size:'
  inode_count_searche = 'Inode count:'
  part_size_searche = 'Partition size:'

  with open(file, 'r') as file:
    lines = file.readlines()

    for l in lines:
      if uuid_searche in l:
        uuid = l.split(':')[1].strip()
      if inode_size_searche in l:
        inode_size = l.split(':')[1].strip()
      if reserved_percent_searche in l:
        reserved_percent = l.split(':')[1].strip()
      if block_size_searche in l:
        block_size = l.split(':')[1].strip()
      if inode_count_searche in l:
        inode_count = l.split(':')[1].strip()
      if part_size_searche in l:
        part_size = l.split(':')[1].strip()

  return (uuid, inode_size, inode_count, block_size, reserved_percent, part_size)


def print_images():
  """return list of images to build

  Returns:
      user choice: list
  """
  print(f"Images list in {out_dir}: ")
  for part in os.listdir(out_dir):
    print(f'\t{part}')
  print('\tall')
  choice = input(
    "\nType name of image you want to build it [eg: system odm]: ")
  if choice == 'all':
    choice = os.listdir(out_dir)
  else:
    choice = choice.split(' ')  # make list from input

  return choice


def run_command(cmd, env):
  """Runs the given command.

  Args:
    cmd: the command represented as a list of strings.
    env: a dictionary of additional environment variables.
  Returns:
    A tuple of the output and the exit code.
  """
  start_time = time.time()
  logger.info("Env: {}", env)
  logger.info("Running: {}", " ".join(cmd))

  env_copy = os.environ.copy()
  env_copy.update(env)

  p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                       env=env_copy)
  output, _ = p.communicate()

  runtime = (time.time() - start_time)
  logger.info("Excution time: {} seconds", runtime)

  return output, p.returncode


def make_ext4(raw=False, sparse=False, brotli=False):
  images_build = print_images()

  for part in images_build:
    if raw:
      if os.path.exists(os.path.join(out_dir, part)):
        file_features = os.path.join(config_dir, part+'_file_features.txt')
        uuid, inode_size, inode_count, block_size, reserved_percent, part_size = dump_data(
          file_features)

        # truncate output file since mke2fs will keep verity section in existing file
        with open(os.path.join(build_dir, part+'.img'), 'w') as output:
          output.truncate()

        # run mke2fs
        if part == 'system':
          mke2fs_cmd = [
            mke2fs, '-O', '^has_journal', '-L', part, '-N', inode_count, '-I', inode_size, '-M', '/', '-m', reserved_percent, '-U', uuid,
            '-t', 'ext4', '-b', block_size, os.path.join(
              build_dir, part+'.img'), str(int(part_size) // int(block_size))
          ]

        else:
          mke2fs_cmd = [
            mke2fs, '-O', '^has_journal', '-L', part, '-N', inode_count, '-I', inode_size, '-M', '/' +
            part, '-m', reserved_percent, '-U', uuid,
            '-t', 'ext4', '-b', block_size, os.path.join(
              build_dir, part+'.img'), str(int(part_size) // int(block_size))
          ]

        mke2fs_env = {"MKE2FS_CONFIG": "./bin/mke2fs.conf",
                      "E2FSPROGS_FAKE_TIME": "1230768000"}

        output, ret = run_command(mke2fs_cmd, mke2fs_env)
        if ret != 0:
          logger.error(f"Failed to run mke2fs: {output}")
          sys.exit(4)

        # run e2fsdroid
        e2fsdroid_env = {"E2FSPROGS_FAKE_TIME": "1230768000"}

        if part == 'system':
          e2fsdroid_cmd = [
            e2fsdroid, '-e', '-T', '1230768000', '-C', os.path.join(config_dir, part+'_file_config.txt'), '-S', os.path.join(
              config_dir, part+'_file_contexts.txt'), '-S', os.path.join(config_dir, 'file_contexts.txt'), '-f', os.path.join(out_dir, part), '-a', '/', os.path.join(build_dir, part+'.img')
          ]

        else:
          try:
            e2fsdroid_cmd = [
              e2fsdroid, '-e', '-T', '1230768000', '-C', os.path.join(config_dir, part+'_file_config.txt'), '-S', os.path.join(
                config_dir, part+'_file_contexts.txt'), '-S', os.path.join(config_dir, 'file_contexts.txt'), '-f', os.path.join(out_dir, part), '-a', '/'+part, os.path.join(build_dir, part+'.img')
            ]

          except:
            logger.info(
              f"Try without ({os.path.join(config_dir, part+'_file_config.txt')})")
            e2fsdroid_cmd = [
              e2fsdroid, '-e', '-T', '1230768000', '-S', os.path.join(
                config_dir, part+'_file_contexts.txt'), '-S', os.path.join(config_dir, 'file_contexts.txt'), '-f', os.path.join(out_dir, part), '-a', '/'+part, os.path.join(build_dir, part+'.img')
            ]

        output, ret = run_command(e2fsdroid_cmd, e2fsdroid_env)
        if ret != 0:
          logger.error(f"Failed to run e2fsdroid_cmd: {output}")
          remove(os.path.join(build_dir, part+'.img'))
          sys.exit(4)
        print('')

    if sparse:
      raw_img = os.path.join(build_dir, part+'.img')
      sparse_img = os.path.join(build_dir, part+'.sparse')
      if os.path.exists(raw_img):
        logger.info('Convert raw image to sparse...')
        cmd = [img2simg, raw_img, sparse_img]
        RunCommand(cmd, verbose=True)

      if os.path.isfile(sparse_img):
        remove(raw_img)

    if brotli:
      sparse_img = os.path.join(build_dir, part+'.sparse')
      sdat_img = os.path.join(build_dir, part+'.new.dat')
      if os.path.exists(sparse_img):
        logger.info('Convert sparse image to sdat...')
        cmd = ['python', img2sdat, '-o', build_dir,
               '-p', part, sparse_img, '402653184']
        RunCommand(cmd, verbose=True)

        if os.path.isfile(sdat_img):
          remove(sparse_img)

        logger.info('Compress with brotli...')
        cmd = [brotli_tool, '-q', '6', '-v', '-f', sdat_img]
        RunCommand(cmd, verbose=True)

        if os.path.isfile(sdat_img+'.br'):
          remove(sdat_img)


def main(raw=False, sparse=False, brotli=False):
  if not os.path.exists(os.path.join(config_dir, 'file_contexts.txt')):
    if os.path.exists(os.path.join(out_dir, 'system/system/etc/selinux/plat_file_contexts')):
      shutil.copyfile(os.path.join(out_dir, 'system/system/etc/selinux/plat_file_contexts'),
                      os.path.join(config_dir, 'file_contexts.txt'))

  make_ext4(raw, sparse, brotli)


if __name__ == '__main__':
  if not os.path.exists(os.path.join(config_dir, 'file_contexts.txt')):
    if os.path.exists(os.path.join(out_dir, 'system/system/etc/selinux/plat_file_contexts')):
      shutil.copyfile(os.path.join(out_dir, 'system/system/etc/selinux/plat_file_contexts'),
                      os.path.join(config_dir, 'file_contexts.txt'))
  make_ext4(False, False, False)
