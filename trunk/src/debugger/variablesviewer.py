#
# -*- coding: utf-8 -*-
#
# codimension - graphics python two-way code editor and analyzer
# Copyright (C) 2010-2012  Sergey Satskiy <sergey.satskiy@gmail.com>
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

" Variables viewer "


from PyQt4.QtCore import Qt, SIGNAL
from PyQt4.QtGui import ( QFrame, QVBoxLayout, QLabel, QWidget,
                          QSizePolicy, QSpacerItem,
                          QHBoxLayout, QToolButton, QPalette )
from utils.pixmapcache import PixmapCache
from ui.combobox import CDMComboBox
from variablesbrowser import VariablesBrowser


class VariablesViewer( QWidget ):
    " Implements the variables viewer for a debugger "

    # First group of filters
    FilterGlobalAndLocal = 0
    FilterGlobalOnly = 1
    FilterLocalOnly = 2

    # Second group of filters
    FilterNone = 0
    Filter__ = 1
    Filter_ = 2

    def __init__( self, debugger, parent = None ):
        QWidget.__init__( self, parent )

        self.__browser = VariablesBrowser( debugger, self )
        self.__filter = VariablesViewer.FilterGlobalAndLocal
        self.__nameFilter = VariablesViewer.FilterNone
        self.__createLayout()
        return

    def __createLayout( self ):
        " Creates the widget layout "

        verticalLayout = QVBoxLayout( self )
        verticalLayout.setContentsMargins( 0, 0, 0, 0 )
        verticalLayout.setSpacing( 0 )

        headerFrame = QFrame()
        headerFrame.setFrameStyle( QFrame.StyledPanel )
        headerFrame.setAutoFillBackground( True )
        headerPalette = headerFrame.palette()
        headerBackground = headerPalette.color( QPalette.Background )
        headerBackground.setRgb( min( headerBackground.red() + 30, 255 ),
                                 min( headerBackground.green() + 30, 255 ),
                                 min( headerBackground.blue() + 30, 255 ) )
        headerPalette.setColor( QPalette.Background, headerBackground )
        headerFrame.setPalette( headerPalette )
        headerFrame.setFixedHeight( 24 )

        label = QLabel( "Variables" )

        expandingSpacer = QSpacerItem( 10, 10, QSizePolicy.Expanding )
        fixedSpacer = QSpacerItem( 3, 3 )

        self.__globalAndLocalButton = QToolButton()
        self.__globalAndLocalButton.setCheckable( True )
        self.__globalAndLocalButton.setChecked( True )
        self.__globalAndLocalButton.setIcon( PixmapCache().getIcon( 'dbgfltgl.png' ) )
        self.__globalAndLocalButton.setFixedSize( 20, 20 )
        self.__globalAndLocalButton.setToolTip( "Show global and local variables" )
        self.__globalAndLocalButton.setFocusPolicy( Qt.NoFocus )
        self.connect( self.__globalAndLocalButton, SIGNAL( 'clicked()' ),
                      self.__onGlobalAndLocalFilter )

        self.__localOnlyButton = QToolButton()
        self.__localOnlyButton.setCheckable( True )
        self.__localOnlyButton.setChecked( False )
        self.__localOnlyButton.setIcon( PixmapCache().getIcon( 'dbgfltlo.png' ) )
        self.__localOnlyButton.setFixedSize( 20, 20 )
        self.__localOnlyButton.setToolTip( "Show local variables only" )
        self.__localOnlyButton.setFocusPolicy( Qt.NoFocus )
        self.connect( self.__localOnlyButton, SIGNAL( 'clicked()' ),
                      self.__onLocalFilter )

        self.__globalOnlyButton = QToolButton()
        self.__globalOnlyButton.setCheckable( True )
        self.__globalOnlyButton.setChecked( False )
        self.__globalOnlyButton.setIcon( PixmapCache().getIcon( 'dbgfltgo.png' ) )
        self.__globalOnlyButton.setFixedSize( 20, 20 )
        self.__globalOnlyButton.setToolTip( "Show global variables only" )
        self.__globalOnlyButton.setFocusPolicy( Qt.NoFocus )
        self.connect( self.__globalOnlyButton, SIGNAL( 'clicked()' ),
                      self.__onGlobalFilter )

        # Predefined name filters
        self.__noHideButton = QToolButton()
        self.__noHideButton.setCheckable( True )
        self.__noHideButton.setChecked( True )
        self.__noHideButton.setIcon( PixmapCache().getIcon( 'dbgfltall.png' ) )
        self.__noHideButton.setFixedSize( 26, 26 )
        self.__noHideButton.setToolTip( "Do not hide _ and __ starting variables" )
        self.__noHideButton.setFocusPolicy( Qt.NoFocus )
        self.connect( self.__noHideButton, SIGNAL( 'clicked()' ),
                      self.__onNoHide )

        self.__hide__Button = QToolButton()
        self.__hide__Button.setCheckable( True )
        self.__hide__Button.setChecked( False )
        self.__hide__Button.setIcon( PixmapCache().getIcon( 'dbgflt__.png' ) )
        self.__hide__Button.setFixedSize( 26, 26 )
        self.__hide__Button.setToolTip( "Hide varibles starting with __" )
        self.__hide__Button.setFocusPolicy( Qt.NoFocus )
        self.connect( self.__hide__Button, SIGNAL( 'clicked()' ),
                      self.__onHide__ )

        self.__hide_Button = QToolButton()
        self.__hide_Button.setCheckable( True )
        self.__hide_Button.setChecked( False )
        self.__hide_Button.setIcon( PixmapCache().getIcon( 'dbgflt_.png' ) )
        self.__hide_Button.setFixedSize( 26, 26 )
        self.__hide_Button.setToolTip( "Hide variables starting with _" )
        self.__hide_Button.setFocusPolicy( Qt.NoFocus )
        self.connect( self.__hide_Button, SIGNAL( 'clicked()' ),
                      self.__onHide_ )
        fixedSpacer2 = QSpacerItem( 5, 5 )

        self.__filterEdit = CDMComboBox( True )
        self.__filterEdit.setSizePolicy( QSizePolicy.Expanding,
                                         QSizePolicy.Expanding )
        self.__filterEdit.lineEdit().setToolTip(
                                    "Space separated regular expressions" )
        self.__filterEdit.setFixedHeight( 26 )

        self.__execStatement = CDMComboBox( False )
        self.__execStatement.setSizePolicy( QSizePolicy.Expanding,
                                            QSizePolicy.Expanding )
        self.__execStatement.lineEdit().setToolTip(
                                "Expression to be executed on the debuggee" )
        self.__execStatement.setFixedHeight( 26 )
        fixedSpacer3 = QSpacerItem( 5, 5 )
        self.__execButton = QToolButton()
        self.__execButton.setText( "Exec" )

        self.__evalStatement = CDMComboBox( False )
        self.__evalStatement.setSizePolicy( QSizePolicy.Expanding,
                                            QSizePolicy.Expanding )
        self.__evalStatement.lineEdit().setToolTip(
                                "Expression to be evaluated on the debuggee" )
        self.__evalStatement.setFixedHeight( 26 )
        fixedSpacer4 = QSpacerItem( 5, 5 )
        self.__evalButton = QToolButton()
        self.__evalButton.setText( "Eval" )

        headerLayout = QHBoxLayout()
        headerLayout.setContentsMargins( 0, 0, 0, 0 )
        headerLayout.setSpacing( 0 )
        headerLayout.addSpacerItem( fixedSpacer )
        headerLayout.addWidget( label )
        headerLayout.addSpacerItem( expandingSpacer )
        headerLayout.addWidget( self.__globalAndLocalButton )
        headerLayout.addWidget( self.__localOnlyButton )
        headerLayout.addWidget( self.__globalOnlyButton )
        headerFrame.setLayout( headerLayout )

        filterLayout = QHBoxLayout()
        filterLayout.setContentsMargins( 0, 0, 0, 0 )
        filterLayout.setSpacing( 0 )
        filterLayout.addWidget( self.__noHideButton )
        filterLayout.addWidget( self.__hide__Button )
        filterLayout.addWidget( self.__hide_Button )
        filterLayout.addSpacerItem( fixedSpacer2 )
        filterLayout.addWidget( self.__filterEdit )

        execLayout = QHBoxLayout()
        execLayout.setContentsMargins( 0, 0, 0, 0 )
        execLayout.setSpacing( 0 )
        execLayout.addWidget( self.__execStatement )
        execLayout.addSpacerItem( fixedSpacer3 )
        execLayout.addWidget( self.__execButton )

        evalLayout = QHBoxLayout()
        evalLayout.setContentsMargins( 0, 0, 0, 0 )
        evalLayout.setSpacing( 0 )
        evalLayout.addWidget( self.__evalStatement )
        evalLayout.addSpacerItem( fixedSpacer4 )
        evalLayout.addWidget( self.__evalButton )

        verticalLayout.addWidget( headerFrame )
        verticalLayout.addLayout( filterLayout )
        verticalLayout.addWidget( self.__browser )
        verticalLayout.addLayout( execLayout )
        verticalLayout.addLayout( evalLayout )
        return

    def __onGlobalAndLocalFilter( self ):
        " Global and local filter has been pressed "
        if self.__filter == VariablesViewer.FilterGlobalAndLocal:
            # No changes
            return

        self.__globalAndLocalButton.setChecked( True )
        self.__localOnlyButton.setChecked( False )
        self.__globalOnlyButton.setChecked( False )

        self.__filter = VariablesViewer.FilterGlobalAndLocal
        return

    def __onLocalFilter( self ):
        " Local only filter has been pressed "
        if self.__filter == VariablesViewer.FilterLocalOnly:
            # No changes
            return

        self.__globalAndLocalButton.setChecked( False )
        self.__localOnlyButton.setChecked( True )
        self.__globalOnlyButton.setChecked( False )

        self.__filter = VariablesViewer.FilterLocalOnly
        return

    def __onGlobalFilter( self ):
        " Global only filter has been pressed "
        if self.__filter == VariablesViewer.FilterGlobalOnly:
            # No changes
            return

        self.__globalAndLocalButton.setChecked( False )
        self.__localOnlyButton.setChecked( False )
        self.__globalOnlyButton.setChecked( True )

        self.__filter = VariablesViewer.FilterGlobalOnly
        return

    def __onNoHide( self ):
        " No hide filter has pressed "
        if self.__nameFilter == VariablesViewer.FilterNone:
            # No changes
            return

        self.__noHideButton.setChecked( True )
        self.__hide__Button.setChecked( False )
        self.__hide_Button.setChecked( False )

        self.__nameFilter = VariablesViewer.FilterNone
        return

    def __onHide__( self ):
        " Hide __ filter has pressed "
        if self.__nameFilter == VariablesViewer.Filter__:
            # No changes
            return

        self.__noHideButton.setChecked( False )
        self.__hide__Button.setChecked( True )
        self.__hide_Button.setChecked( False )

        self.__nameFilter = VariablesViewer.Filter__
        return

    def __onHide_( self ):
        " Hide _ filter has pressed "
        if self.__nameFilter == VariablesViewer.Filter_:
            # No changes
            return

        self.__noHideButton.setChecked( False )
        self.__hide__Button.setChecked( False )
        self.__hide_Button.setChecked( True )

        self.__nameFilter = VariablesViewer.Filter_
        return

    def updateVariables( self, areGlobals, frameNumber, variables ):
        " Triggered when a new set of variables is received "
        self.__browser.showVariables( areGlobals, variables, frameNumber )
        return

    def updateVariable( self, areGlobals, variables ):
        " Triggered when a new variable has been received "
        self.__browser.showVariable( areGlobals, variables )
        return

    def clear( self ):
        " Clears the content "
        self.__browser.clear()
        return

