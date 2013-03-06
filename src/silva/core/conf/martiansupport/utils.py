# -*- coding: utf-8 -*-
# Copyright (c) 2011-2013 Infrae. All rights reserved.
# See also LICENSE.txt

import martian
from five import grok
from martian.directive import StoreMultipleTimes
from zope.interface.interface import TAGGED_DATA
from zope.interface import implementedBy
from zope.event import notify
from silva.core.interfaces import ISilvaService
from silva.core.interfaces.events import InstalledServiceEvent


def get_service_interface(factory, is_class=True):
    """Get service interface.
    """
    if not is_class:
        factory = factory.__class__
    provided = grok.provides.bind(get_default=lambda *x: None).get(factory)
    if provided is not None:
        return provided
    implemented = list(implementedBy(factory).interfaces())
    if (not len(implemented) or ISilvaService.extends(implemented[0])):
        raise ValueError(
            u"Service %r doesn't implements a service interface" % (
                factory,))
    return implemented[0]


class ServiceInfo(object):
    """Store information about the automatic creation of a service at
    installation time.
    """

    def __init__(self, public, name, setup):
        self.factory = None
        self.provided = None
        self.name = name
        self.public = public
        self.setup = setup

    def prepare(self, factory):
        """Prepare and validate the service parameters.
        """
        self.factory = factory
        if self.name is None:
            name = grok.name.bind().get(factory)
            if name is None:
                name = getattr(factory, 'default_service_identifier', None)
            self.name = name
        if self.public and self.name is None:
            raise martian.GrokError(
                u"Unnamed public services are not possible: %s" % self.factory)
        try:
            self.provided = get_service_interface(self.factory)
        except ValueError as e:
            raise martian.GrokError(e.args)

    def install(self, site, event):
        """Install the new default service.
        """
        manager = site.getSiteManager()
        utility = self.factory()
        if not self.public:
            manager[self.factory.__name__] = utility
        else:
            site._setObject(self.name, utility, suppress_events=True)
            utility = site._getOb(self.name)
        manager.registerUtility(utility, provided=self.provided)

        if self.setup is not None:
            self.setup(utility)

        notify(InstalledServiceEvent(utility))


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
