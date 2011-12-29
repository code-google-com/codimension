#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# codimension - graphics python two-way code editor and analyzer
# Copyright (C) 2010  Sergey Satskiy <sergey.satskiy@gmail.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# $Id$
#

"""
codimension main Python script.
It performs necessery initialization and starts the Qt main loop.
"""

__version__ = "0.0"

import sys, os.path, traceback, logging, shutil, time
from PyQt4                      import QtGui
from optparse                   import OptionParser
from PyQt4.QtCore               import SIGNAL, SLOT, QTimer, QDir
from utils.latestver            import getLatestVersionFile
from autocomplete.completelists import buildSystemWideModulesList


# Workaround if link is used
sys.argv[0] = os.path.realpath( sys.argv[0] )

# Make it possible to import from the subdirectories
srcDir = os.path.dirname( os.path.abspath( sys.argv[0] ) )
if not srcDir in sys.path:
    sys.path.append( srcDir )

from utils.settings         import Settings
from utils.globals          import GlobalData
from ui.application         import CodimensionApplication
from ui.splashscreen        import SplashScreen
from utils.pixmapcache      import PixmapCache
from utils.project          import CodimensionProject
from utils.skin             import Skin


# Saving the root logging handlers
__rootLoggingHandlers = []


def codimensionMain():
    """ The codimension driver """

    # Parse command line arguments
    parser = OptionParser(
    """
    %prog [options] [project file | python files]
    Runs codimension UI
    """,
    version = "%prog " + __version__ )

    parser.add_option( "--debug",
                       action="store_true", dest="debug", default=False,
                       help="switch on debug and info messages (default: Off)" )

    options, args = parser.parse_args()

    # Configure logging
    setupLogging( options.debug )

    # The default exception handler can be replaced
    sys.excepthook = exceptionHook

    # Create global data singleton.
    # It's unlikely to throw any exceptions.
    globalData = GlobalData()
    globalData.version = __version__

    # Create pixmap cache singleton
    pixmapCache = PixmapCache()

    # Loading settings - they have to be loaded before the application is
    # created. This is because the skin name is saved there.
    settings = Settings()
    copySkin()

    # Load the skin
    globalData.skin = Skin()
    globalData.skin.load( settings.basedir + "skins" + \
                          os.path.sep + settings.skinName )

    # Create QT application
    codimensionApp = CodimensionApplication( sys.argv )
    globalData.application = codimensionApp

    logging.debug( "Starting codimension v." + __version__ )

    try:
        # Process command line arguments
        projectFile = processCommandLineArgs( args )
    except Exception, exc:
        logging.error( str( exc ) )
        parser.print_help()
        return 1

    # Show splash screen
    splash = SplashScreen()
    globalData.splash = splash

    screenSize = codimensionApp.desktop().screenGeometry()
    globalData.screenWidth = screenSize.width()
    globalData.screenHeight = screenSize.height()


    splash.showMessage( "Applying skin to lexers..." )
    from editor.lexer import updateLexersStyles
    updateLexersStyles( globalData.skin )

    splash.showMessage( "Importing packages..." )
    from ui.mainwindow import CodimensionMainWindow

    splash.showMessage( "Building system wide modules list..." )
    buildSystemWideModulesList()

    splash.showMessage( "Generating main window..." )
    mainWindow = CodimensionMainWindow( splash, settings )
    codimensionApp.setMainWindow( mainWindow )
    globalData.mainWindow = mainWindow
    codimensionApp.connect( codimensionApp, SIGNAL( "lastWindowClosed()" ),
                            codimensionApp, SLOT( "quit()" ) )

    # Loading project if given or the recent one
    if projectFile != "":
        splash.showMessage( "Loading project..." )
        globalData.project.loadProject( projectFile )
    elif len( args ) != 0:
        # There are arguments and they are python files
        # The project should not be loaded but the files should
        # be opened
        for fName in args:
            mainWindow.openFile( os.path.abspath( fName ), -1 )
        # Fake signal for triggering browsers layout
        globalData.project.emit( SIGNAL( 'projectChanged' ),
                                 CodimensionProject.CompleteProject )
    elif settings.projectLoaded:
        if len( settings.recentProjects ) == 0:
            return      # Some project was loaded but now it is not available

        splash.showMessage( " Loading recent project..." )
        if os.path.exists( settings.recentProjects[ -1 ] ):
            globalData.project.loadProject( settings.recentProjects[ -1 ] )
        else:
            logging.warning( "Cannot open the most recent project: " + \
                             settings.recentProjects[ -1 ] + \
                             ". Ignore and continue." )
            # Fake signal for triggering browsers layout
            globalData.project.emit( SIGNAL( 'projectChanged' ),
                                     CodimensionProject.CompleteProject )
    else:
        mainWindow.editorsManagerWidget.editorsManager.restoreTabs( \
                                                    settings.tabsStatus )
        # Fake signal for triggering browsers layout
        globalData.project.emit( SIGNAL( 'projectChanged' ),
                                 CodimensionProject.CompleteProject )

    mainWindow.show()

    # The editors positions can be restored properly only when the editors have
    # actually been drawn. Otherwise the first visible line is unknown.
    # So, I load the project first and let object browsers initialize
    # themselves and then manually call the main window handler to restore the
    # editors. The last step is to connect the signal.
    mainWindow.onProjectChanged( CodimensionProject.CompleteProject )
    mainWindow.connect( globalData.project, SIGNAL( 'projectChanged' ),
                        mainWindow.onProjectChanged )

    # Launch the user interface
    QTimer.singleShot( 0, launchUserInterface )

    # Run the application main cycle
    retVal = codimensionApp.exec_()
    return retVal


