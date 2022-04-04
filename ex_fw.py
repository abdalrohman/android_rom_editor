import argparse
import gzip
import os
import re
import shutil
import sys
import zipfile

from loguru import logger

from config import load_config
from utils import RunCommand, init_log, mkdir, remove

# tools #################
brotli = load_config('LINUX', 'brotli')
simg2img = load_config('LINUX', 'simg2img')
lpunpack = load_config('LINUX', 'lpunpack')
payload = load_config('LINUX', 'payload')
sdat2img = load_config('PYTHON', 'sdat2img')

#########################


# functions #############
def extract_zip(input_zip, output):
  """extract zip file

  Args:
      input: input zip
      output: output folder
  """
  logger.info('Extracting %s to %s' % (input_zip, output))
  with zipfile.ZipFile(input_zip, 'r') as zf:
    zf.extractall(output)


def extract_file_from_zip(input_zip, output, members=None):
  """extract some files from a zip file

  Args:
      input: input zip
      output: output folder
      members (optional): specify files to extract. Defaults to None.
  """
  try:
    logger.info('Extracting %s from %s to %s' % (members, input_zip, output))
    with zipfile.ZipFile(input_zip, 'r') as zf:
      zf.extractall(output, members=[members])
  except KeyError:
    logger.error("Can't extract %s from archive", members)


def zip_list(input_zip):
  with zipfile.ZipFile(input_zip, 'r') as zf:
    list_files = zf.infolist()
    lf = []
    for f in list_files:
      lf.append(f.filename)
    return sorted(lf)


def find_in_list(lst, element):
  """Search for specfic element inside list

  Args:
      lst (list): _description_
      element: elemnt in list
  Returns:
      True: found
      False: not found
  """
  for i in range(len(lst)):
    if lst[i] == element:
      return True
  return False


def check_zip(zip_file):
  """check if this zip file or not

  Args:
      zip (zipfile): input zip file

  Returns:
      0: Good zip file
      1: Bad zip file
  """
  if os.path.exists(zip_file):
    logger.info("Testing %s\n" % zip_file)

    if zipfile.ZipFile(zip_file).testzip() is not None:
      logger.error("Bad zip file %s", zip_file)
      return 1
    else:
      return 0
  else:
    logger.error("Not found %s", zip_file)


def gnuzip(input_zip, output):
  """Gunzips the given gzip compressed file to a given output file

  Args:
      input : input gzip file.
      output : output file.
  """
  with gzip.open(input_zip, "rb") as in_file, \
      open(output, "wb") as out_file:
    shutil.copyfileobj(in_file, out_file)


def extract_brotli(br_img, output):
  """Extract .br extention.

  must have [br_img.transfers.list] in the same directory

  Args:
      br_img : brotli image (eg: system.new.dat.br)
      output : output folder
  """
  # check if image.new.dat.br is exist befor converting
  if os.path.exists(br_img):
    basedir = os.path.realpath(os.path.dirname(br_img))
    output = os.path.realpath(output)
    sdat_img = br_img.split('.br')[0]
    img_name = os.path.basename(br_img).split('.')[0]
    # check if output folder exists (if not make it)
    if not os.path.exists(output):
      mkdir(output)

    logger.info("Convert %s.new.dat.br to %s.new.dat" % (img_name, img_name))
    cmd = [brotli, '-df', br_img]
    RunCommand(cmd, verbose=True)

    if os.path.exists(sdat_img):
      logger.info('Convertig %s.new.dat to %s.img' % (img_name, img_name))
      cmd = [
        'python', sdat2img, os.path.join(
          basedir, img_name+'.transfer.list'), sdat_img, os.path.join(output, img_name+'.img')
      ]
      RunCommand(cmd, verbose=True)

    if os.path.exists(os.path.join(output, img_name+'.img')):
      remove(br_img)
      remove(os.path.join(output, img_name+'.new.dat'))
      remove(os.path.join(output, img_name+'.transfer.list'))

  else:
    logger.info("Not found %s", br_img)


