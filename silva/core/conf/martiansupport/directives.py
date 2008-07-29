# Copyright (c) 2002-2008 Infrae. All rights reserved.
# See also LICENSE.txt
# $Id$

import martian

class icon(martian.Directive):
    scope = martian.CLASS
    store = martian.ONCE
    default = None
    validate = martian.validateText

class factory(martian.Directive):
    scope = martian.CLASS
    store = martian.MULTIPLE_NOBASE
    default = []

class versionClass(martian.Directive):
    scope = martian.CLASS
    store = martian.ONCE
    default = None

class versionFactory(martian.Directive):
    scope = martian.CLASS
    store = martian.MULTIPLE_NOBASE
    default = []

from martian import priority
from martian import component
from martian import baseclass

class extensionName(martian.Directive):
    scope = martian.MODULE
    store = martian.ONCE
    default = u""
    validate = martian.validateText

class extensionTitle(martian.Directive):
    scope = martian.MODULE
    store = martian.ONCE
    default = u""
    validate = martian.validateText
    
class extensionDepends(martian.Directive):
    scope = martian.MODULE
    store = martian.ONCE
    default = u"Silva"

class XSLT(martian.Directive):
    scope = martian.CLASS
    store = martian.ONCE
    default = None
    validate = martian.validateText

class namespace(martian.Directive):
    scope = martian.CLASS_OR_MODULE
    store = martian.ONCE
    default = None
    validate = martian.validateText

from grokcore.component import name
from grokcore.component import title
from grokcore.component import context
