#
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


""" codimension project """

import os, os.path, ConfigParser, logging, uuid, re
import rope.base.project
from briefmodinfocache import BriefModuleInfoCache
from runparamscache    import RunParametersCache
from PyQt4.QtCore      import QObject, SIGNAL
from settings          import Settings, ropePreferences, settingsDir
from watcher           import Watcher


class CodimensionProject( QObject ):
    " Provides codimension project singleton facility "

    # Constants for the projectChanged signal
    CompleteProject = 0     # It is a completely new project
    Properties      = 1     # Project properties were updated

    def __init__( self ):
        QObject.__init__( self )

        self.__dirWatcher = None
        self.__formatOK = True

        # Avoid pylint complains
        self.fileName = ""
        self.userProjectDir = ""    # Directory in ~/.codimension/uuidNN/
        self.filesList = set()

        self.scriptName = ""        # Script to run the project
        self.creationDate = ""
        self.author = ""
        self.license = ""
        self.copyright = ""
        self.version = ""
        self.email = ""
        self.description = ""
        self.uuid = ""

        self.ropeProject = None

        # Coming from separate files from ~/.codimension/uuidN/
        self.todos = []
        self.bookmarks = []
        self.briefModinfoCache = BriefModuleInfoCache()
        self.runParamsCache = RunParametersCache()
        self.topLevelDirs = []
        self.findHistory = []
        self.findNameHistory = []
        self.findFileHistory = []
        self.replaceHistory = []
        self.tabsStatus = []

        self.findFilesWhat = []
        self.findFilesDirs = []
        self.findFilesMasks = []

        self.findClassHistory = []
        self.findFuncHistory = []
        self.findGlobalHistory = []

        self.recentFiles = []
        self.importDirs = []

        # Precompile the exclude filters
        self.__excludeFilter = []
        for flt in Settings().projectFilesFilters:
            self.__excludeFilter.append( re.compile( flt ) )

        return

    def shouldExclude( self, name ):
        " Tests if a file must be excluded "
        for excl in self.__excludeFilter:
            if excl.match( name ):
                return True
        return False

    def __resetValues( self ):
        """ Initializes or resets all the project members """

        # Empty file name means that the project has not been loaded or
        # created. This must be an absolute path.
        self.fileName = ""
        self.userProjectDir = ""

        # Generated having the project dir Full paths are stored.
        # The set holds all files and directories. The dirs end with os.path.sep
        self.filesList = set()

        self.scriptName = ""
        self.creationDate = ""
        self.author = ""
        self.license = ""
        self.copyright = ""
        self.version = ""
        self.email = ""
        self.description = ""
        self.uuid = ""

        # Coming from separate files from ~/.codimension/uuidN/
        self.todos = []
        self.bookmarks = []
        self.briefModinfoCache = BriefModuleInfoCache()
        self.runParamsCache = RunParametersCache()
        self.topLevelDirs = []
        self.findHistory = []
        self.findNameHistory = []
        self.findFileHistory = []
        self.replaceHistory = []
        self.tabsStatus = []

        self.findFilesWhat = []
        self.findFilesDirs = []
        self.findFilesMasks = []

        self.findClassHistory = []
        self.findFuncHistory = []
        self.findGlobalHistory = []

        self.recentFiles = []
        self.importDirs = []

        # Reset the dir watchers if so
        if self.__dirWatcher is not None:
            del self.__dirWatcher
        self.__dirWatcher = None
        return

    def createNew( self, fileName, scriptName, importDirs, author, lic,
                   copyRight, description, creationDate, version, email ):
        " Creates a new project "

        # Try to create the user project directory
        projectUuid = str( uuid.uuid1() )
        userProjectDir = settingsDir + projectUuid + os.path.sep
        if not os.path.exists( userProjectDir ):
            try:
                os.mkdir( userProjectDir )
            except:
                logging.error( "Cannot create user project directory: " + \
                               self.userProjectDir + ". Please check the " \
                               "available disk space and re-create the " \
                               "project." )
                raise
        else:
            logging.warning( "The user project directory existed! " \
                             "The content will be overwritten." )
            self.__removeProjectFiles( userProjectDir )

        # Basic pre-requisites are met. We can reset the current project
        self.__resetValues()

        self.fileName = str( fileName )
        self.importDirs = importDirs
        self.scriptName = scriptName
        self.creationDate = creationDate
        self.author = author
        self.license = lic
        self.copyright = copyRight
        self.version = version
        self.email = email
        self.description = description
        self.uuid = projectUuid
        self.userProjectDir = userProjectDir

        self.__createProjectFile()  # ~/.codimension/uuidNN/project

        self.__generateFilesList()
        self.__updateModinfoCache()

        self.saveProject()

        # Update the watcher
        self.__dirWatcher = Watcher( Settings().projectFilesFilters,
                                     self.getProjectDir() )
        self.connect( self.__dirWatcher, SIGNAL( 'fsCahanged' ),
                      self.onFSChanged )

        self.__createRopeProject()
        self.emit( SIGNAL( 'projectChanged' ), self.CompleteProject )
        return

    @staticmethod
    def __safeRemove( path ):
        " Safe file removal "
        try:
            os.remove( path )
        except:
            return

    def __removeProjectFiles( self, userProjectDir ):
        " Removes user project files "

        self.__safeRemove( userProjectDir + "project" )
        self.__safeRemove( userProjectDir + "bookmarks" )
        self.__safeRemove( userProjectDir + "todos" )
        self.__safeRemove( userProjectDir + "briefinfocache" )
        self.__safeRemove( userProjectDir + "searchhistory" )
        self.__safeRemove( userProjectDir + "topleveldirs" )
        self.__safeRemove( userProjectDir + "tabsstatus" )
        self.__safeRemove( userProjectDir + "findinfiles" )
        self.__safeRemove( userProjectDir + "recentfiles" )
        return

    def __createProjectFile( self ):
        " Helper function to create the user project file "
        try:
            f = open( self.userProjectDir + "project", "w" )
            f.write( self.fileName )
            f.close()
        except:
            return

    def __updateModinfoCache( self ):
        " Helper to hit each cache item "
        for item in self.filesList:
            if item.endswith( '.py' ) or item.endswith( '.py3' ):
                self.briefModinfoCache.get( item )
        return

    def saveProject( self ):
        " Writes all the settings into the file "
        if not self.isLoaded():
            return

        # Project properties part
        propertiesPart = "[properties]\n" \
                         "scriptname=" + self.scriptName + "\n" \
                         "creationdate=" + self.creationDate + "\n" \
                         "author=" + self.author + "\n" \
                         "license=" + self.license + "\n" \
                         "copyright=" + self.copyright + "\n" \
                         "description=" + \
                            self.description.replace( '\n', '<CR><LF>' ) + \
                            "\n" \
                         "version=" + self.version + "\n" \
                         "email=" + self.email + "\n" \
                         "uuid=" + self.uuid + "\n"

        f = open( self.fileName, "w" )
        self.__writeHeader( f )
        self.__writeList( f, "importdirs", "dir", self.importDirs )
        f.write( propertiesPart + "\n" + \
                 "\n\n" )
        f.close()

        # Save brief cache
        self.briefModinfoCache.serialize( self.userProjectDir + \
                                          "briefinfocache" )
        self.serializeRunParameters()
        self.__saveTopLevelDirs()
        self.__saveSearchHistory()
        self.__saveTabsStatus()
        self.__saveFindFiles()
        self.__saveFindObjects()
        self.__saveRecentFiles()

        self.__formatOK = True
        return

    def serializeRunParameters( self ):
        " Saves the run parameters cache "
        self.runParamsCache.serialize( self.userProjectDir + "runparamscache" )
        return

    def __saveTabsStatus( self ):
        " Helper to save tabs status "
        if self.isLoaded():
            f = open( self.userProjectDir + "tabsstatus", "w" )
            self.__writeHeader( f )
            self.__writeList( f, "tabsstatus", "tab", self.tabsStatus )
            f.close()
        return

    def __saveSearchHistory( self ):
        " Helper to save the project search history "
        if self.isLoaded():
            f = open( self.userProjectDir + "searchhistory", "w" )
            self.__writeHeader( f )
            self.__writeList( f, "findhistory", "find",
                              self.findHistory )
            self.__writeList( f, "replacehistory", "replace",
                              self.replaceHistory )
            self.__writeList( f, "findnamehistory", "find",
                              self.findNameHistory )
            self.__writeList( f, "findfilehistory", "find",
                              self.findFileHistory )
            f.close()
        return

    def __saveTopLevelDirs( self ):
        " Helper to save the project top level dirs "
        if self.isLoaded():
            f = open( self.userProjectDir + "topleveldirs", "w" )
            self.__writeHeader( f )
            self.__writeList( f, "topleveldirs", "dir", self.topLevelDirs )
            f.close()
        return

    def __saveFindFiles( self ):
        " Helper to save the find in files history "
        if self.isLoaded():
            f = open( self.userProjectDir + "findinfiles", "w" )
            self.__writeHeader( f )
            self.__writeList( f, "whathistory", "what", self.findFilesWhat )
            self.__writeList( f, "dirhistory", "dir", self.findFilesDirs )
            self.__writeList( f, "maskhistory", "mask", self.findFilesMasks )
            f.close()
        return

    def __saveFindObjects( self ):
        " Helper to save find objects history "
        if self.isLoaded():
            f = open( self.userProjectDir + "findobjects", "w" )
            self.__writeHeader( f )
            self.__writeList( f, "classhistory", "class",
                              self.findClassHistory )
            self.__writeList( f, "funchistory", "func",
                              self.findFuncHistory )
            self.__writeList( f, "globalhistory", "global",
                              self.findGlobalHistory )
            f.close()
        return

    def __saveRecentFiles( self ):
        " Helper to save recent files list "
        if self.isLoaded():
            f = open( self.userProjectDir + "recentfiles", "w" )
            self.__writeHeader( f )
            self.__writeList( f, "recentfiles", "file", self.recentFiles )
            f.close()
        return

    @staticmethod
    def __writeHeader( fileObj ):
        " Helper to write a header with a warning "
        fileObj.write( "#\n" \
                       "# Generated automatically.\n" \
                       "# Don't edit it manually unless you " \
                       "know what you are doing.\n" \
                       "#\n\n" )
        return

    @staticmethod
    def __writeList( fileObj, header, prefix, items ):
        " Helper to write a list "
        fileObj.write( "[" + header + "]\n" )
        index = 0
        for item in items:
            fileObj.write( prefix + str( index ) + "=" + item + "\n" )
            index += 1
        fileObj.write( "\n" )
        return

    def __getStr( self, conf, sec, key, default ):
        " Helper to read a config value "
        try:
            return conf.get( sec, key ).strip()
        except:
            self.__formatOK = False
        return default

    def loadProject( self, projectFile ):
        """ Loads a project from the given file """

        absPath = os.path.abspath( projectFile )
        if not os.path.exists( absPath ):
            raise Exception( "Cannot open project file " + projectFile )
        if not absPath.endswith( ".cdm" ):
            raise Exception( "Unexpected project file extension. " \
                             "Expected: .cdm" )

        config = ConfigParser.ConfigParser()

        try:
            config.read( absPath )
        except:
            # Bad error - cannot load project file at all
            config = None
            raise Exception( "Bad project file" )


        self.__resetValues()
        self.fileName = str( absPath )

        # Properties part
        self.scriptName = self.__getStr( config, 'properties',
                                                 'scriptname', '' )
        self.creationDate = self.__getStr( config, 'properties',
                                                   'creationdate', '' )
        self.author = self.__getStr( config, 'properties', 'author', '' )
        self.license = self.__getStr( config, 'properties', 'license', '' )
        self.copyright = self.__getStr( config, 'properties', 'copyright', '' )
        self.description = self.__getStr( config, 'properties', 'description',
                                          '' ).replace( '<CR><LF>', '\n' )
        self.version = self.__getStr( config, 'properties', 'version', '' )
        self.email = self.__getStr( config, 'properties', 'email', '' )
        self.uuid = self.__getStr( config, 'properties', 'uuid', '' )
        if self.uuid == "":
            logging.warning( "Project file does not have UUID. " \
                             "Re-generate it..." )
            self.uuid = str( uuid.uuid1() )
        self.userProjectDir = settingsDir + self.uuid + os.path.sep
        if not os.path.exists( self.userProjectDir ):
            os.mkdir( self.userProjectDir )

        # import dirs part
        index = 0
        try:
            while True:
                dirName = config.get( 'importdirs',
                                      'dir' + str( index ) ).strip()
                index += 1
                if os.path.isabs( dirName ):
                    absPath = dirName
                else:
                    absPath = self.getProjectDir() + dirName
                if not os.path.exists( absPath ):
                    logging.error( "Codimension project: cannot find " \
                                   "import directory: " + dirName )
                elif not os.path.isdir( absPath ):
                    logging.error( "Codimension project: the import path: " + \
                                   dirName + " is not a directory" )
                self.importDirs.append( dirName )
        except ConfigParser.NoSectionError:
            self.__formatOK = False
        except ConfigParser.NoOptionError:
            # just continue
            pass
        except:
            self.__formatOK = False

        config = None

        # Read the other config files
        self.__loadTopLevelDirs()
        self.__loadSearchHistory()
        self.__loadTabsStatus()
        self.__loadFindFiles()
        self.__loadFindObjects()
        self.__loadRecentFiles()

        # The project might have been moved...
        self.__createProjectFile()  # ~/.codimension/uuidNN/project
        self.__generateFilesList()

        if os.path.exists( self.userProjectDir + "briefinfocache" ):
            self.briefModinfoCache.deserialize( self.userProjectDir + \
                                                "briefinfocache" )
        if os.path.exists( self.userProjectDir + "runparamscache" ):
            self.runParamsCache.deserialize( self.userProjectDir + \
                                             "runparamscache" )

        # Get each file info as it could be out of date
        self.__updateModinfoCache()

        if not self.__formatOK:
            logging.info( "Project files are broken or absent. " \
                          "Overwriting the project files." )
            self.saveProject()

        # Update the recent list
        Settings().addRecentProject( self.fileName )

        # Setup the new watcher
        self.__dirWatcher = Watcher( Settings().projectFilesFilters,
                                     self.getProjectDir() )
        self.connect( self.__dirWatcher, SIGNAL( 'fsCahanged' ),
                      self.onFSChanged )

        self.__createRopeProject()
        self.emit( SIGNAL( 'projectChanged' ), self.CompleteProject )
        return

    def __createRopeProject( self ):
        " Creates a rope library project "
        if self.ropeProject is not None:
            self.ropeProject.close()
            self.ropeProject = None

        # Rope folder is default here, so it will be created
        self.ropeProject = rope.base.project.Project( \
                                            self.getProjectDir(),
                                            **ropePreferences )
        self.ropeProject.validate( self.ropeProject.root )
        return

    def onFSChanged( self, items ):
        " Triggered when the watcher detects changes "
