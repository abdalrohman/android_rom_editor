import sys



if not sys.version_info >= (3, 6):
  print("Python 3.6 or higher is required.")
  print("You are using Python {}.{}.".format(
    sys.version_info.major, sys.version_info.minor))
  sys.exit(1)
