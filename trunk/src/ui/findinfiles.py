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


""" find in files dialog """


import os, os.path, re, time, logging
from PyQt4.QtCore                import Qt, SIGNAL
from PyQt4.QtGui                 import QDialog, QDialogButtonBox, \
                                        QVBoxLayout, QSizePolicy, QLabel, \
                                        QProgressBar, QApplication, \
                                        QComboBox, QGridLayout, QHBoxLayout, \
                                        QCheckBox, QRadioButton, QGroupBox, \
                                        QPushButton, QFileDialog, QCursor
from fitlabel                    import FitPathLabel
from utils.globals               import GlobalData
from utils.settings              import Settings
from utils.fileutils             import detectFileType, PixmapFileType, \
                                        PythonCompiledFileType, ELFFileType, \
                                        SOFileType, PDFFileType, \
                                        BrokenSymlinkFileType
from mainwindowtabwidgetbase     import MainWindowTabWidgetBase
from cdmbriefparser              import getBriefModuleInfoFromMemory



class Match:
    " Stores info about one match in a file "

    def __init__( self, line, start, finish ):
        self.line = line        # Matched line
        self.start = start      # Match start pos
        self.finish = finish    # Match end pos
        self.tooltip = "not implemented"
        self.text = ""
        return

class ItemToSearchIn:
    " Stores information about one item to search in "

    contextLines = 15

    def __init__( self, fname, bufferID ):
        self.fileName = fname       # Could be absolute -> for existing files
                                    # or relative -> for newly created
        self.bufferUUID = bufferID  # Non empty for currently opened files
        self.tooltip = ""           # For python files only -> docstring
        self.matches = []
        return

    def search( self, expression ):
        " Perform search within this item "

        self.matches = []
        if self.bufferUUID != "":
            # Search item is the currently loaded buffer
            mainWindow = GlobalData().mainWindow
            widget = mainWindow.getWidgetByUUID( self.bufferUUID )
            if widget is not None:
                # Search in the buffer

                content = str( widget.getEditor().text() ).splitlines()
                self.__lookThroughLines( content, expression )
                return

        # Here: there were no buffer or have not found it
        #       try searching in a file
        if not os.path.isabs( self.fileName ) or \
           not os.path.exists( self.fileName ):
            raise Exception( "Neither buffer nor file exists." )

        # File exists, search in the file
        try:
            f = open( self.fileName )
            content = f.read().split( "\n" )
            f.close()
            self.__lookThroughLines( content, expression )
        except:
            logging.error( "Cannot read " + self.fileName )
        return

    def __lookThroughLines( self, content, expression ):
        " Searches through all the given lines "
        lineIndex = 0
        totalLines = len( content )
        while lineIndex < totalLines:
            line = content[ lineIndex ]
            contains = expression.search( line )
            if contains:
                match = Match( lineIndex + 1, contains.start(), contains.end() )
                match.text = line.strip()
                start, end = self.__calculateContextStart( lineIndex,
                                                           totalLines )
                lines = content[ start : end ]
                matchedLineIndex = lineIndex - start
                lines[ matchedLineIndex ] = \
                        lines[ matchedLineIndex ][ :match.start ] + \
                        "<b>" + \
                        lines[ matchedLineIndex ][ match.start:match.finish ] + \
                        "</b>" + \
                        lines[ matchedLineIndex ][ match.finish: ]

                match.tooltip = "<pre>" + "\n".join( lines ) + "</pre>"
                self.matches.append( match )
                if len( self.matches ) > 1024:
                    # Too much entries, stop here
                    logging.warning( "More than 1024 matches in " + \
                                     self.fileName + \
                                     ". Stop further search in this file." )
                    break
            lineIndex += 1

        # Extract docsting if applicable
        if len( self.matches ) > 0:
            if self.fileName.endswith( '.py' ) or \
               self.fileName.endswith( '.py3' ):
                info = getBriefModuleInfoFromMemory( "\n".join( content ) )
                self.tooltip = ""
                if info.docstring is not None:
                    self.tooltip = info.docstring.text

        return

    @staticmethod
    def __calculateContextStart( matchedLine, totalLines ):
        """ Calculates the start line number for the context tooltip """
        # matchedLine is a zero based index
        if ItemToSearchIn.contextLines >= totalLines:
            return 0, totalLines - 1

        start = matchedLine - int( ItemToSearchIn.contextLines / 2 )
        if start < 0:
            start = 0
        end = start + ItemToSearchIn.contextLines
        if end < totalLines:
            return start, end
        return totalLines - ItemToSearchIn.contextLines, totalLines - 1



