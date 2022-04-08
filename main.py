#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import argparse
import os
import sys

from loguru import logger

import create_ext4
import ex_fw
from config import load_config, update_config
from utils import RunCommand, init_log, mkdir, rmdir

__version__ = '1.0'

PARTITIONS = load_config('MAIN', 'partitions').split(' ')


def init_folders(project):
  folders = load_config('MAIN', 'proj_folders').split(' ')
  for f in folders:
    mkdir(os.path.join(project, f))


def parser():
  parser = argparse.ArgumentParser(
    description='')
  parser.add_argument('-n', dest='name', help='Specify project name')
  parser.add_argument('-i', dest='input', help='Input zip')
  parser.add_argument('-l', dest='lst', action='store_true',
                      help='List of projects')
  parser.add_argument('-R', dest='raw', action='store_true',
                      help='Build ext4 image (linux only)')
  parser.add_argument('-S', dest='sparse', action='store_true',
                      help='Build Sparse image (linux only) with [-R]')
  parser.add_argument('-B', dest='brotli', action='store_true',
                      help='Build .sdat.br image (linux only) with [-RS]')
  parser.add_argument('-V', '--version', dest='version',
                      action='store_true', help='Display version')
  return parser


if __name__ == '__main__':
  init_log('Log.txt')

  parser = parser()
  args = parser.parse_args()

  if len(sys.argv) < 2:
    parser.print_usage()

  if args.version:
    print(f"{__version__}")

  if args.name:
    logger.info("Your project name: {}", args.name)

    data = {'main_project': os.path.join('projects', args.name)}
    update_config('MAIN', data)

    init_folders(load_config('MAIN', 'main_project'))

  main_project = load_config('MAIN', 'main_project')

  if args.lst:
    print('List of projects: ')
    for p in os.listdir('projects'):
      print('\t%s' % p)

  if args.input:
    if os.path.isdir(os.path.join('projects', args.name)):
      logger.warning("This project exist")
      choice = input("If you want to continu will delete this project [y/n]: ")
      if choice.lower() == 'y':
        logger.info('Remove project {}', load_config('MAIN', 'main_project'))
        rmdir(os.path.join('projects', args.name))
      else:
        pass

    ex_fw.main(args.input, os.path.join(main_project, 'source'), 'Log.txt')
    for part in PARTITIONS:
      ext4_info = os.path.join(load_config('PYTHON', 'ext4_info'))
      extract_ext4 = os.path.join(load_config('PYTHON', 'extract_ext4'))

      input_img = os.path.join(main_project, 'source', part+'.img')
      info_dir = os.path.join(main_project, 'config')
      out_dir = os.path.join(main_project, 'output', part)
      if os.path.isfile(input_img):
        mkdir(out_dir)
        logger.info("Extract information {}", part)
        cmd = ['python', ext4_info, input_img, info_dir]
        RunCommand(cmd, verbose=True)
        logger.info("Extract {} to {}", input_img, out_dir)
        cmd = ['python', extract_ext4, input_img, out_dir]
        RunCommand(cmd, verbose=True)

  if args.raw:
    raw = True
  else:
    raw = False

  if args.sparse:
    sparse = True
  else:
    sparse = False

  if args.brotli:
    brotli = True
  else:
    brotli = False

  if sparse or raw or brotli:
    create_ext4.main(raw, sparse, brotli)