##        report = "REPORT: "
##        projectItems = []
        for item in items:
            item = str( item )

#            if not os.path.islink( item ):
#                realPath = os.path.realpath( item[ 1: ] )
#                isDir = item.endswith( os.path.sep )
#                if isDir:
#                    if self.isProjectDir( realPath + os.path.sep ):
#                        item = item[ 0 ] + realPath + os.path.sep
#                else:
#                    if self.isProjectFile( realPath + os.path.sep ):
#                        item = item[ 0 ] + realPath

#            projectItems.append( item )
##            report += " " + item
            try:
                if item.startswith( '+' ):
                    self.filesList.update( [ item[ 1: ] ] )
                else:
                    self.filesList.remove( item[ 1: ] )
##                projectItems.append( item )
            except:
#                print "EXCEPTION for '" + item + "'"
                pass
#        print "'" + report + "'"

        self.emit( SIGNAL( 'fsChanged' ), items )
#        self.__dirWatcher.debug()
        return

    def __loadTabsStatus( self ):
        " Loads the last tabs status "
        configFile = self.userProjectDir + "tabsstatus"
        if not os.path.exists( configFile ):
            logging.info( "Cannot find tabsstatus project file. " \
                          "Expected here: " + configFile )
            self.__formatOK = False
            return

        config = ConfigParser.ConfigParser()
        try:
            config.read( configFile )
        except:
            # Bad error - cannot load project file at all
            config = None
            self.__formatOK = False
            logging.warning( "Cannot read tabsstatus project file " \
                             "from here: " + configFile )
            return

        # tabs part
        self.tabsStatus = self.__loadListSection( \
                config, 'tabsstatus', 'tab' )

        config = None
        return

    def __loadTopLevelDirs( self ):
        " Loads the top level dirs "
        configFile = self.userProjectDir + "topleveldirs"
        if not os.path.exists( configFile ):
            logging.info( "Cannot find topleveldirs project file. " \
                          "Expected here: " + configFile )
            self.__formatOK = False
            return

        config = ConfigParser.ConfigParser()
        try:
            config.read( configFile )
        except:
            # Bad error - cannot load project file at all
            config = None
            self.__formatOK = False
            logging.warning( "Cannot read topleveldirs project file " \
                             "from here: " + configFile )
            return

        # dirs part
        self.topLevelDirs = self.__loadListSection( \
                config, 'topleveldirs', 'dir' )

        config = None
        return

    def __loadSearchHistory( self ):
        " Loads the search history file content "
        confFile = self.userProjectDir + "searchhistory"
        if not os.path.exists( confFile ):
            logging.info( "Cannot find searchhistory project file. " \
                          "Expected here: " + confFile )
            self.__formatOK = False
            return

        config = ConfigParser.ConfigParser()
        try:
            config.read( confFile )
        except:
            # Bad error - cannot load project file at all
            config = None
            self.__formatOK = False
            logging.warning( "Cannot read searchhistory project file " \
                             "from here: " + confFile )
            return

        # find part
        self.findHistory = self.__loadListSection( \
                config, 'findhistory', 'find' )
        self.findNameHistory = self.__loadListSection( \
                config, 'findnamehistory', 'find' )
        self.findFileHistory = self.__loadListSection( \
                config, 'findfilehistory', 'find' )

        # replace part
        self.replaceHistory = self.__loadListSection( \
                config, 'replacehistory', 'replace' )

        config = None
        return

    def __loadFindObjects( self ):
        " Loads the find objects history "
        confFile = self.userProjectDir + "findobjects"
        if not os.path.exists( confFile ):
            logging.info( "Cannot find findobjects project file. " \
                          "Expected here: " + confFile )
            self.__formatOK = False
            return

        config = ConfigParser.ConfigParser()
        try:
            config.read( confFile )
        except:
            # Bad error - cannot load project file at all
            config = None
            self.__formatOK = False
            logging.warning( "Cannot read findobjects project file " \
                             "from here: " + confFile )
            return

        self.findClassHistory = self.__loadListSection( \
                config, 'classhistory', 'class' )
        self.findFuncHistory = self.__loadListSection( \
                config, 'funchistory', 'func' )
        self.findGlobalHistory = self.__loadListSection( \
                config, 'globalhistory', 'global' )
        config = None
        return

    def __loadFindFiles( self ):
        " Loads the find in files history "
        confFile = self.userProjectDir + "findinfiles"
        if not os.path.exists( confFile ):
            logging.info( "Cannot find findinfiles project file. " \
                          "Expected here: " + confFile )
            self.__formatOK = False
            return

        config = ConfigParser.ConfigParser()
        try:
            config.read( confFile )
        except:
            # Bad error - cannot load project file at all
            config = None
            self.__formatOK = False
            logging.warning( "Cannot read findinfiles project file " \
                             "from here: " + confFile )
            return

        self.findFilesWhat = self.__loadListSection( \
                config, 'whathistory', 'what' )
        self.findFilesDirs = self.__loadListSection( \
                config, 'dirhistory', 'dir' )
        self.findFilesMasks = self.__loadListSection( \
                config, 'maskhistory', 'mask' )
        config = None
        return

    def __loadRecentFiles( self ):
        " Loads the recent files list "
        confFile = self.userProjectDir + "recentfiles"
        if not os.path.exists( confFile ):
            logging.info( "Cannot find recentfiles project file. " \
                          "Expected here: " + confFile )
            self.__formatOK = False
            return

        config = ConfigParser.ConfigParser()
        try:
            config.read( confFile )
        except:
            # Bad error - cannot load project file at all
            config = None
            self.__formatOK = False
            logging.warning( "Cannot read recentfiles project file " \
                             "from here: " + confFile )
            return

        self.recentFiles = self.__loadListSection( \
                config, 'recentfiles', 'file' )
        config = None
        return

    def __loadListSection( self, config, section, listPrefix ):
        " Loads a list off the given section from the given file "
        items = []
        index = 0
        try:
            while True:
                item = config.get( section, listPrefix + str(index) ).strip()
                index += 1
                items.append( item )
        except ConfigParser.NoSectionError:
            self.__formatOK = False
        except ConfigParser.NoOptionError:
            pass    # Just continue
        except:
            self.__formatOK = False
        return items

    def unloadProject( self ):
        """ Unloads the current project if required """
        self.__resetValues()
        self.emit( SIGNAL( 'projectChanged' ), self.CompleteProject )
        self.ropeProject.close()
        self.ropeProject = None
        return

    def setImportDirs( self, paths ):
        " Sets a new set of the project import dirs "
        if self.importDirs != paths:
            self.importDirs = paths
            self.saveProject()
            self.emit( SIGNAL( 'projectChanged' ), self.Properties )
        return

    def __generateFilesList( self ):
        """ Generates the files list having the list of dirs """
        self.filesList = set()
        path = self.getProjectDir()
        self.filesList.update( [ path ] )
        self.__scanDir( path )
        return

    def __scanDir( self, path ):
        """ Recursive function to scan one dir """
        # The path is with '/' at the end
        for item in os.listdir( path ):
            if self.shouldExclude( item ):
                continue

            # Exclude symlinks if they point to the other project
            # covered pieces
            if os.path.islink( path + item ):
                realItem = os.path.realpath( path + item )
                if os.path.isdir( realItem ):
                    if self.isProjectDir( realItem ):
                        continue
                else:
                    if self.isProjectDir( os.path.dirname( realItem ) ):
                        continue

            if os.path.isdir( path + item ):
                self.filesList.update( [ path + item + os.path.sep ] )
                self.__scanDir( path + item + os.path.sep )
                continue
            self.filesList.update( [ path + item ] )
        return

    def isProjectDir( self, path ):
        " Returns True if the path belongs to the project "
        if not self.isLoaded():
            return False
        path = os.path.realpath( str( path ) )     # it could be a symlink
        if not path.endswith( os.path.sep ):
            path += os.path.sep
        return path.startswith( self.getProjectDir() )

    def isProjectFile( self, path ):
        " Returns True if the path belongs to the project "
        if not self.isLoaded():
            return False
        return self.isProjectDir( os.path.dirname( path ) )

    def isTopLevelDir( self, path ):
        " Checks if the path is a top level dir "
        if not path.endswith( os.path.sep ):
            path += os.path.sep
        return path in self.topLevelDirs

    def addTopLevelDir( self, path ):
        " Adds the path to the top level dirs list "
        if not path.endswith( os.path.sep ):
            path += os.path.sep
        if path in self.topLevelDirs:
            logging.warning( "Top level dir " + path + \
                             " is already in the list of dirs. " \
                             "Ignore adding..." )
            return
        self.topLevelDirs.append( path )
        self.__saveTopLevelDirs()
        return

    def removeTopLevelDir( self, path ):
        " Removes the path from the top level dirs list "
        if not path.endswith( os.path.sep ):
            path += os.path.sep
        if path not in self.topLevelDirs:
            logging.warning( "Top level dir " + path + \
                             " is not in the list of dirs. Ignore removing..." )
            return
        self.topLevelDirs.remove( path )
        self.__saveTopLevelDirs()
        return

    def setFindNameHistory( self, history ):
        " Sets the new find name history and saves it into a file "
        self.findNameHistory = history
        self.__saveSearchHistory()
        return

    def setFindFileHistory( self, history ):
        " Sets the new find file history and saves it into a file "
        self.findFileHistory = history
        self.__saveSearchHistory()
        return

    def setFindHistory( self, history ):
        " Sets the new find history and save it into a file "
        self.findHistory = history
        self.__saveSearchHistory()
        return

    def setReplaceHistory( self, whatHistory, toHistory ):
        " Sets the new replace history and save it into a file "
        self.findHistory = whatHistory
        self.replaceHistory = toHistory
        self.__saveSearchHistory()
        return

    def setTabsStatus( self, status ):
        " Sets the new tabs status and save it into a file "
        self.tabsStatus = status
        self.__saveTabsStatus()
        return

    def setFindInFilesHistory( self, what, dirs, masks ):
        " Sets the new lists and save them into a file "
        self.findFilesWhat = what
        self.findFilesDirs = dirs
        self.findFilesMasks = masks
        self.__saveFindFiles()
        return

    def setFindClassHistory( self, history ):
        " Sets the new history and saves it into a file "
        self.findClassHistory = history
        self.__saveFindObjects()
        return

    def setFindFuncHistory( self, history ):
        " Sets the new history and saves it into a file "
        self.findFuncHistory = history
        self.__saveFindObjects()
        return

    def setFindGlobalHistory( self, history ):
        " Sets the new history and saves it into a file "
        self.findGlobalHistory = history
        self.__saveFindObjects()
        return

    def updateProperties( self, scriptName, importDirs, creationDate, author,
                          lic, copy_right, version,
                          email, description ):
        " Updates the project properties "

        if self.scriptName == scriptName and \
           self.creationDate == creationDate and \
           self.author == author and \
           self.license == lic and \
           self.copyright == copy_right and \
           self.version == version and \
           self.email == email and \
           self.description == description and \
           self.importDirs == importDirs:
            # No real changes
            return

        self.importDirs = importDirs
        self.scriptName = scriptName
        self.creationDate = creationDate
        self.author = author
        self.license = lic
        self.copyright = copy_right
        self.version = version
        self.email = email
        self.description = description
        self.saveProject()
        self.emit( SIGNAL( 'projectChanged' ), self.Properties )
        return

    def onProjectFileUpdated( self ):
        " Called when a project file is updated via direct editing "

        scriptName, importDirs, \
        creationDate, author, \
        lic, copy_right, \
        description, version, \
        email, projectUuid = getProjectProperties( self.fileName )

        self.importDirs = importDirs
        self.scriptName = scriptName
        self.creationDate = creationDate
        self.author = author
        self.license = lic
        self.copyright = copy_right
        self.version = version
        self.email = email
        self.description = description

        # no need to save, but signal just in case
        self.emit( SIGNAL( 'projectChanged' ), self.Properties )
        return

    def isLoaded( self ):
        " returns True if a project is loaded "
        return self.fileName != ""

    def getProjectDir( self ):
        " Provides an absolute path to the project dir "
        if not self.isLoaded():
            return ""
        return os.path.dirname( os.path.realpath( self.fileName ) ) + \
               os.path.sep

    def getProjectScript( self ):
        " Provides the project script file name "
        if not self.isLoaded():
            return ""
        if self.scriptName == "":
            return ""
        if os.path.isabs( self.scriptName ):
            return self.scriptName
        return os.path.normpath( self.getProjectDir() + self.scriptName )

    def addRecentFile( self, path ):
        " Adds a single recent file. True if a new file was inserted. "
        if path in self.recentFiles:
            self.recentFiles.remove( path )
            self.recentFiles.insert( 0, path )
            self.__saveRecentFiles()
            return False
        self.recentFiles.insert( 0, path )
        self.__saveRecentFiles()
        if len( self.recentFiles ) > 32:
            self.recentFiles = self.recentFiles[ -32 : ]
        self.emit( SIGNAL( 'recentFilesChanged' ) )
        return True

    def removeRecentFile( self, path ):
        " Removes a single recent file "
        if path in self.recentFiles:
            self.recentFiles.remove( path )
            self.__saveRecentFiles()
        return


