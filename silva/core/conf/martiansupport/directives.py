# Copyright (c) 2008-2009 Infrae. All rights reserved.
# See also LICENSE.txt
# $Id$

import martian
from martian import priority
from martian import component
from martian import baseclass
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

