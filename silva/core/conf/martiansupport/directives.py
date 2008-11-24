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

class extensionSystem(martian.MarkerDirective):
    scope = martian.MODULE
    store = martian.ONCE

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

from martian.directive import StoreMultipleTimes
from zope.interface.interface import TAGGED_DATA

class TaggedValueStoreMutipleTimes(StoreMultipleTimes):
    """Stores the directive value in a interface tagged value.
    """

    def get(self, directive, component, default):
        return component.queryTaggedValue(directive.dotted_name(), default)

    def set(self, locals_, directive, value):
        taggeddata = locals_.setdefault(TAGGED_DATA, {})
        if directive.dotted_name() in taggeddata:
            taggeddata[directive.dotted_name()].append(value)
        else:
            taggeddata[directive.dotted_name()] = [value, ]

    def setattr(self, context, directive, value):
        context.setTaggedValue(directive.dotted_name(), [value, ])


class resource(martian.Directive):
    scope = martian.CLASS
    store = TaggedValueStoreMutipleTimes()

from grokcore.component import name
from grokcore.component import title
from grokcore.component import context
from grokcore.view import skin
from grokcore.view import layer
from grokcore.viewlet import view
from grokcore.viewlet import viewletmanager
from grokcore.viewlet import order
