# Copyright (c) 2002-2010 Infrae. All rights reserved.
# See also LICENSE.txt
# $Id$

from zope import interface, component

from silva.core.interfaces import IRegistry

class Registry(object):
    """Base class for registry.
    """

    interface.implements(IRegistry)


def getRegistry(name):
    return component.queryUtility(IRegistry, name=name)
