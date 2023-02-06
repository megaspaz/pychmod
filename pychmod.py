#!/usr/bin/env python3
#
# Copyright 2006 by megaspaz
# All Rights Reserved.
#
# Script Name: pychmod.py

"""Chmod a directory and all of its subdirectories and files.

This script chmods a directory and all its subdirectories to the specified
permissions mode with the default being 0755. It chmods all of the directory's
files to the specified permissions with the default being 0644. It chmods
script/executable files to the specified permissions with the default being
0755. Script/executable files are determined by a list of file extensions.
Files with no file extension are treated as regular files.

Usage: pychmod.py --dir[-d]=<dir> [--dirperms|-p]=<perm> [--fileperms|-f]=<perm>
  [--execperms|-x]=<perm> [--symlinks|-s] [--verbose|-v] [--help|-h]

  -d --dir        Directory to traverse. Required.
  -p --dirperms   Permissions for directories - default 0755. Optional.
  -f --fileperms  Permissions for files - default 0644. Optional.
  -s --symlinks   Follow and process symlinks - default False. Optional.
  -v --verbose    Prints the current directory/file - default False. Optional.
  -x --execperms  Perms for scripts/executables. - default 0755. Optional.
                  [ .bash .cgi .csh .exe .o .out .par .pl .py .pyc .pyo .rb
                  .sh .so ]
  -h --help       Print this usage and exit.
"""

__author__ = "megaspaz <megaspaz2k7<at>gmail.com>"

import getopt
import os
import re
import sys

# Constants
_DEF_DIR_PERMS = '0755'
_DEF_FILE_PERMS = '0644'
_DEF_EXEC_PERMS = '0755'
_EXE_LIST = [
    '.bash', '.cgi', '.csh', '.exe', '.o', '.out', '.par', '.pl', '.py',
    '.pyc', '.pyo', '.rb', '.sh', '.so'
]
_DEF_VERBOSE = False
_DEF_SYM = False


def _get_options():
  """This function gets the options from sys.arg"""

  try:
    # pylint: disable=unused-variable
    opts, args = getopt.getopt(sys.argv[1:], 'd:f:p:x:hsv',
                               ['dir=', 'dirperms=', 'fileperms=',
                                'execperms=', 'symlinks', 'help',
                                'verbose'])

    basedir = None
    dirperms = _DEF_DIR_PERMS
    fileperms = _DEF_FILE_PERMS
    scriptperms = _DEF_EXEC_PERMS
    verbose = _DEF_VERBOSE
    followsymlinks = _DEF_SYM
    for (name, value) in opts:
      if name in ("-h", "--help"):
        # Print usage and exit.
        return (0, None, [_DEF_DIR_PERMS, _DEF_FILE_PERMS, _DEF_EXEC_PERMS], _DEF_VERBOSE, _DEF_SYM)

      if name in ("-d", "--dir"):
        basedir = value.strip()
      elif name in ("-p", "--dirperms"):
        dirperms = value.strip()
      elif name in ("-f", "--fileperms"):
        fileperms = value.strip()
      elif name in ("-x", "--execperms"):
        scriptperms = value.strip()
      elif name in ("-s", "--symlinks"):
        followsymlinks = True
      elif name in ("-v", "--verbose"):
        verbose = True
      else:
        # Throw usage error.
        raise KeyError('Invalid flag: %s' % name)

    if basedir is None or not os.path.isdir(basedir):
      raise ValueError('Directory (--dir or -d) required and must be of type directory.')

    return 0, basedir, _process_resources(dirperms, fileperms, scriptperms), verbose, followsymlinks

  except(getopt.GetoptError, KeyError, ValueError) as err:
    return (-1, err, [_DEF_DIR_PERMS, _DEF_FILE_PERMS, _DEF_EXEC_PERMS], _DEF_VERBOSE, _DEF_SYM)


def _process_resources(dirperms, fileperms, scriptperms):
  """Determine permissions. If user input invalid, then assign default permissions."""

  perm_regex = re.compile('^[0-7]{4}$')
  if (perm_regex.match(dirperms) is None or perm_regex.match(fileperms) is None or
          perm_regex.match(scriptperms) is None):
    raise ValueError('Invalid permission(s). Permission values must consist of 4 digits.')

  return [dirperms, fileperms, scriptperms]


def _use_permissions(somefile, fperms, xperms):
  """Determine if we should use script permissions or not."""

  # No file extension? Maybe it's a script. Check She-bang...
  file_desc = None
  line = ''
  try:
    file_desc = open(somefile, 'r')
    line = file_desc.readline()
  except OSError:
    line = ''
  finally:
    file_desc.close()

  return xperms if line.startswith("#!") else fperms


def _chmod_files(directory, perms, verbose, followsymlinks):
  """Change permissions depending on the type of resource"""

  listing = os.listdir(directory)
  dirlist = [os.path.join(directory, filename) for filename in listing]

  # Unpack perms list.
  (dperms, fperms, xperms) = perms

  # Change the permissions of the passed directory and print if verbose is true.
  os.chmod(directory, int(dperms, 8))
  if verbose:
    sys.stdout.write('dir: %s\n' % directory)

  # Loop through the listing looking for sub directories.
  for somefile in dirlist:
    # Check if somefile is a symlink.
    if os.path.islink(somefile) and followsymlinks is False:
      # Flag set to False. Do not follow.
      continue

    if os.path.isdir(somefile):
      # Traverse this directory
      _chmod_files(somefile, perms, verbose, followsymlinks)
    else:
      # This is a non-dir file. chmod and print if verbose is true.
      # Check to see if somefile has a file extension.
      partslist = somefile.split('.')
      if len(partslist) == 1:
        os.chmod(somefile, int(_use_permissions(somefile, fperms, xperms), 8))
        if verbose:
          sys.stdout.write('file: %s\n' % somefile)
      else:
        # This file has a file extension. Check to see if it's in exec list.
        fileext = '.%s' % partslist[-1]
        if _EXE_LIST.count(fileext) == 0:
          # Not in exec list. Regular file.
          os.chmod(somefile, int(fperms, 8))
          if verbose:
            sys.stdout.write('file: %s\n' % somefile)
        else:
          # Is in the exec list. Script/Exec file.
          os.chmod(somefile, int(xperms, 8))
          if verbose:
            sys.stdout.write('script/executable: %s\n' % somefile)


def main():
  """Main program."""

  retval, startdir, perms, verbose, followsymlinks = _get_options()
  if retval:
    # getopt error occurred.
    sys.stderr.write('\nERROR: %s\n\n%s\n' % (startdir, __doc__))
    return retval

  if startdir is None:
    # User entered -h for option
    sys.stdout.write(__doc__)
    return retval

  try:
    sys.stdout.write('chmod dirs to %s\nchmod files to %s\n'
                     'chmod scripts to %s\n' % (perms[0], perms[1], perms[2]))
    _chmod_files(startdir, perms, verbose, followsymlinks)
    return 0
  except(IOError, OSError, MemoryError) as err:
    sys.stderr.write('%s\n' % str(err))
    return err.errno


if __name__ == '__main__':
  sys.exit(main())
