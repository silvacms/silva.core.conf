# Copyright (c) 2002-2010 Infrae. All rights reserved.
# See also LICENSE.txt
# $Id$

import os.path

from zope.configuration.name import resolve

from Products.SilvaMetadata.Compatibility import registerTypeForMetadata
from Products.Silva.ExtensionRegistry import extensionRegistry
from Products.FileSystemSite.DirectoryView import registerDirectory

from silva.core.conf.utils import ContentFactory, VersionedContentFactory
from silva.core.conf.utils import registerFactory, registerIcon, registerClass
from silva.core.conf.utils import VersionFactory, getProductMethods


def extension(_context, name, title, depends=(u"Silva",)):
    """The handler for the silva:extension directive.

    See .directives.IExtensionDirective

    Defers its implementation to registerExtension.
    """
    _context.action(
        discriminator=name,
        callable=registerExtension,
        args=(name, title, depends))


def registerExtension(name, title, depends):
    """Register a Silva extension.
    """
    try:
        install_module = resolve('Products.%s.install' % name)
    except ImportError:
        install_module = resolve('%s.install' % name)

    # since we don't pass in any modules for automatic class
    # registration, we don't need a context either
    if not depends:
        depends = None
    extensionRegistry.register(
        name, title, context=None, modules=[], install_module=install_module,
        depends_on=depends)

    extension = extensionRegistry.get_extension(name)
    extension_directory = os.path.dirname(install_module.__file__)
    if os.path.isdir(os.path.join(extension_directory, 'views')):
        registerDirectory('views', extension.module_directory)


def content(_context, extension_name, content, priority=0, icon=None,
            content_factory=None, zmi_addable=False):
    """The handler for the silva:content directive.

    See .directives.IContentDirective

    Defers its implementation to registerContent.
    """
    _context.action(
        discriminator=(content,),
        callable=registerContent,
        args=(extension_name, content, priority, icon, content_factory, zmi_addable),
        )

def registerContent(extension_name, content, priority, icon, content_factory, zmi_addable):
    """Register content type.
    """
    registerClass(content, extension_name, zmi_addable)

    extension = extensionRegistry.get_extension(extension_name)
    methods = getProductMethods(extension.module)

    if content_factory is None:
        content_factory = ContentFactory(content)

    registerFactory(methods, content, content_factory)

    registerIcon(extension_name, content, icon)
    # make sure we can add silva metadata to it
    registerTypeForMetadata(content.meta_type)
    # make it show up in the Silva addables list
    extensionRegistry.addAddable(content.meta_type, priority)

def versionedcontent(_context, extension_name, content, version, priority=0,
                     icon=None, content_factory=None, version_factory=None, zmi_addable=False):
    """The handler for the silva:versionedcontent directive.

    See .directives.IVersionedContentDirective

    Defers its implementation to registerVersionedContent.
    """
    _context.action(
        discriminator=(content, version),
        callable=registerVersionedContent,
        args=(extension_name, content, version, priority, icon,
              content_factory, version_factory, zmi_addable),
        )

def registerVersionedContent(extension_name, content, version, priority,
                             icon, content_factory, version_factory, zmi_addable):
    """Register a versioned content type and the implementation of its version.
    """

    registerClass(content, extension_name, zmi_addable)
    registerClass(version, extension_name, zmi_addable)

    extension = extensionRegistry.get_extension(extension_name)
    methods = getProductMethods(extension.module)

    if content_factory is None:
        content_factory = VersionedContentFactory(extension_name,
                                                  content, version)
    registerFactory(methods, content, content_factory)
    if version_factory is None:
        version_factory = VersionFactory(version)
    registerFactory(methods, version, version_factory)

    registerIcon(extension_name, content, icon)
    # make sure we can add silva metadata to it
    registerTypeForMetadata(version.meta_type)
    # make it show up in the Silva addables list
    extensionRegistry.addAddable(content.meta_type, priority)
