/*
 * codimension - graphics python two-way code editor and analyzer
 * Copyright (C) 2014  Sergey Satskiy <sergey.satskiy@gmail.com>
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program.  If not, see <http://www.gnu.org/licenses/>.
 *
 * $Id$
 *
 * Python extension module
 */


#include "cflowversion.hpp"
#include "cflowdocs.hpp"
#include "cflowfragmenttypes.hpp"
#include "cflowfragments.hpp"

#include "cflowmodule.hpp"



CDMControlFlowModule::CDMControlFlowModule() :
    Py::ExtensionModule< CDMControlFlowModule >( "cdmcf" )
{
    FragmentBase::Init();

    Fragment::InitType();
    BangLine::InitType();
//    FragmentWithComments::InitType();

    add_varargs_method( "Fragment",
                        &CDMControlFlowModule::createFragment,
                        CREATE_FRAGMENT_DOC );
    add_varargs_method( "BangLine",
                        &CDMControlFlowModule::createBangLine,
                        CREATE_BANGLINE_DOC );
//    add_varargs_method( "FragmentWithComments",
//                        &CDMControlFlowModule::createFragmentWithComments,
//                        "Creates the FragmentWithComments class instance" );

    // Free functions visible from the module
    add_varargs_method( "getControlFlowFromMemory",
                        &CDMControlFlowModule::getControlFlowFromMemory,
                        GET_CF_MEMORY_DOC );
    add_varargs_method( "getControlFlowFromFile",
                        &CDMControlFlowModule::getControlFlowFromFile,
                        GET_CF_FILE_DOC );


    initialize( MODULE_DOC );

    // Constants visible from the module
    Py::Dict        d( moduleDictionary() );
    d[ "VERSION" ]                  = Py::String( CDM_CF_PARSER_VERION );
    d[ "CML_VERSION" ]              = Py::String( CML_VERSION_AS_STRING );

    d[ "UNDEFINED_FRAGMENT" ]       = Py::Int( UNDEFINED_FRAGMENT );
    d[ "FRAGMENT" ]                 = Py::Int( FRAGMENT );
    d[ "BANG_LINE_FRAGMENT" ]       = Py::Int( BANG_LINE_FRAGMENT );
    d[ "ENCODING_LINE_FRAGMENT" ]   = Py::Int( ENCODING_LINE_FRAGMENT );
    d[ "COMMENT_FRAGMENT" ]         = Py::Int( COMMENT_FRAGMENT );
    d[ "FRAGMENT_WITH_COMMENTS" ]   = Py::Int( FRAGMENT_WITH_COMMENTS );
    d[ "DOCSTRING_FRAGMENT" ]       = Py::Int( DOCSTRING_FRAGMENT );
    d[ "DECORATOR_FRAGMENT" ]       = Py::Int( DECORATOR_FRAGMENT );
    d[ "CODEBLOCK_FRAGMENT" ]       = Py::Int( CODEBLOCK_FRAGMENT );
    d[ "FUNCTION_FRAGMENT" ]        = Py::Int( FUNCTION_FRAGMENT );
    d[ "CLASS_FRAGMENT" ]           = Py::Int( CLASS_FRAGMENT );
    d[ "BREAK_FRAGMENT" ]           = Py::Int( BREAK_FRAGMENT );
    d[ "CONTINUE_FRAGMENT" ]        = Py::Int( CONTINUE_FRAGMENT );
    d[ "RETURN_FRAGMENT" ]          = Py::Int( RETURN_FRAGMENT );
    d[ "RAISE_FRAGMENT" ]           = Py::Int( RAISE_FRAGMENT );
    d[ "ASSERT_FRAGMENT" ]          = Py::Int( ASSERT_FRAGMENT );
    d[ "SYSEXIT_FRAGMENT" ]         = Py::Int( SYSEXIT_FRAGMENT );
    d[ "WHILE_FRAGMENT" ]           = Py::Int( WHILE_FRAGMENT );
    d[ "FOR_FRAGMENT" ]             = Py::Int( FOR_FRAGMENT );
    d[ "IMPORT_FRAGMENT" ]          = Py::Int( IMPORT_FRAGMENT );
    d[ "IF_PART_FRAGMENT" ]         = Py::Int( IF_PART_FRAGMENT );
    d[ "IF_FRAGMENT" ]              = Py::Int( IF_FRAGMENT );
    d[ "WITH_FRAGMENT" ]            = Py::Int( WITH_FRAGMENT );
    d[ "EXCEPT_PART_FRAGMENT" ]     = Py::Int( EXCEPT_PART_FRAGMENT );
    d[ "TRY_FRAGMENT" ]             = Py::Int( TRY_FRAGMENT );
    d[ "CONTROL_FLOW_FRAGMENT" ]    = Py::Int( CONTROL_FLOW_FRAGMENT );

}


CDMControlFlowModule::~CDMControlFlowModule()
{}


Py::Object
CDMControlFlowModule::getControlFlowFromMemory( const Py::Tuple &  args )
{
    return Py::None();
}


Py::Object
CDMControlFlowModule::getControlFlowFromFile( const Py::Tuple &  args )
{
    return Py::None();
}

Py::Object  CDMControlFlowModule::createFragment( const Py::Tuple &  args )
{
    return Py::asObject( new Fragment() );
}

Py::Object  CDMControlFlowModule::createBangLine( const Py::Tuple &  args )
{
    return Py::asObject( new BangLine() );
}

//Py::Object createFragmentWithComments( const Py::Tuple &  args )
//{
//    return Py::asObject( new FragmentWithComments() );
//}




static CDMControlFlowModule *  CDMControlFlow;

extern "C" void initcdmcf()
{
    CDMControlFlow = new CDMControlFlowModule;
}

// symbol required for the debug version
extern "C" void initcdmcf_d()
{
    initcdmcf();
}


