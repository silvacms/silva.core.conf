# Copyright (c) 2002-2008 Infrae. All rights reserved.
# See also LICENSE.txt
# $Id$

import martian

from zope.configuration.name import resolve

from Products.Silva.ExtensionRegistry import extensionRegistry
from Products.Silva.upgrade import registry as upgradeRegistry
from Products.Silva.upgrade import BaseUpgrader
from Products.Silva.fssite import registerDirectory

from silva.core.conf.martiansupport import directives as silvaconf
from silva.core.conf.installer import SystemExtensionInstaller


import os.path

class ExtensionGrokker(martian.GlobalGrokker):
    """This grokker grok a module for an declaration of
    """

    martian.priority(800)

    def grok(self, name, module, module_info, config, **kw):

        get = lambda d: d.bind().get(module=module)

        ext_name = get(silvaconf.extensionName)
        ext_title = get(silvaconf.extensionTitle)
        
        if not ext_name or not ext_title:
            return False

        is_system = get(silvaconf.extensionSystem)
        ext_depends = get(silvaconf.extensionDepends)
        if is_system:
            install_module = SystemExtensionInstaller()
        else:
            install_module = resolve('%s.install' % name)

        extensionRegistry.register(ext_name,
                                   ext_title,
                                   context=None,
                                   modules=[],
                                   install_module=install_module,
                                   module_path=module_info.package_dotted_name,
                                   depends_on=ext_depends)

        if not is_system:
            extension = extensionRegistry.get_extension(ext_name)
            module_directory = extension.module_directory
            # Register Silva Views directory
            if os.path.exists(os.path.join(module_directory, 'views')):
                registerDirectory(module_directory, 'views')

        return True


class UpgradeGrokker(martian.InstanceGrokker):
    """This lookup Upgrade instance and register them.
    """

    martian.component(BaseUpgrader)
    martian.priority(200)

    def grok(self, name, instance, module_info, config, **kw):
        upgradeRegistry.registerUpgrader(instance)
        return True
