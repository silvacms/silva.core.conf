# Copyright (c) 2002-2010 Infrae. All rights reserved.
# See also LICENSE.txt
# $Id$

import martian

from zope import component

from silva.core.conf import registry

class RegistryGrokker(martian.InstanceGrokker):

    martian.component(registry.Registry)

    def grok(self, name, instance, module_info, config, **kw):
        name = name.lower()
        config.action(
            discriminator = ('utility', registry.IRegistry, name),
            callable = component.provideUtility,
            args = (instance, registry.IRegistry, name),
            )
        return True


