#
# -*- coding: utf-8 -*-
#
# codimension - graphics python two-way code editor and analyzer
# Copyright (C) 2011  Sergey Satskiy <sergey.satskiy@gmail.com>
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

""" The diff viewer implementation """

from PyQt4.QtCore import Qt, SIGNAL, QSize
from PyQt4.QtGui import QHBoxLayout, QWidget, QAction, QToolBar, \
                        QSizePolicy, QVBoxLayout
from utils.pixmapcache import PixmapCache
from htmltabwidget     import HTMLTabWidget
from utils.globals     import GlobalData


class DiffViewer( QWidget ):
    """ The tag help viewer widget """

    NODIFF = '<html><body bgcolor="#ffffe6"></body></html>'

    def __init__( self, parent = None ):
        QWidget.__init__( self, parent )

        self.__viewer = None
        self.__clearButton = None
        self.__sendUpButton = None
        self.__createLayout()
        self.__isEmpty = True
        self.__tooltip = ""
        self.__inClear = False

        self.__viewer.setHTML( self.NODIFF )
        self.__updateToolbarButtons()
        return

    def __createLayout( self ):
        " Helper to create the viewer layout "

        self.__viewer = HTMLTabWidget()

        # Buttons
        self.__sendUpButton = QAction( \
            PixmapCache().getIcon( 'senddiffup.png' ),
            'Send to Main Editing Area', self )
        self.connect( self.__sendUpButton, SIGNAL( "triggered()" ),
                      self.__sendUp )
        spacer = QWidget()
        spacer.setSizePolicy( QSizePolicy.Expanding, QSizePolicy.Expanding )
        self.__clearButton = QAction( \
            PixmapCache().getIcon( 'trash.png' ),
            'Clear Generated Diff', self )
        self.connect( self.__clearButton, SIGNAL( "triggered()" ),
                      self.__clear )

        # Toolbar
        toolbar = QToolBar()
        toolbar.setOrientation( Qt.Vertical )
        toolbar.setMovable( False )
        toolbar.setAllowedAreas( Qt.LeftToolBarArea )
        toolbar.setIconSize( QSize( 16, 16 ) )
        toolbar.setFixedWidth( 28 )
        toolbar.setContentsMargins( 0, 0, 0, 0 )
        toolbar.addAction( self.__sendUpButton )
        toolbar.addWidget( spacer )
        toolbar.addAction( self.__clearButton )

        verticalLayout = QVBoxLayout()
        verticalLayout.setContentsMargins( 2, 2, 2, 2 )
        verticalLayout.setSpacing( 2 )
        verticalLayout.addWidget( self.__viewer )

        # layout
        layout = QHBoxLayout()
        layout.setContentsMargins( 0, 0, 0, 0 )
        layout.setSpacing( 0 )
        layout.addWidget( toolbar )
        layout.addLayout( verticalLayout )

        self.setLayout( layout )
        return

    def setHTML( self, content, tooltip ):
        """ Shows the given content """
        if self.__inClear:
            self.__viewer.setHTML( content )
            return

        if content == '' or content is None:
            self.__clear()
        else:
            self.__viewer.setHTML( content )
            self.__isEmpty = False
            self.__updateToolbarButtons()
            self.__tooltip = tooltip
        return

    def __sendUp( self ):
        """ Triggered when the content should be sent
            to the main editor area """
        if not self.__isEmpty:
            GlobalData().mainWindow.showDiffInMainArea( self.__viewer.getHTML(),
                                                        self.__tooltip )
        return

    def __clear( self ):
        """ Triggered when the content should be cleared """
        self.__inClear = True
        # Dirty hack - reset the tooltip
        GlobalData().mainWindow.showDiff( "", "No diff shown" )
        self.__viewer.setHTML( DiffViewer.NODIFF )
        self.__inClear = False

        self.__isEmpty = True
        self.__tooltip = ""
        self.__updateToolbarButtons()
        return

    def __updateToolbarButtons( self ):
        " Contextually updates toolbar buttons "
        self.__sendUpButton.setEnabled( not self.__isEmpty )
        self.__clearButton.setEnabled( not self.__isEmpty )
        return