def extract_super_img(input_img, output, type='sparse'):
  raw_img = os.path.join(output, "super.raw")

  if type == 'sparse':
    logger.info("Extracting sparse super image...")
    cmd = [simg2img, input_img, raw_img]
    RunCommand(cmd, verbose=True)
    if os.path.exists(raw_img):
      remove(input_img)  # cleanup after extract

  elif type == 'gz':
    logger.info("Extracting gzip super image...")
    gnuzip(input_img, raw_img)
    if os.path.exists(raw_img):
      remove(input_img)  # cleanup after extract

  elif type == 'brotli':
    logger.info("Extracting brotli super image...")
    extract_brotli(input_img, output)
    os.rename(os.path.join(output, 'super.img'),
              os.path.join(output, 'super.raw'))

  else:
    logger.info("Not supported yet.")

  # extract images from super.img
  try:
    logger.info("Extracting raw super image...")
    if os.path.exists(raw_img):
      cmd = [lpunpack, raw_img, output]
      _, ret = RunCommand(cmd, verbose=True)
      remove(raw_img)  # cleanup after extract

  except:
    logger.error("Error when extracting raw super image...")
    exit(1)


def extract_payload(img, output):
  cmd = [payload, '-o', output, img]
  RunCommand(cmd)
  remove(img)


def extract_fw(input_zip, output_folder):
  list_images = []
  list_zip = zip_list(input_zip)
  br = False
  super_img = False
  extracted_list = ['odm', 'system', 'vendor', 'product', 'system_ext', 'cust']
  list_other = ['vbmeta_system', 'vbmeta', 'boot', 'dtbo']

  for lz in list_zip:
    if re.search(r"(super.*)", lz) is not None:  # super
      super_img = True
      list_images.append(lz)

    elif lz == 'system.new.dat.br':
      br = True

    elif lz == 'payload.bin':
      extract_file_from_zip(input_zip, output_folder, members=lz)
      extract_payload(os.path.join(
        output_folder, 'payload.bin'), output_folder)

    else:
      continue

  if super_img:
    for s in list_images:
      if re.search(r"(super.img.gz)", s) is not None:
        logger.info("Gzip super image detected.")
        extract_file_from_zip(input_zip, output_folder, members=s)
        extract_super_img(os.path.join(
          output_folder, s), output_folder, type='gz')

      elif re.search(r"(super.new.dat.br)", s) is not None:
        logger.info("Brotli super image detected.")
        extract_file_from_zip(input_zip, output_folder,
                              members='super.new.dat.br')
        extract_file_from_zip(input_zip, output_folder,
                              members='super.transfer.list')

        extract_super_img(os.path.join(
          output_folder, 'super.new.dat.br'), output_folder, type='brotli')

      elif re.search(r'super.img', s) is not None:  # sparse
        logger.info("Sparse super image detected.")
        extract_file_from_zip(input_zip, output_folder, members=s)
        extract_super_img(os.path.join(
          output_folder, s), output_folder)

  if br:
    logger.info("Brotli images detected.")
    for br_img in extracted_list:
      for in_zip in list_zip:
        if in_zip == br_img+'.new.dat.br':
          extract_file_from_zip(input_zip, output_folder, members=in_zip)
          extract_file_from_zip(input_zip, output_folder,
                                members=br_img+'.transfer.list')
          extract_brotli(os.path.join(output_folder, in_zip), output_folder)

  # extract other images from zip file
  for other in list_zip:
    for lo in list_other:
      if re.search(rf"({lo}.*)", other) is not None:
        extract_file_from_zip(input_zip, output_folder, members=other)


#########################


def main(input_zip, output, log_file=None):
  if log_file is not None:
    init_log(log_file)
  else:
    init_log()

  if check_zip(input_zip) == 0:
    extract_fw(input_zip, output)
  else:
    exit(1)


def parser():
  parser = argparse.ArgumentParser(
    description='')
  parser.add_argument('input', help='Input rom zip')
  parser.add_argument('output', help='Specify output directory')
  parser.add_argument('-l', '--log', dest='log',  help='Specify log file')

  return parser


if __name__ == '__main__':
  parser = parser()
  args = parser.parse_args()

  if len(sys.argv) < 2:
    parser.usage()

  if args.log:
    log_file = args.log
  else:
    log_file = None

  if args.input:
    input_zip = args.input

  if args.output:
    output = args.output
    if not os.path.exists(output):
      mkdir(output)

  main(input_zip, output, log_file)
