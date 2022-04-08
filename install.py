#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
from pathlib import Path

from config import load_config
from create_ext4 import build_dir
from utils import RunCommand

fastboot = load_config('LINUX', 'fastboot')
source_dir = os.path.join(load_config('MAIN', 'main_project'), "source")

if not os.path.isfile(fastboot):
  exit(1)

for boot in Path(source_dir).rglob('boot.img'):
  RunCommand([fastboot, 'flash', 'boot', str(boot)], verbose=True)

for dtbo in Path(source_dir).rglob('dtbo.img'):
  RunCommand([fastboot, 'flash', 'dtbo', str(dtbo)], verbose=True)

for vbmeta in Path(source_dir).rglob('vbmeta.img'):
  RunCommand([fastboot, 'flash', 'vbmeta', str(vbmeta)], verbose=True)

for vbmeta_system in Path(source_dir).rglob('vbmeta_system.img'):
  RunCommand([fastboot, 'flash', 'vbmeta_system',
              str(vbmeta_system)], verbose=True)

for img in os.listdir(build_dir):
  RunCommand([fastboot, 'flash', img.split('.sparse')[0],
              os.path.join(build_dir, img)], verbose=True)


ans = input(
  "It will delete all your files and photos stored on internal storage. [y/n]: ")
if ans.lower() == 'y':
  RunCommand([fastboot, 'erase', 'metadata'], verbose=True)
  RunCommand([fastboot, 'erase', 'userdata'], verbose=True)

ans = input("If you want to reboot [y/n]")
if ans.lower() == 'y':
  RunCommand([fastboot, 'reboot'], verbose=True)
