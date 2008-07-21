# Copyright (c) 2002-2008 Infrae. All rights reserved.
# See also LICENSE.txt
# $Id$

import martian

from zope.configuration.name import resolve

from Products.Silva.ExtensionRegistry import extensionRegistry
from Products.Silva.upgrade import registry as upgradeRegistry
from Products.Silva.upgrade import BaseUpgrader
from Products.Silva.fssite import registerDirectory

import silva.core.conf.martiansupport.directives as silvadirectives

class ExtensionGrokker(martian.GlobalGrokker):
    """This grokker grok a module for an declaration of
    """

    martian.priority(800)

    def grok(self, name, module, module_info, config, **kw):

        get = lambda d: d.bind().get(module=module)

        ext_name = get(silvadirectives.extensionName)
        ext_title = get(silvadirectives.extensionTitle)
        
        if not ext_name or not ext_title:
            return False

        install_module = resolve('%s.install' % name)
        ext_depends = get(silvadirectives.extensionDepends)
        
        extensionRegistry.register(ext_name,
                                   ext_title,
                                   context=None,
                                   modules=[],
                                   install_module=install_module,
                                   depends_on=ext_depends)

        extension = extensionRegistry.get_product(ext_name)
        registerDirectory('views', extension.module_directory)

        return True


class UpgradeGrokker(martian.InstanceGrokker):
    """This lookup Upgrade instance and register them.
    """

    martian.component(BaseUpgrader)
    martian.priority(200)

    def grok(self, name, instance, module_info, config, **kw):
        upgradeRegistry.registerUpgrader(instance)
        return True