def launchUserInterface():
    """ UI launch pad """

    globalData = GlobalData()
    if not globalData.splash is None:
        globalData.splash.finish( globalData.mainWindow )
        splashScreen = globalData.splash
        globalData.splash = None
        del splashScreen

    # Check the new version availability
    if int( time.time() ) > Settings().lastSuccessVerCheck + 60 * 60 * 24 * 30:
        # Last check was earlier than a month ago
        success, values = getLatestVersionFile()
        if success:
            Settings().lastSuccessVerCheck = int( time.time() )

            # The file has been read from the web site
            if float( values[ "LatestVersion" ] ) > float( globalData.version ):
                # Newer version is available
                if not Settings().newerVerShown:
                    logging.info( "Newer codimension version " + \
                                  values[ "LatestVersion" ] + \
                                  " is available. Please visit " \
                                  "http://satsky.spb.ru/codimension/codimensionEng.php" )
                    Settings().newerVerShown = True

    # Additional checks may come here

    return


def setupLogging( debug ):
    """ Configures the logging module """

    global __rootLoggingHandlers

    if debug:
        logLevel = logging.DEBUG
    else:
        logLevel = logging.INFO

    # Default output stream is stderr
    logging.basicConfig( level = logLevel,
                         format = "%(levelname) -10s %(asctime)s %(message)s" )

    # Memorize the root logging handlers
    __rootLoggingHandlers = logging.root.handlers
    return


def processCommandLineArgs( args ):
    " Checks what is in the command line "

    # I cannot import it at the top because the fileutils want
    # to use the pixmap cache which needs the application to be
    # created, so the import is deferred
    from utils.fileutils import CodimensionProjectFileType, PythonFileType, \
                                Python3FileType, detectFileType

    if len( args ) == 0:
        return ""

    # Check that all the files exist
    fileType = PythonFileType
    for fName in args:
        if not os.path.exists( fName ):
            raise Exception( "Cannot open file: " + fName )
        if not os.path.isfile( fName ):
            raise Exception( "The " + fName + " is not a file" )
        fileType = detectFileType( fName )
        if fileType not in [ PythonFileType, Python3FileType,
                             CodimensionProjectFileType ]:
            raise Exception( "Unexpected file type (" + \
                             fName + ")" )

    if len( args ) == 1:
        if fileType == CodimensionProjectFileType:
            return args[ 0 ]
        return ""

    # There are many files, check that they are python only
    for fName in args:
        fileType = detectFileType( fName )
        if fileType == CodimensionProjectFileType:
            raise Exception( "Codimension project file (" + \
                             fName + ") must not come " \
                             "together with python files" )
    return ""


def copySkin():
    " Tests if the configured skin is in place. Copies the default if not. "
    localSkinDir = os.path.normpath( str( QDir.homePath() ) ) + \
                   os.path.sep + ".codimension" + os.path.sep + "skins" + \
                   os.path.sep + Settings().skinName
    if os.path.exists( localSkinDir ) and os.path.isdir( localSkinDir ):
        # That's just fine
        return

    # The configured skin has not been found in the user directory,
    # try to find it in the codimension installation and copy it to the
    # user local dir
    skinDir = srcDir + os.path.sep + "skins" + os.path.sep + Settings().skinName
    if os.path.exists( skinDir ) and os.path.isdir( skinDir ):
        # OK, copy it for the user
        try:
            shutil.copytree( skinDir, localSkinDir )
        except Exception, exc:
            logging.error( "Could not create the user skin directory. " \
                           "Continue without a skin." )
            logging.error( str( exc ) )
        return

    # The configured skin dir has not been found anywhere.
    # Try to get back to default.
    logging.warning( "The configured skin '" + Settings().skinName + \
                     "' has not been found neither in the codimension " \
                     "installation nor in the user local tree. " \
                     "Trying to fallback to the 'default' skin." )

    Settings().skinName = 'default'
    if os.path.exists( skinDir ) and os.path.isdir( skinDir ):
        # OK, copy it for the user
        try:
            shutil.copytree( skinDir, localSkinDir )
        except Exception, exc:
            logging.error( "Could not create the user skin directory. " \
                           "Continue without a skin." )
            logging.error( str( exc ) )
        return

    # No bloody good - there will be no skin
    logging.error( "Cannot find the 'default' skin. " \
                   "Please check codimension installation." )
    return


def exceptionHook( excType, excValue, tracebackObj ):
    """ Catches unhandled exceptions """

    globalData = GlobalData()

    # Keyboard interrupt is a special case
    if issubclass( excType, KeyboardInterrupt ):
        if not globalData.application is None:
            globalData.application.quit()
        return

    filename, line, dummy, dummy = traceback.extract_tb( tracebackObj ).pop()
    filename = os.path.basename( filename )
    error    = "%s: %s" % ( excType.__name__, excValue )
    stackTraceString = "".join( traceback.format_exception( excType, excValue,
                                                            tracebackObj ) )

    # Write a message to a log file
    logging.error( "Unhandled exception is caught\n" + stackTraceString )

    # Display the message as a QT modal dialog box if the application
    # has started
    if not globalData.application is None:
        QtGui.QMessageBox.critical( None, "Error: " + error,
                                    "<html>Unhandled exception is caught." \
                                    "<pre>" + stackTraceString + "</pre>" \
                                    "</html>" )
        globalData.application.exit( 1 )
    return


if __name__ == '__main__':
    retCode = codimensionMain()

    # restore root logging handlers
    if len( __rootLoggingHandlers ) != 0:
        logging.root.handlers = __rootLoggingHandlers

    logging.debug( "Exiting codimension" )
    sys.exit( retCode )