class FindInFilesDialog( QDialog, object ):
    """ find in files dialog implementation """

    inProject = 0
    inDirectory = 1
    inOpenFiles = 2

    def __init__( self, where, what = "",
                  dirPath = "", filters = [],
                  parent = None ):

        QDialog.__init__( self, parent )

        mainWindow = GlobalData().mainWindow
        self.editorsManager = mainWindow.editorsManagerWidget.editorsManager

        self.__cancelRequest = False
        self.__inProgress = False
        self.searchRegexp = None
        self.searchResults = []

        # Avoid pylint complains
        self.findCombo = None
        self.caseCheckBox = None
        self.wordCheckBox = None
        self.regexpCheckBox = None
        self.projectRButton = None
        self.openFilesRButton = None
        self.dirRButton = None
        self.dirEditCombo = None
        self.dirSelectButton = None
        self.filterCombo = None
        self.fileLabel = None
        self.progressBar = None
        self.findButton = None

        self.__createLayout()
        self.setWindowTitle( "Find in files" )

        # Restore the combo box values
        project = GlobalData().project
        if project.fileName != "":
            self.findFilesWhat = project.findFilesWhat
            self.findFilesDirs = project.findFilesDirs
            self.findFilesMasks = project.findFilesMasks
        else:
            settings = Settings()
            self.findFilesWhat = settings.findFilesWhat
            self.findFilesDirs = settings.findFilesDirs
            self.findFilesMasks = settings.findFilesMasks
        self.findCombo.addItems( self.findFilesWhat )
        self.findCombo.setEditText( "" )
        self.dirEditCombo.addItems( self.findFilesDirs )
        self.dirEditCombo.setEditText( "" )
        self.filterCombo.addItems( self.findFilesMasks )
        self.filterCombo.setEditText( "" )

        if where == self.inProject:
            self.setSearchInProject( what, filters )
        elif where == self.inDirectory:
            self.setSearchInDirectory( what, dirPath, filters )
        else:
            self.setSearchInOpenFiles( what, filters )

        return

    def __createLayout( self ):
        """ Creates the dialog layout """

        self.resize( 600, 300 )
        self.setSizeGripEnabled( True )

        verticalLayout = QVBoxLayout( self )
        gridLayout = QGridLayout()

        # Combo box for the text to search
        findLabel = QLabel( self )
        findLabel.setText( "Find text:" )
        self.findCombo = QComboBox( self )
        self.__tuneCombo( self.findCombo )
        self.findCombo.lineEdit().setToolTip( "Regular expression to search for" )
        self.connect( self.findCombo,
                      SIGNAL( 'editTextChanged(const QString &)' ),
                      self.__someTextChanged )

        gridLayout.addWidget( findLabel, 0, 0, 1, 1 )
        gridLayout.addWidget( self.findCombo, 0, 1, 1, 1 )
        verticalLayout.addLayout( gridLayout )

        # Check boxes
        horizontalCBLayout = QHBoxLayout()
        self.caseCheckBox = QCheckBox( self )
        self.caseCheckBox.setText( "Match &case" )
        horizontalCBLayout.addWidget( self.caseCheckBox )
        self.wordCheckBox = QCheckBox( self )
        self.wordCheckBox.setText( "Match whole &word" )
        horizontalCBLayout.addWidget( self.wordCheckBox )
        self.regexpCheckBox = QCheckBox( self )
        self.regexpCheckBox.setText( "Regular &expression" )
        horizontalCBLayout.addWidget( self.regexpCheckBox )

        verticalLayout.addLayout( horizontalCBLayout )

        # Files groupbox
        filesGroupbox = QGroupBox( self )
        filesGroupbox.setTitle( "Find in" )
        sizePolicy = QSizePolicy( QSizePolicy.Expanding, QSizePolicy.Preferred )
        sizePolicy.setHorizontalStretch( 0 )
        sizePolicy.setVerticalStretch( 0 )
        sizePolicy.setHeightForWidth( \
                        filesGroupbox.sizePolicy().hasHeightForWidth() )
        filesGroupbox.setSizePolicy( sizePolicy )

        gridLayoutFG = QGridLayout( filesGroupbox )
        self.projectRButton = QRadioButton( filesGroupbox )
        self.projectRButton.setText( "&Project" )
        gridLayoutFG.addWidget( self.projectRButton, 0, 0 )
        self.connect( self.projectRButton, SIGNAL( 'clicked()' ),
                      self.__projectClicked )

        self.openFilesRButton = QRadioButton( filesGroupbox )
        self.openFilesRButton.setText( "&Opened files only" )
        gridLayoutFG.addWidget( self.openFilesRButton, 1, 0 )
        self.connect( self.openFilesRButton, SIGNAL( 'clicked()' ),
                      self.__openFilesOnlyClicked )

        self.dirRButton = QRadioButton( filesGroupbox )
        self.dirRButton.setText( "&Directory tree" )
        gridLayoutFG.addWidget( self.dirRButton, 2, 0 )
        self.connect( self.dirRButton, SIGNAL( 'clicked()' ),
                      self.__dirClicked )

        self.dirEditCombo = QComboBox( filesGroupbox )
        self.__tuneCombo( self.dirEditCombo )
        self.dirEditCombo.lineEdit().setToolTip( "Directory to search in" )
        gridLayoutFG.addWidget( self.dirEditCombo, 2, 1 )
        self.connect( self.dirEditCombo,
                      SIGNAL( 'editTextChanged(const QString &)' ),
                      self.__someTextChanged )

        self.dirSelectButton = QPushButton( filesGroupbox )
        self.dirSelectButton.setText( "..." )
        gridLayoutFG.addWidget( self.dirSelectButton, 2, 2 )
        self.connect( self.dirSelectButton, SIGNAL( 'clicked()' ),
                      self.__selectDirClicked )

        filterLabel = QLabel( filesGroupbox )
        filterLabel.setText( "Files filter:" )
        gridLayoutFG.addWidget( filterLabel, 3, 0 )
        self.filterCombo = QComboBox( filesGroupbox )
        self.__tuneCombo( self.filterCombo )
        self.filterCombo.lineEdit().setToolTip( "File names regular expression" )
        gridLayoutFG.addWidget( self.filterCombo, 3, 1 )
        self.connect( self.filterCombo,
                      SIGNAL( 'editTextChanged(const QString &)' ),
                      self.__someTextChanged )

        verticalLayout.addWidget( filesGroupbox )

        # File label
        self.fileLabel = FitPathLabel( self )
        verticalLayout.addWidget( self.fileLabel )

        # Progress bar
        self.progressBar = QProgressBar( self )
        self.progressBar.setValue( 0 )
        self.progressBar.setOrientation( Qt.Horizontal )
        verticalLayout.addWidget( self.progressBar )

        # Buttons at the bottom
        buttonBox = QDialogButtonBox( self )
        buttonBox.setOrientation( Qt.Horizontal )
        buttonBox.setStandardButtons( QDialogButtonBox.Cancel )
        self.findButton = buttonBox.addButton( "Find",
                                               QDialogButtonBox.ActionRole )
        self.findButton.setDefault( True )
        self.connect( self.findButton, SIGNAL( 'clicked()' ),
                      self.__process )
        verticalLayout.addWidget( buttonBox )

        self.connect( buttonBox, SIGNAL( "rejected()" ), self.__onClose )
        return

    @staticmethod
    def __tuneCombo( comboBox ):
        " Sets the common settings for a combo box "
        sizePolicy = QSizePolicy( QSizePolicy.Expanding, QSizePolicy.Fixed )
        sizePolicy.setHorizontalStretch( 0 )
        sizePolicy.setVerticalStretch( 0 )
        sizePolicy.setHeightForWidth( \
                            comboBox.sizePolicy().hasHeightForWidth() )
        comboBox.setSizePolicy( sizePolicy )
        comboBox.setEditable( True )
        comboBox.setInsertPolicy( QComboBox.InsertAtTop )
        comboBox.setAutoCompletion( False )
        comboBox.setDuplicatesEnabled( False )
        return


    def __onClose( self ):
        " triggered when the close button is clicked "

        self.__cancelRequest = True
        if not self.__inProgress:
            self.close()
        return

    def setSearchInProject( self, what = "", filters = [] ):
        " Set search ready for the whole project "

        if GlobalData().project.fileName == "":
            # No project loaded, fallback to opened files
            self.setSearchInOpenFiles( what, filters )
            return

        # Select the project radio button
        self.projectRButton.setEnabled( True )
        self.projectRButton.setChecked( True )
        self.dirEditCombo.setEnabled( False )
        self.dirSelectButton.setEnabled( False )

        openedFiles = self.editorsManager.getTextEditors()
        self.openFilesRButton.setEnabled( len( openedFiles ) != 0 )

        self.setFilters( filters )

        self.findCombo.setEditText( what )
        self.findCombo.lineEdit().selectAll()
        self.findCombo.setFocus()

        # Check searchability
        self.__testSearchability()
        return


    def setSearchInOpenFiles( self, what = "", filters = [] ):
        " Sets search ready for the opened files "

        openedFiles = self.editorsManager.getTextEditors()
        if len( openedFiles ) == 0:
            # No opened files, fallback to search in dir
            self.setSearchInDirectory( what, "", filters )
            return

        # Select the radio buttons
        self.projectRButton.setEnabled( GlobalData().project.fileName != "" )
        self.openFilesRButton.setEnabled( True )
        self.openFilesRButton.setChecked( True )
        self.dirEditCombo.setEnabled( False )
        self.dirSelectButton.setEnabled( False )

        self.setFilters( filters )

        self.findCombo.setEditText( what )
        self.findCombo.lineEdit().selectAll()
        self.findCombo.setFocus()

        # Check searchability
        self.__testSearchability()
        return


    def setSearchInDirectory( self, what = "", dirPath = "", filters = [] ):
        " Sets search ready for the given directory "

        # Select radio buttons
        self.projectRButton.setEnabled( GlobalData().project.fileName != "" )
        openedFiles = self.editorsManager.getTextEditors()
        self.openFilesRButton.setEnabled( len( openedFiles ) != 0 )
        self.dirRButton.setEnabled( True )
        self.dirRButton.setChecked( True )
        self.dirEditCombo.setEnabled( True )
        self.dirSelectButton.setEnabled( True )
        self.dirEditCombo.setEditText( dirPath )

        self.setFilters( filters )

        self.findCombo.setEditText( what )
        self.findCombo.lineEdit().selectAll()
        self.findCombo.setFocus()

        # Check searchability
        self.__testSearchability()
        return


    def setFilters( self, filters ):
        " Sets up the filters "

        # Set filters if provided
        if len( filters ) > 0:
            self.filterCombo.setEditText( ";".join( filters ) )
        else:
            self.filterCombo.setEditText( "" )
        return

    def __testSearchability( self ):
        " Tests the searchability and sets the Find button status "

        startTime = time.time()
        if str( self.findCombo.currentText() ).strip() == "":
            self.findButton.setEnabled( False )
            self.findButton.setToolTip( "No text to search" )
            return

        if self.dirRButton.isChecked():
            dirname = str( self.dirEditCombo.currentText() ).strip()
            if dirname == "":
                self.findButton.setEnabled( False )
                self.findButton.setToolTip( "No directory path" )
                return
            if not os.path.isdir( dirname ):
                self.findButton.setEnabled( False )
                self.findButton.setToolTip( "Path is not a directory" )
                return

        # Now we need to match file names if there is a filter
        filtersText = str( self.filterCombo.currentText() ).strip()
        if filtersText == "":
            self.findButton.setEnabled( True )
            self.findButton.setToolTip( "Find in files" )
            return

        # Need to check the files match
        try:
            filterRe = re.compile( filtersText, re.IGNORECASE )
        except:
            self.findButton.setEnabled( False )
            self.findButton.setToolTip( "Incorrect files " \
                                        "filter regular expression" )
            return

        matched = False
        tooLong = False
        if self.projectRButton.isChecked():
            # Whole project
            for fname in GlobalData().project.filesList:
                if fname.endswith( os.path.sep ):
                    continue
                matched = filterRe.match( fname )
                if matched:
                    break
                # Check the time, it might took too long
                if time.time() - startTime > 0.1:
                    tooLong = True
                    break

        elif self.openFilesRButton.isChecked():
            # Opened files
            openedFiles = self.editorsManager.getTextEditors()
            for record in openedFiles:
                matched = filterRe.match( record[ 1 ] )
                if matched:
                    break
                # Check the time, it might took too long
                if time.time() - startTime > 0.1:
                    tooLong = True
                    break

        else:
            # Search in the dir
            if not dirname.endswith( os.path.sep ):
                dirname += os.path.sep
            matched, tooLong = self.__matchInDir( dirname, filterRe, startTime )

        if matched:
            self.findButton.setEnabled( True )
            self.findButton.setToolTip( "Find in files" )
        else:
            if tooLong:
                self.findButton.setEnabled( True )
                self.findButton.setToolTip( "Find in files" )
            else:
                self.findButton.setEnabled( False )
                self.findButton.setToolTip( "No files matched to search in" )
        return

    @staticmethod
    def __matchInDir( path, filterRe, startTime ):
        " Provides the 'match' and 'too long' statuses "
        matched = False
        tooLong = False
        for item in os.listdir( path ):
            if time.time() - startTime > 0.1:
                tooLong = True
                return matched, tooLong
            if os.path.isdir( path + item ):
                dname = path + item + os.path.sep
                matched, tooLong = FindInFilesDialog.__matchInDir( dname,
                                                                   filterRe,
                                                                   startTime )
                if matched or tooLong:
                    return matched, tooLong
                continue
            if filterRe.match( path + item ):
                matched = True
                return matched, tooLong
        return matched, tooLong

    def __projectClicked( self ):
        " project radio button clicked "
        self.dirEditCombo.setEnabled( False )
        self.dirSelectButton.setEnabled( False )
        self.__testSearchability()
        return

    def __openFilesOnlyClicked( self ):
        " open files only radio button clicked "
        self.dirEditCombo.setEnabled( False )
        self.dirSelectButton.setEnabled( False )
        self.__testSearchability()
        return

    def __dirClicked( self ):
        " dir radio button clicked "
        self.dirEditCombo.setEnabled( True )
        self.dirSelectButton.setEnabled( True )
        self.dirEditCombo.setFocus()
        self.__testSearchability()
        return

    def __someTextChanged( self, text ):
        " Text to search, filter or dir name has been changed "
        self.__testSearchability()
        return

    def __selectDirClicked( self ):
        " The user selects a directory "
        dirName = QFileDialog.getExistingDirectory( self,
                    "Select directory to search in",
                    self.dirEditCombo.currentText(),
                    QFileDialog.Options( QFileDialog.ShowDirsOnly ) )

        if not dirName.isEmpty():
            self.dirEditCombo.setEditText( os.path.normpath( str( dirName ) ) )
        self.__testSearchability()
        return


    @staticmethod
    def __projectFiles( filterRe ):
        " Project files list respecting the mask "
        files = []
        for fname in GlobalData().project.filesList:
            if fname.endswith( os.path.sep ):
                continue
            if filterRe is None or filterRe.match( fname ):
                mainWindow = GlobalData().mainWindow
                widget = mainWindow.getWidgetForFileName( fname )
                if widget is None:
                    fileType = detectFileType( fname )
                    if fileType not in [ PythonCompiledFileType, PixmapFileType,
                                         ELFFileType, SOFileType, PDFFileType,
                                         BrokenSymlinkFileType ]:
                        files.append( ItemToSearchIn( fname, "" ) )
                else:
                    if widget.getType() in \
                                [ MainWindowTabWidgetBase.PlainTextEditor ]:
                        files.append( ItemToSearchIn( fname,
                                                      widget.getUUID() ) )
        return files

    def __openedFiles( self, filterRe ):
        " Currently opened editor buffers "

        files = []
        openedFiles = self.editorsManager.getTextEditors()
        for record in openedFiles:
            uuid = record[ 0 ]
            fname = record[ 1 ]
            if filterRe is None or filterRe.match( fname ):
                files.append( ItemToSearchIn( fname, uuid ) )
        return files

    @staticmethod
    def __dirFiles( path, filterRe, files ):
        " Files recursively for the dir "
        for item in os.listdir( path ):
            if os.path.isdir( path + item ):
                FindInFilesDialog.__dirFiles( path + item + os.path.sep,
                                              filterRe, files )
                continue
            realItem = os.path.realpath( path + item )
            if filterRe is None or filterRe.match( realItem ):
                found = False
                for itm in files:
                    if itm.fileName == realItem:
                        found = True
                        break
                if not found:
                    mainWindow = GlobalData().mainWindow
                    widget = mainWindow.getWidgetForFileName( realItem )
                    if widget is None:
                        fileType = detectFileType( realItem )
                        if fileType not in [ PythonCompiledFileType,
                                             PixmapFileType, ELFFileType,
                                             SOFileType, PDFFileType,
                                             BrokenSymlinkFileType ]:
                            files.append( ItemToSearchIn( realItem, "" ) )
                    else:
                        if widget.getType() in \
                                    [ MainWindowTabWidgetBase.PlainTextEditor ]:
                            files.append( ItemToSearchIn( realItem,
                                                          widget.getUUID() ) )
        return


    def __buildFilesList( self ):
        " Builds the list of files to search in "
        filtersText = str( self.filterCombo.currentText() ).strip()
        if filtersText != "":
            filterRe = re.compile( filtersText, re.IGNORECASE )
        else:
            filterRe = None

        if self.projectRButton.isChecked():
            return self.__projectFiles( filterRe )

        if self.openFilesRButton.isChecked():
            return self.__openedFiles( filterRe )

        dirname = str( self.dirEditCombo.currentText() ).strip()
        if not dirname.endswith( os.path.sep ):
            dirname += os.path.sep
        files = []
        self.__dirFiles( dirname, filterRe, files )
        return files


    def __process( self ):
        " Search process "

        # Add entries to the combo box if required
        regexpText = str( self.findCombo.currentText() )
        if regexpText in self.findFilesWhat:
            self.findFilesWhat.remove( regexpText )
        self.findFilesWhat.insert( 0, regexpText )
        if len( self.findFilesWhat ) > 32:
            self.findFilesWhat = self.findFilesWhat[ : 32 ]
        self.findCombo.clear()
        self.findCombo.addItems( self.findFilesWhat )

        filtersText = str( self.filterCombo.currentText() ).strip()
        if filtersText in self.findFilesMasks:
            self.findFilesMasks.remove( filtersText )
        self.findFilesMasks.insert( 0, filtersText )
        if len( self.findFilesMasks ) > 32:
            self.findFilesMasks = self.findFilesMasks[ : 32 ]
        self.filterCombo.clear()
        self.filterCombo.addItems( self.findFilesMasks )

        if self.dirRButton.isChecked():
            dirText = str( self.dirEditCombo.currentText() ).strip()
            if dirText in self.findFilesDirs:
                self.findFilesDirs.remove( dirText )
            self.findFilesDirs.insert( 0, dirText )
            if len( self.findFilesDirs ) > 32:
                self.findFilesDirs = self.findFilesDirs[ : 32 ]
            self.dirEditCombo.clear()
            self.dirEditCombo.addItems( self.findFilesDirs )

        # Save the combo values for further usage
        if GlobalData().project.fileName != "":
            GlobalData().project.setFindInFilesHistory( self.findFilesWhat,
                                                        self.findFilesDirs,
                                                        self.findFilesMasks )
        else:
            Settings().findFilesWhat = self.findFilesWhat
            Settings().findFilesDirs = self.findFilesDirs
            Settings().findFilesMasks = self.findFilesMasks


        self.__inProgress = True
        numberOfMatches = 0
        self.searchResults = []
        self.searchRegexp = None

        # Form the regexp to search
        if self.regexpCheckBox.isChecked():
            regexpText = re.escape( regexpText )
        if self.wordCheckBox.isChecked():
            regexpText = "\\b%s\\b" % regexpText
        flags = re.UNICODE | re.LOCALE
        if not self.caseCheckBox.isChecked():
            flags |= re.IGNORECASE

        try:
            self.searchRegexp = re.compile( regexpText, flags )
        except:
            logging.error( "Invalid search expression" )
            self.close()
            return


        QApplication.setOverrideCursor( QCursor( Qt.WaitCursor ) )
        self.fileLabel.setPath( 'Building list of files to search in...' )
        files = self.__buildFilesList()
        QApplication.restoreOverrideCursor()
        QApplication.processEvents()

        if len( files ) == 0:
            self.fileLabel.setPath( 'No files to search in' )
            return

        self.progressBar.setRange( 0, len( files ) )

        index = 1
        for item in files:

            if self.__cancelRequest:
                self.__inProgress = False
                self.close()
                return

            self.fileLabel.setPath( 'Matches: ' + str( numberOfMatches ) + \
                                    ' Processing: ' + item.fileName )

            item.search( self.searchRegexp )
            found = len( item.matches )
            if found > 0:
                numberOfMatches += found
                self.searchResults.append( item )

            self.progressBar.setValue( index )
            index += 1

            QApplication.processEvents()

        if numberOfMatches == 0:
            if len( files ) == 1:
                self.fileLabel.setPath( "No matches in 1 file." )
            else:
                self.fileLabel.setPath( "No matches in " + \
                                        str( len( files ) ) + " files." )
            self.__inProgress = False
        else:
            self.close()
        return

