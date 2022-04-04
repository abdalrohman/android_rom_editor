#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# write and restore config.ini


import configparser


def write_config(section, data, config_file='config.ini'):
  config = configparser.ConfigParser(delimiters=':')
  config.read(config_file)

  config[section] = data

  with open(config_file, 'w') as configfile:
    config.write(configfile)

  return 0


def update_config(section, data, config_file='config.ini'):
  config = configparser.ConfigParser(delimiters=':')
  config.read(config_file)

  if config.has_section(section):
    for key, value in data.items():
      config.set(section, key, value)

    with open(config_file, 'w') as configfile:
      config.write(configfile)
    return 0
  else:
    print(f'Not found {section} in {config_file}')
    exit(1)


def load_config(section, key, config_file='config.ini'):
  config = configparser.ConfigParser(delimiters=':')
  config.read(config_file)
  value = config[section].get(key)

  return value


def write_default_config():
  win = {
    'wsl_exe': '/mnt/c/Windows/system32/wsl.exe'
  }
  linux = {
    'brotli': 'bin/brotli',
    'payload': 'bin/payload-dumper-go',
    'mke2fs': 'bin/mke2fs',
    'mke2fs_conf': 'bin/mke2fs.conf',
    'e2fsdroid': 'bin/e2fsdroid',
    'img2simg': 'bin/img2simg',
    'simg2img': 'bin/simg2img',
    'lpunpack': 'bin/lpunpack',
    'fastboot': 'bin/fastboot'
  }
  python = {
    'ext4_info': 'bin/python/ext4_info.py',
    'extract_ext4': 'bin/python/extract_ext4.py',
    'img2sdat': 'bin/python/img2sdat/img2sdat.py',
    'sdat2img': 'bin/python/sdat2img.py'
  }
  main = {
    'main_project': 'projects/',
    'partitions': 'odm system vendor product system_ext my_engineering my_preload my_manifest my_company my_stock my_bigball my_product my_heytap my_region',
    'proj_folders': 'config build backup assert source output'
  }

  write_config('MAIN', main)
  write_config('WIN', win)
  write_config('LINUX', linux)
  write_config('PYTHON', python)


# TODO:
if __name__ == '__main__':
  write_default_config()
