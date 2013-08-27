# -*- coding: utf-8 -*-
# Copyright (c) 2002-2013 Infrae. All rights reserved.
# See also LICENSE.txt

from grokcore.view.directive import  TaggedValueStoreOnce
from silva.core.conf.martiansupport.utils import ServiceInfo
from silva.core.conf.martiansupport.utils import TaggedValueStoreMutipleTimes
from silva.core.interfaces import IIcon
from zope.interface import Interface
from martian.util import not_unicode_or_ascii
from martian.error import GrokImportError
import martian


# Directives

class icon(martian.Directive):
    scope = martian.CLASS
    store = martian.ONCE
    default = None

    def validate(self, default, **optional):
        if not_unicode_or_ascii(default) and not IIcon.providedBy(default):
            raise GrokImportError(
                "The '%s' directive can only be called with "
                "unicode or ASCII." % self.name)
        for key, value in optional.items():
            if not_unicode_or_ascii(value) and not IIcon.providedBy(default):
                raise GrokImportError(
                    "The '%s' directive can only be called with "
                    "unicode or ASCII." % self.name)

    def factory(self, default, **optional):
        value = {None: default}
        value.update(optional)
        return value


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


class extension_default(martian.MarkerDirective):
    scope = martian.MODULE
    store = martian.ONCE


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


class default_service(martian.Directive):
    scope = martian.CLASS
    store = martian.ONCE_NOBASE

    def factory(self, name=None, public=True, setup=None):
        return ServiceInfo(public, name, setup)


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
