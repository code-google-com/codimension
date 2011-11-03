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

""" QsciScintilla wrapper """

import re
from PyQt4.QtCore import QString, Qt, QRegExp
from PyQt4.QtGui import QApplication, QPalette
from PyQt4.Qsci import QsciScintilla



class ScintillaWrapper( QsciScintilla ):
    """ QsciScintilla wrapper implementation """

    def __init__( self, parent = None ):

        QsciScintilla.__init__( self, parent )

        self.zoom = 0

        self.__targetSearchFlags = 0
        self.__targetSearchExpr = QString()
        self.__targetSearchStart = 0
        self.__targetSearchEnd = -1
        self.__targetSearchActive = False
        return

    def setLexer( self, lex = None ):
        """ Sets the new lexer or resets if None """

        QsciScintilla.setLexer( self, lex )
        if lex is None:
            self.clearStyles()
        return

    def clearStyles( self ):
        """ Sets the styles according the selected Qt style """

        palette = QApplication.palette()
        self.SendScintilla( self.SCI_STYLESETFORE, self.STYLE_DEFAULT,
                            palette.color( QPalette.Text ) )
        self.SendScintilla( self.SCI_STYLESETBACK, self.STYLE_DEFAULT,
                            palette.color( QPalette.Base ) )
        self.SendScintilla( self.SCI_STYLECLEARALL )
        self.SendScintilla( self.SCI_CLEARDOCUMENTSTYLE )
        return

    def monospacedStyles( self, font ):
        """ Sets the current style to be monospaced """

        try:
            rangeLow = range( self.STYLE_DEFAULT )
        except AttributeError:
            rangeLow = range( 32 )

        try:
            rangeHigh = range( self.STYLE_LASTPREDEFINED + 1,
                               self.STYLE_MAX + 1 )
        except AttributeError:
            rangeHigh = range( 40, 128 )

        fontFamily = str( font.family() )
        fontSize = font.pointSize()
        for style in rangeLow + rangeHigh:
            self.SendScintilla( self.SCI_STYLESETFONT, style, fontFamily )
            self.SendScintilla( self.SCI_STYLESETSIZE, style, fontSize )
        return

    def linesOnScreen( self ):
        """ Provides the number of the visible lines """

        return self.SendScintilla( self.SCI_LINESONSCREEN )

    def lineAt( self, pos ):
        """ Calculates the line at a position. pos is int or QPoint.
            Returns -1 if there is no line at pos """

        if type( pos ) == type( 1 ):
            scipos = pos
        else:
            scipos = self.SendScintilla( self.SCI_POSITIONFROMPOINT,
                                         pos.x(), pos.y() )
        line = self.SendScintilla( self.SCI_LINEFROMPOSITION, scipos )

        # Zero based, so >=
        if line >= self.lines():
            return -1
        return line

    def currentPosition( self ):
        """ Provides the current cursor position """
        return self.SendScintilla( self.SCI_GETCURRENTPOS )

    def getCurrentPixelPosition( self ):
        " Provides the current text cursor position in points "
        pos = self.SendScintilla( self.SCI_GETCURRENTPOS )
        x = self.SendScintilla( self.SCI_POINTXFROMPOSITION, pos )
        y = self.SendScintilla( self.SCI_POINTYFROMPOSITION, pos )
        return x, y

    def setCurrentPosition( self, pos ):
        " Sets the current position "
        self.SendScintilla( self.SCI_SETCURRENTPOS, pos )
        return

    def styleAt( self, pos ):
        """ Provides the style at the pos """
        return self.SendScintilla( self.SCI_GETSTYLEAT, pos )

    def currentStyle( self ):
        """ Provides the style at the current cursor position """
        return self.styleAt( self.currentPosition() )

    def getEndStyled( self ):
        """ Provides the last styled position """
        return self.SendScintilla( self.SCI_GETENDSTYLED )

    def startStyling( self, pos, mask ):
        """ Prepares styling """
        self.SendScintilla( self.SCI_STARTSTYLING, pos, mask )
        return

    def setStyling( self, length, style ):
        """ Styles some text """

        self.SendScintilla( self.SCI_SETSTYLING, length, style )
        return

    def setStyleBits( self, bits ):
        """ Sets the number of bits to be used for styling """

        self.SendScintilla( self.SCI_SETSTYLEBITS, bits )
        return

    def charAt( self, pos ):
        """ Provides the character at the pos in the text
            observing multibyte characters """

        character = self.rawCharAt( pos )
        if character and ord( character ) > 127 and self.isUtf8():
            if ( ord( character[0] ) & 0xF0 ) == 0xF0:
                utf8Len = 4
            elif ( ord( character[0] ) & 0xE0 ) == 0xE0:
                utf8Len = 3
            elif ( ord( character[0] ) & 0xC0 ) == 0xC0:
                utf8Len = 2
            while len( character ) < utf8Len:
                pos += 1
                character += self.rawCharAt( pos )
            return character.decode( 'utf8' )
        return character

    def rawCharAt( self, pos ):
        """ Provides the raw character at the pos in the text """

        character = self.SendScintilla( self.SCI_GETCHARAT, pos )
        if character == 0:
            return ""
        if character < 0:
            return chr( character + 256 )
        return chr( character )

    def foldLevelAt( self, line ):
        """ Provides the fold level for the line in the document """

        level = self.SendScintilla( self.SCI_GETFOLDLEVEL, line )
        return (level & self.SC_FOLDLEVELNUMBERMASK) - self.SC_FOLDLEVELBASE

    def foldFlagsAt( self, line ):
        """ Provides the fold flags for the line in the document """

        level = self.SendScintilla( self.SCI_GETFOLDLEVEL, line )
        return level & ~self.SC_FOLDLEVELNUMBERMASK

    def foldHeaderAt( self, line ):
        """ Determines if the line in the document is a fold header line """

        level = self.SendScintilla( self.SCI_GETFOLDLEVEL, line )
        return level & self.SC_FOLDLEVELHEADERFLAG

    def foldExpandedAt( self, line ):
        """ Determines if a fold is expanded """

        return self.SendScintilla( self.SCI_GETFOLDEXPANDED, line )

    def setIndentationGuideView( self, view ):
        """ Sets the view of the indentation guides """

        self.SendScintilla( self.SCI_SETINDENTATIONGUIDES, view )
        return

    def indentationGuideView( self ):
        """ Provides the indentation guide view """

        return self.SendScintilla( self.SCI_GETINDENTATIONGUIDES )

    # methods below are missing from QScintilla

    def zoomIn( self, zoom = 1 ):
        """ Increases the zoom factor """

        self.zoom += zoom
        QsciScintilla.zoomIn( self, zoom )
        return

    def zoomOut( self, zoom = 1 ):
        """ Decreases the zoom factor """

        self.zoom -= zoom
        QsciScintilla.zoomOut( self, zoom )
        return

    def zoomTo( self, zoom ):
        """ Zooms to the specific zoom factor """

        self.zoom = zoom
        QsciScintilla.zoomTo( self, zoom )
        return

    def getZoom( self ):
        """ Provides the current zoom factor """
        return self.zoom

    def editorCommand( self, cmd ):
        """ Executes a simple editor command """
        self.SendScintilla( cmd )
        return

    def scrollVertical( self, lines ):
        """ Scroll the text area the given lines up or down """

        self.SendScintilla( self.SCI_LINESCROLL, 0, lines )
        return

    def moveCursorToEOL( self ):
        """ Moves the cursor to the end of line """

        self.SendScintilla( self.SCI_LINEEND )
        return

    def moveCursorLeft( self ):
        """ Moves the cursor left """

        self.SendScintilla( self.SCI_CHARLEFT )
        return

    def moveCursorRight( self ):
        """ Moves the cursor right """

        self.SendScintilla( self.SCI_CHARRIGHT )
        return

    def moveCursorWordLeft( self ):
        """ Moves the cursor one word left """

        self.SendScintilla( self.SCI_WORDLEFT )
        return

    def moveCursorWordRight( self ):
        """ Moves the cursor one word right """

        self.SendScintilla( self.SCI_WORDRIGHT )
        return

    def newLineBelow( self ):
        """ Inserts a new line below the current one """

        self.SendScintilla( self.SCI_LINEEND )
        self.SendScintilla( self.SCI_NEWLINE )
        return

    def deleteBack( self ):
        """ Deletes the character to the left of the cursor """

        self.SendScintilla( self.SCI_DELETEBACK )
        return

    def delete( self ):
        """ Deletes the character to the right of the cursor """

        self.SendScintilla( self.SCI_CLEAR )
        return

    def deleteWordLeft( self ):
        """ Deletes the word to the left of the cursor """

        self.SendScintilla( self.SCI_DELWORDLEFT )
        return

    def deleteWordRight( self ):
        """ Deletes the word to the right of the cursor """

        self.SendScintilla( self.SCI_DELWORDRIGHT )
        return

    def deleteLineLeft( self ):
        """ Deletes the line to the left of the cursor """

        self.SendScintilla( self.SCI_DELLINELEFT )
        return

    def deleteLineRight( self ):
        """ Deletes the line to the right of the cursor """

        self.SendScintilla( self.SCI_DELLINERIGHT )
        return

    def extendSelectionLeft( self ):
        """ Extends the selection one character to the left """

        self.SendScintilla( self.SCI_CHARLEFTEXTEND )
        return

    def extendSelectionRight( self ):
        """ Extends the selection one character to the right """

        self.SendScintilla( self.SCI_CHARRIGHTEXTEND )
        return

    def extendSelectionWordLeft( self ):
        """ Extends the selection one word to the left """

        self.SendScintilla( self.SCI_WORDLEFTEXTEND )
        return

    def extendSelectionWordRight( self ):
        """ Extends the selection one word to the right """

        self.SendScintilla( self.SCI_WORDRIGHTEXTEND )
        return

    def extendSelectionToBOL( self ):
        """ Extends the selection to the beginning of the line """

        self.SendScintilla( self.SCI_VCHOMEEXTEND )
        return

    def extendSelectionToEOL( self ):
        """ Extends the selection to the end of the line """

        self.SendScintilla( self.SCI_LINEENDEXTEND )
        return

    def setHScrollOffset( self, value ):
        " Sets the current horizontal offset "
        self.SendScintilla( self.SCI_SETXOFFSET, value )
        return

    def getHScrollOffset( self ):
        " Provides the current horizontal offset "
        return self.SendScintilla( self.SCI_GETXOFFSET )

    def getLineSeparator( self ):
        """ Provides the line separator for the current eol mode """

        mode = self.eolMode()
        if mode == QsciScintilla.EolWindows:
            return '\r\n'
        if mode == QsciScintilla.EolUnix:
            return '\n'
        if mode == QsciScintilla.EolMac:
            return '\r'
        return ''

    def getEolIndicator( self ):
        """ Provides the eol indicator for the current eol mode """

        mode = self.eolMode()
        if mode == QsciScintilla.EolWindows:
            return 'CRLF'
        if mode == QsciScintilla.EolUnix:
            return 'LF'
        if mode == QsciScintilla.EolMac:
            return 'CR'
        return ''

    def setEolModeByEolString( self, eolStr ):
        """ Sets the eol mode by the eol string """

        if eolStr == '\n':
            self.setEolMode( self.EolMode( self.EolUnix ) )
            return
        if eolStr == '\r\n':
            self.setEolMode( self.EolMode( self.EolWindows ) )
            return
        if eolStr == '\r':
            self.setEolMode( self.EolMode( self.EolMac ) )
            return
        self.setEolMode( self.EolMode( self.EolUnix ) )
        return

    @staticmethod
    def detectEolString( txt ):
        """ Determines the eol string """

        utxt = unicode( txt )
        if len( utxt.split( "\r\n", 1 ) ) == 2:
            return '\r\n'
        if len( utxt.split( "\n", 1 ) ) == 2:
            return '\n'
        if len( utxt.split( "\r", 1 ) ) == 2:
            return '\r'
        return None

        # methods to perform searches in target range

    def positionFromPoint( self, point ):
        """ Calculates the scintilla position from a point in the window """

        return self.SendScintilla( self.SCI_POSITIONFROMPOINTCLOSE,
                                   point.x(), point.y() )

    def positionBefore( self, pos ):
        """ Provides the position before the given position taking into account
            multibyte characters """

        return self.SendScintilla( self.SCI_POSITIONBEFORE, pos )

    def positionAfter( self, pos ):
        """ Provides the position after the given position taking into account
            multibyte characters """

        return self.SendScintilla( self.SCI_POSITIONAFTER, pos )

    def positionFromLineIndex( self, line, index ):
        """ Converts line and index to an absolute position """

        pos = self.SendScintilla( self.SCI_POSITIONFROMLINE, line )

        # Allow for multi-byte characters
        for i in range( index ):
            pos = self.positionAfter( pos )
        return pos

    def lineIndexFromPosition( self, pos ):
        """ Converts an absolute position to line and index """

        lin = self.SendScintilla( self.SCI_LINEFROMPOSITION, pos )
        linpos = self.SendScintilla( self.SCI_POSITIONFROMLINE, lin )
        index = 0

        # Allow for multi-byte characters
        while linpos < pos:
            new_linpos = self.positionAfter( linpos )

            # If the position hasn't moved then we must be at the end
            # of the text (which implies that the position passed was
            # beyond the end of the text)
            if new_linpos == linpos:
                break

            linpos = new_linpos
            index += 1

        return lin, index

    def lineEndPosition( self, line ):
        """ Determines the line end position of the given line """

        return self.SendScintilla( self.SCI_GETLINEENDPOSITION, line )

    def __doSearchTarget( self ):
        """ Searches in target """

        if self.__targetSearchStart == self.__targetSearchEnd:
            self.__targetSearchActive = False
            return False

        self.SendScintilla( self.SCI_SETTARGETSTART, self.__targetSearchStart )
        self.SendScintilla( self.SCI_SETTARGETEND, self.__targetSearchEnd )
        self.SendScintilla( self.SCI_SETSEARCHFLAGS, self.__targetSearchFlags )
        pos = self.SendScintilla( self.SCI_SEARCHINTARGET,
                                  len( self.__targetSearchExpr ),
                                  self.__targetSearchExpr )

        if pos == -1:
            self.__targetSearchActive = False
            return False

        targend = self.SendScintilla( self.SCI_GETTARGETEND )
        self.__targetSearchStart = targend
        return True

    def getFoundTarget( self ):
        " Provides the recently found target "
        if self.__targetSearchActive:
            spos = self.SendScintilla( self.SCI_GETTARGETSTART )
            epos = self.SendScintilla( self.SCI_GETTARGETEND )
            return ( spos, epos - spos )
        return ( 0, 0 )

    def getTargetText( self ):
        " Provides the found text "
        begin, length = self.getFoundTarget()
        if begin == 0 and length == 0:
            return ""
        line, pos = self.lineIndexFromPosition( begin )
        return self.getTextAtPos( line, pos, length )

    def findFirstTarget( self, expr_, isRegexp, isCasesensitive,
                         isWordonly,
                         begline = -1, begindex = -1,
                         endline = -1, endindex = -1,
                         isWordstart = False):
        """ Searches in a specified range of text without
            setting the selection """

        self.__targetSearchFlags = 0
        if isRegexp:
            self.__targetSearchFlags |= self.SCFIND_REGEXP
        if isCasesensitive:
            self.__targetSearchFlags |= self.SCFIND_MATCHCASE
        if isWordonly:
            self.__targetSearchFlags |= self.SCFIND_WHOLEWORD
        if isWordstart:
            self.__targetSearchFlags |= self.SCFIND_WORDSTART

        if begline < 0 or begindex < 0:
            self.__targetSearchStart = self.SendScintilla( \
                                            self.SCI_GETCURRENTPOS )
        else:
            self.__targetSearchStart = self.positionFromLineIndex( \
                                            begline, begindex )

        if endline < 0 or endindex < 0:
            self.__targetSearchEnd = self.SendScintilla( \
                                          self.SCI_GETTEXTLENGTH )
        else:
            self.__targetSearchEnd = self.positionFromLineIndex( \
                                          endline, endindex )

        if self.isUtf8():
            self.__targetSearchExpr = unicode( expr_ ).encode( "utf-8" )
        else:
            self.__targetSearchExpr = unicode( expr_ ).encode( "latin1" )

        if self.__targetSearchExpr:
            self.__targetSearchActive = True
            return self.__doSearchTarget()

        return False

    def findNextTarget( self ):
        " Finds the next occurrence in the target range "
        if not self.__targetSearchActive:
            return False
        return self.__doSearchTarget()

    def replaceTarget( self, replaceStr ):
        """ Replaces the string found by the last search in target """

        if not self.__targetSearchActive:
            return

        if self.__targetSearchFlags & self.SCFIND_REGEXP:
            cmd = self.SCI_REPLACETARGETRE
        else:
            cmd = self.SCI_REPLACETARGET

        start = self.SendScintilla( self.SCI_GETTARGETSTART )

        if self.isUtf8():
            replacement = replaceStr.encode( "utf-8" )
        else:
            replacement = replaceStr.encode( "latin1" )

        if replacement == self.getTargetText():
            # The found target is the same as what the user wants it
            # to replace with
            return False

        self.SendScintilla( cmd, len( replacement ), replacement )
        self.__targetSearchStart = start + len( replaceStr )
        return True

    # indicator handling methods

    def __checkIndicator( self, indicator ):
        """ Checks the indicator value """

        if indicator < self.INDIC_CONTAINER or \
           indicator > self.INDIC_MAX:
            raise ValueError( "indicator number out of range" )
        return

    def indicatorDefine( self, indicator, style, color ):
        """ Defines the indicator appearance """

        self.__checkIndicator( indicator )

        if style < self.INDIC_PLAIN or style > self.INDIC_ROUNDBOX:
            raise ValueError( "style out of range" )

        self.SendScintilla( self.SCI_INDICSETSTYLE, indicator, style )
        self.SendScintilla( self.SCI_INDICSETFORE, indicator, color )
        return

    def setCurrentIndicator( self, indicator ):
        " Sets the current indicator "
        self.__checkIndicator( indicator )
        self.SendScintilla( self.SCI_SETINDICATORCURRENT, indicator)
        return

    def getCurrentIndicator( self ):
        " Provides the current indicator "
        return self.SendScintilla( self.SCI_GETINDICATORCURRENT )

    def setIndicatorRange( self, indicator, spos, length ):
        " Sets the indicator for the given range "
        self.setCurrentIndicator( indicator )
        self.SendScintilla( self.SCI_INDICATORFILLRANGE, spos, length )
        return

    def setIndicator( self, indicator, sline, sindex, eline, eindex ):
        """ Sets the indicator for the given range """

        spos = self.positionFromLineIndex( sline, sindex )
        epos = self.positionFromLineIndex( eline, eindex )
        self.setIndicatorRange( indicator, spos, epos - spos )
        return

    def clearIndicatorRange( self, indicator, spos, length ):
        """ Clears the indicator for the given range """

        self.setCurrentIndicator( indicator )
        self.SendScintilla( self.SCI_INDICATORCLEARRANGE, spos, length )
        return

    def clearIndicator( self, indicator, sline, sindex, eline, eindex ):
        """ Clears the indicator for the given range """

        spos = self.positionFromLineIndex( sline, sindex )
        epos = self.positionFromLineIndex( eline, eindex )
        self.clearIndicatorRange( indicator, spos, epos - spos )
        return

    def clearAllIndicators( self, indicator ):
        " Clears all occurrences of an indicator "
        self.clearIndicatorRange( indicator, 0, self.length() )
        return

    def hasIndicator( self, indicator, pos ):
        """ Tests for the existence of the indicator """

        return self.SendScintilla( self.SCI_INDICATORVALUEAT, indicator, pos )

    # interface methods to the standard keyboard command set

    def clearKeys( self ):
        """ Clears the key commands """

        # call into the QsciCommandSet
        self.standardCommands().clearKeys()
        return

    def clearAlternateKeys( self ):
        """ Clears the alternate key commands """

        # call into the QsciCommandSet
        self.standardCommands().clearAlternateKeys()
        return

    def setCurrentLineHighlight( self, isHighlighted, color ):
        " Sets the current line highlight "
        self.SendScintilla( self.SCI_SETCARETLINEVISIBLE, isHighlighted )
        if isHighlighted:
            self.SendScintilla( self.SCI_SETCARETLINEBACK, color )
        return

    def removeTrailingWhitespaces( self ):
        " Removes trailing whitespaces "
        searchRE = r"[ \t]+$"    # whitespace at the end of a line

        line, pos = self.getCursorPosition()
        found = self.findFirstTarget( searchRE, True, False, False, 0, 0 )
        self.beginUndoAction()
        while found:
            self.replaceTarget( "" )
            found = self.findNextTarget()
        self.endUndoAction()
        self.setCursorPosition( line, pos )
        return

    def expandTabs( self, spaces ):
        " Expands tabs "
        searchRE = r"\t"

        line, pos = self.getCursorPosition()
        replace = spaces * " "
        found = self.findFirstTarget( searchRE, True, False, False, 0, 0 )
        self.beginUndoAction()
        while found:
            self.replaceTarget( replace )
            found = self.findNextTarget()
        self.endUndoAction()
        self.setCursorPosition( line, pos )
        return

    def getSearchText( self, selectionOnly = False ):
        " Provides the guessed text for searching "

        if self.hasSelectedText():
            text = self.selectedText()
            if text.contains( '\r' ) or text.contains( '\n' ):
                # the selection contains at least a newline, it is
                # unlikely to be the expression to search for
                return QString( "" )
            return text

        if not selectionOnly:
            # no selected text, determine the word at the current position
            return self.getCurrentWord()

        return QString( "" )

    def getCurrentWord( self, addChars = "" ):
        " Provides the word at the current position "

        line, col = self.getCursorPosition()
        return self.getWord( line, col, 0, True, addChars )

    def getWord( self, line, col, direction = 0, useWordChars = True, addChars = "" ):
        """ Provides the word at a position.
            direction direction to look in (0 = whole word, 1 = left, 2 = right)
        """
        start, end = self.getWordBoundaries( line, col, useWordChars, addChars )
        if direction == 1:
            end = col
        elif direction == 2:
            start = col

        if end > start:
            text = self.text( line )
            return text.mid( start, end - start )
        return QString( '' )

    def getWordBoundaries( self, line, col, useWordChars = True, addChars = "" ):
        " Provides the word boundaries at a position "

        text = self.text( line )
        if self.caseSensitive():
            cs = Qt.CaseSensitive
        else:
            cs = Qt.CaseInsensitive
        wc = self.wordCharacters()
        if wc is None or not useWordChars:
            regExp = QRegExp( '[^\w_]', cs )
        else:
            wc += addChars
            wc = re.sub( '\w', "", wc )
            regExp = QRegExp( '[^\w%s]' % re.escape( wc ), cs )
        start = text.lastIndexOf( regExp, col ) + 1
        end = text.indexOf( regExp, col )
        if start == end + 1 and col > 0:
            # we are on a word boundary, try again
            start = text.lastIndexOf( regExp, col - 1 ) + 1
        if start == -1:
            start = 0
        if end == -1:
            end = text.length()

        return ( start, end )

    def getTextAtPos( self, line, col, length ):
        " Provides the text of the given length under the cursor "
        text = self.text( line )
        return text.mid( col, length )

