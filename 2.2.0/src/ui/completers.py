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

#
# The file was taken from eric 4.4.3 and adopted for codimension.
# Original copyright:
# Copyright (c) 2007 - 2010 Detlev Offenbach <detlev@die-offenbachs.de>
#


""" Various kinds of completers """


from PyQt4.QtCore import QDir, QStringList
from PyQt4.QtGui import QCompleter, QDirModel, QStringListModel


class FileCompleter( QCompleter ):
    """ Completer for file names """

    def __init__( self, parent = None,
                  completionMode = QCompleter.PopupCompletion,
                  showHidden = False ):

        QCompleter.__init__( self, parent )
        self.__model = QDirModel( self )

        if showHidden:
            filters = QDir.Filters( QDir.Dirs | QDir.Files | QDir.Drives | \
                                    QDir.AllDirs | QDir.Hidden )
        else:
            filters = QDir.Filters( QDir.Dirs | QDir.Files | \
                                    QDir.Drives | QDir.AllDirs )
        self.__model.setFilter( filters )

        self.setModel( self.__model )
        self.setCompletionMode( completionMode )

        if parent:
            parent.setCompleter( self )
        return


class DirCompleter( QCompleter ):
    """ Completer for directory names """

    def __init__( self, parent = None,
                  completionMode = QCompleter.PopupCompletion,
                  showHidden = False ):

        QCompleter.__init__( self, parent )
        self.__model = QDirModel( self )

        if showHidden:
            filters = QDir.Filters(QDir.Drives | QDir.AllDirs | QDir.Hidden)
        else:
            filters = QDir.Filters(QDir.Drives | QDir.AllDirs)
        self.__model.setFilter( filters )

        self.setModel( self.__model )
        self.setCompletionMode( completionMode )

        if parent:
            parent.setCompleter( self )
        return


class StringListCompleter( QCompleter ):
    """ Completer for strings lists """

    def __init__( self, parent = None, strings = QStringList(),
                  completionMode = QCompleter.PopupCompletion ):

        QCompleter.__init__( self, parent )
        self.__model = QStringListModel( strings, parent )
        self.setModel( self.__model )
        self.setCompletionMode( completionMode )

        if parent:
            parent.setCompleter( self )
        return

