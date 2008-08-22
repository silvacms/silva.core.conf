# Copyright (c) 2002-2008 Infrae. All rights reserved.
# See also LICENSE.txt
# $Id$

from zope.interface.interface import InterfaceClass
from zope.component.interface import provideInterface

from Products.SilvaLayout.interfaces import ISilvaLayer, ISilvaSkin
from silva.core.layout.interfaces import ICustomizableType, ICustomizable
from silva.core.layout.interfaces import ILayerType

import martian

class SilvaInterfaceGrokker(martian.InstanceGrokker):
    """We register interfaces than people can customize as utility on
    ISilvaCustomizable.
    """

    martian.component(InterfaceClass)

    def grok(self, name, interface, module_info, config, **kw):

        if interface.extends(ICustomizable):
            config.action(
                discriminator=('utility', ICustomizableType, interface),
                callable=provideInterface,
                args=('', interface, ICustomizableType))
            return True
        if interface.isOrExtends(ISilvaLayer) and not interface.isOrExtends(ISilvaSkin):
            config.action(
                discriminator=('utility', ILayerType, interface),
                callable=provideInterface,
                args=('', interface, ILayerType))
            return True
        return False

                

