# Copyright (c) 2002-2009 Infrae. All rights reserved.
# See also LICENSE.txt
# $Id$

from martian.error import GrokError
import martian

from zope.interface import alsoProvides
from zope.configuration.name import resolve

from Products.Silva.ExtensionRegistry import extensionRegistry
from Products.Silva.fssite import registerDirectory

from silva.core.conf.martiansupport import directives as silvaconf
from silva.core.conf.installer import SystemExtensionInstaller
from silva.core.interfaces import ISystemExtension

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

        if not module_info.isPackage():
            raise GrokError(
                "Your extension %s is not defined in a package." % ext_title,
                module)

        is_system = get(silvaconf.extensionSystem)
        ext_depends = get(silvaconf.extensionDepends)
        if is_system:
            install_module = SystemExtensionInstaller()
        else:
            try:
                install_module = resolve('%s.install' % name)
            except ImportError:
                raise GrokError(
                    "You need to define an installer for your extension %s." % ext_title, module)

        extensionRegistry.register(ext_name,
                                   ext_title,
                                   context=None,
                                   modules=[],
                                   install_module=install_module,
                                   module_path=module_info.package_dotted_name,
                                   depends_on=ext_depends)

        extension = extensionRegistry.get_extension(ext_name)
        if is_system:
            alsoProvides(extension, ISystemExtension)
        else:
            module_directory = extension.module_directory
            # Register Silva Views directory
            if os.path.exists(os.path.join(module_directory, 'views')):
                registerDirectory('views', module_directory)

        return True

