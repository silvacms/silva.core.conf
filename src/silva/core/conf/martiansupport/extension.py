# Copyright (c) 2002-2010 Infrae. All rights reserved.
# See also LICENSE.txt
# $Id$

from martian.error import GrokError
import martian

from zope import component
from zope.configuration.name import resolve
from zope.interface import alsoProvides

from Products.Silva.ExtensionRegistry import extensionRegistry

from silva.core.conf.installer import SystemExtensionInstaller
from silva.core.conf.martiansupport import directives as silvaconf
from silva.core.interfaces import IRoot
from silva.core.interfaces import ISystemExtension
from silva.core.interfaces.events import IInstallRootEvent


def install(name):

    def installer(root, event):
        extensionRegistry.install(name, root)

    return installer


class ExtensionGrokker(martian.GlobalGrokker):
    """This grokker grok a module for an declaration of
    """
    martian.priority(800)

    def grok(self, name, module, module_info, config, **kw):
        get = lambda d: d.bind().get(module)

        ext_name = get(silvaconf.extension_name)
        ext_title = get(silvaconf.extension_title)

        if not ext_name or not ext_title:
            return False

        if not module_info.isPackage():
            raise GrokError(
                "Your extension %s is not defined in a package." % ext_title,
                module)

        is_system = get(silvaconf.extension_system)
        is_default = get(silvaconf.extension_default)
        ext_depends = get(silvaconf.extension_depends)
        if is_system:
            if is_default:
                raise GrokError(
                    u"System extension %s doesn't have an installer. "
                    u"So you cannot install it by default." % ext_title)
            install_module = SystemExtensionInstaller()
        else:
            try:
                install_module = resolve('%s.install' % name)
            except ImportError:
                raise GrokError(
                    u"You need to define an installer for your extension %s." % (
                        ext_title))

        extensionRegistry.register(
            ext_name,
            ext_title,
            context=None,
            modules=[],
            install_module=install_module,
            module_path=module_info.package_dotted_name,
            depends_on=ext_depends)

        extension = extensionRegistry.get_extension(ext_name)
        if is_system:
            alsoProvides(extension, ISystemExtension)
        if is_default:
            config.action(
                discriminator=None,
                callable=component.provideHandler,
                args=(install(ext_name), (IRoot, IInstallRootEvent)))
        return True

