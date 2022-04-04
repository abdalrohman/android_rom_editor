#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re

from config import load_config
from create_ext4 import build_dir
from utils import RunCommand

fastboot = load_config('LINUX', 'fastboot')
source_dir = os.path.join(load_config('MAIN', 'main_project'), "source")

if not os.path.isfile(fastboot):
  exit(1)

ans = input(
  "It will delete all your files and photos stored on internal storage. [y/n]: ")


if ans.lower() == 'y':
  for img in os.listdir(source_dir):
    if re.search(rf"('boot.img')", img) is not None:
      RunCommand([fastboot, 'flash', 'boot', os.path.join(
        source_dir, img)], verbose=True)

    if re.search(rf"('dtbo.img')", img) is not None:
      RunCommand([fastboot, 'flash', 'dtbo', os.path.join(
        source_dir, img)], verbose=True)

    if re.search(rf"('vbmeta.img')", img) is not None:
      RunCommand([fastboot, 'flash', 'vbmeta', os.path.join(
        source_dir, img)], verbose=True)

    if re.search(rf"('vbmeta_system.img')", img) is not None:
      RunCommand([fastboot, 'flash', 'vbmeta_system', os.path.join(
        source_dir, img)], verbose=True)

  for img in os.listdir(build_dir):
    RunCommand([fastboot, 'flash', img.split('.sparse')[0],
               os.path.join(build_dir, img)], verbose=True)

  RunCommand([fastboot, 'erase', 'metadata'], verbose=True)
  RunCommand([fastboot, 'erase', 'userdata'], verbose=True)
  RunCommand([fastboot, 'reboot'], verbose=True)


else:
  exit(1)
