# -*- coding: utf-8 -*-
# Copyright (c) 2002-2013 Infrae. All rights reserved.
# See also LICENSE.txt

from zope.interface.interface import InterfaceClass
from zope.component.interface import provideInterface
from silva.core.interfaces import ISilvaObject, IViewableObject

import martian


class InterfaceGrokker(martian.InstanceGrokker):
    """We register content interfaces so we can lookup them afterwards.
    """
    martian.component(InterfaceClass)

    def grok(self, name, interface, module_info, config, **kw):
        if (interface.extends(ISilvaObject) or
            interface.extends(IViewableObject)):
            config.action(
                discriminator=None,
                callable=provideInterface,
                args=('', interface))
            return True

        return False



