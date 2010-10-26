# Copyright (c) 2002-2010 Infrae. All rights reserved.
# See also LICENSE.txt
# $Id$

from grokcore.view.directive import  TaggedValueStoreOnce
from martian.directive import StoreMultipleTimes
from zope.interface import Interface
from zope.interface.interface import TAGGED_DATA
import martian


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

# Directives

class icon(martian.Directive):
    scope = martian.CLASS
    store = martian.ONCE
    default = None
    validate = martian.validateText


class factory(martian.Directive):
    scope = martian.CLASS
    store = martian.MULTIPLE_NOBASE
    default = []


class version_class(martian.Directive):
    scope = martian.CLASS
    store = martian.ONCE
    default = None


class version_factory(martian.Directive):
    scope = martian.CLASS
    store = martian.MULTIPLE_NOBASE
    default = []


class zmi_addable(martian.Directive):
    scope = martian.CLASS
    store = martian.ONCE
    default = False


class extension_name(martian.Directive):
    scope = martian.MODULE
    store = martian.ONCE
    default = u""
    validate = martian.validateText


class extension_title(martian.Directive):
    scope = martian.MODULE
    store = martian.ONCE
    default = u""
    validate = martian.validateText


class extension_depends(martian.Directive):
    scope = martian.MODULE
    store = martian.ONCE
    default = u"Silva"


class extension_system(martian.MarkerDirective):
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


class only_for(martian.Directive):
    """The purpose of this directive is a bit like grok.context, but
    it is used on interfaces.
    """
    scope = martian.CLASS
    store = TaggedValueStoreOnce()
    default = Interface
    validate = martian.validateInterfaceOrClass


class resource(martian.Directive):
    scope = martian.CLASS
    store = TaggedValueStoreMutipleTimes()



# BBB
versionClass = version_class
versionFactory = version_factory
zmiAddable = zmi_addable
extensionName = extension_name
extensionTitle = extension_title
extensionDepends = extension_depends
extensionSystem = extension_system

# Grok API
from martian import priority
from martian import component
from martian import baseclass
from grokcore.component import name
from grokcore.component import title
from grokcore.component import context
from grokcore.view import skin
from grokcore.view import layer
from grokcore.viewlet import view
from grokcore.viewlet import viewletmanager
from grokcore.viewlet import order