def getProjectProperties( projectFile ):
    """ Provides project properties or throws an exception """

    def readValue( conf, sec, key ):
        " Helper function for try block "
        try:
            return conf.get( sec, key ).strip()
        except:
            return ""

    absPath = os.path.abspath( projectFile )
    if not os.path.exists( absPath ):
        raise Exception( "Cannot find project file " + projectFile )

    config = ConfigParser.ConfigParser()
    config.read( absPath )

    # We are interested in properties only
    importDirs = []
    index = 0
    try:
        while True:
            importDirs.append( config.get( "importdirs",
                                           "dir" + str( index ) ).strip() )
            index += 1
    except:
        pass

    scriptName = readValue( config, 'properties', 'scriptname' )
    creationDate = readValue( config, 'properties', 'creationdate' )
    author = readValue( config, 'properties', 'author' )
    lic = readValue( config, 'properties', 'license' )
    copy_right = readValue( config, 'properties', 'copyright' )
    description = readValue( config, 'properties',
                             'description' ).replace( '<CR><LF>', '\n' )
    version = readValue( config, 'properties', 'version' )
    email = readValue( config, 'properties', 'email' )
    projectUuid = readValue( config, 'properties', 'uuid' )

    config = None

    return scriptName, importDirs, creationDate, author, lic, copy_right, \
           description, version, email, projectUuid


def getProjectFileTooltip( fileName ):
    " Provides a project file tooltip "
    scriptName, importDirs, creationDate, author, lic, \
    copy_right, description, \
    version, email, uuid = getProjectProperties( fileName )

    return "Version: " + version + "\n" \
           "Description: " + description + "\n" \
           "Author: " + author + "\n" \
           "e-mail: " + email + "\n" \
           "Copyright: " + copy_right + "\n" \
           "License: " + lic + "\n" \
           "Creation date: " + creationDate + "\n" \
           "UUID: " + uuid
