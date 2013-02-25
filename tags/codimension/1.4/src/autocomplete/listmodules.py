#!/usr/bin/python
# $Id$
#
# Locate all standard modules available in this build.
#
# This script is designed to run on Python 1.5.2 and newer.
#
# Written by Fredrik Lundh, January 2005
# Adopted for codimension by Sergey Satskiy, 2011
#

" Routines to get a list of modules; sys and for a dir "

import imp, sys, os, re

# known test packages
TEST_PACKAGES = "test.", "bsddb.test.", "distutils.tests."

__suffixes = imp.get_suffixes()

def __getSuffix( fileName ):
    " Provides suffix info for a file name "
    for suffix in __suffixes:
        if fileName[ -len( suffix[ 0 ] ) : ] == suffix[ 0 ]:
            return suffix
    return None


def getSysModules():
    " Provides a dictionary of system modules. The pwd dir is excluded. "

    paths = __getSysPathExceptCurrent()

    modules = {}
    for modName in sys.builtin_module_names:
        if modName not in [ '__builtin__', '__main__' ]:
            modules[ modName ] = None

    # The os.path depends on the platform, so I insert it here as an exception
    modules[ "os.path" ] = None

    for path in paths:
        modules.update( getModules( path ) )

    return modules


class DevNull:
    " Stderr supresser "
    def write( self, data ):
        " Supresses everything what is written into a stream "
        pass

def __isTestModule( modName ):
    " Returns True if it is a test module "
    for modToDel in TEST_PACKAGES:
        if modName[ : len( modToDel ) ] == modToDel:
            return True
    return False

__regexpr = re.compile("(?i)[a-z_]\w*$")

def getModules( path ):
    " Provides modules in a given directory "

    oldStderr = sys.stderr
    sys.stderr = DevNull()
    modules = {}
    for fName in os.listdir( path ):
        fName = os.path.join( path, fName )
        if os.path.isfile( fName ):
            modName, e = os.path.splitext( fName )
            suffix = __getSuffix( fName )
            if not suffix:
                continue
            modName = os.path.basename( modName )
            if modName == "__init__":
                continue
            if __regexpr.match( modName ):
                if suffix[ 2 ] == imp.C_EXTENSION:
                    # check that this extension can be imported
                    try:
                        __import__( modName )
                    except:
                        # There could be different errors,
                        # so to be on the safe side all are supressed
                        continue
                if not __isTestModule( modName ):
                    if not fName.endswith( ".pyc" ):
                        modules[ modName ] = os.path.realpath( fName )
        elif os.path.isdir( fName ):
            modName = os.path.basename( fName )
            if os.path.isfile( os.path.join( fName, "__init__.py" ) ) or \
               os.path.isfile( os.path.join( fName, "__init__.py3" ) ):
                if not __isTestModule( modName ):
                    modules[ modName ] = os.path.realpath( fName )
                for subMod, fName in getModules( fName ).items():
                    candidate = modName + "." + subMod
                    if not __isTestModule( candidate ):
                        modules[ candidate ] = os.path.realpath( fName )
    sys.stderr = oldStderr
    return modules

def __getSysPathExceptCurrent():
    " Provides a list of paths for system modules "

    path = map( os.path.realpath, map( os.path.abspath, sys.path[ : ] ) )

    def __filterCallback( path, cwd = os.path.realpath( os.getcwd() ) ):
        " get rid of non-existent directories and the current directory "
        return os.path.isdir( path ) and path != cwd

    return filter( __filterCallback, path )

if __name__ == "__main__":
    names = getSysModules().keys()
    names.sort()
    for name in names:
        print name
