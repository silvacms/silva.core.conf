# Copyright (c) 2002-2010 Infrae. All rights reserved.
# See also LICENSE.txt
# $Id$

from martian.error import GrokError
import martian

from Products.Silva.Content import Content
from Products.Silva.Asset import Asset
from Products.Silva.Folder import Folder
from Products.Silva.VersionedContent import VersionedContent

from zope.configuration.name import resolve

from Products.SilvaMetadata.Compatibility import registerTypeForMetadata
from Products.Silva.ExtensionRegistry import extensionRegistry

from silva.core.services.base import ZMIObject
from silva.core.conf.utils import getProductMethods
from silva.core.conf.utils import ContentFactory, VersionFactory, \
    VersionedContentFactory, ServiceFactory
from silva.core.conf.utils import registerIcon, registerFactory, registerClass
from silva.core.interfaces import (
    IVersionedContent, ISilvaService, ISilvaLocalService)
from silva.core.conf.martiansupport import directives as silvaconf


class ZMIObjectGrokker(martian.ClassGrokker):
    """This grokker register new services and ZMI objects.
    """
    martian.component(ZMIObject)
    martian.directive(silvaconf.icon)
    martian.directive(silvaconf.factory)
    martian.priority(600)

    def _get_extension_name(self, content):
        """Lookup the name of the extension containing this class.
        """
        name = extensionRegistry.get_name_for_class(content)
        if name is None:
            raise GrokError(
                "Cannot find which to product belongs this content %s." % (
                    str(content)),
                content)
        return name

    def _get_extension_detail(self, content):
        """Lookup information for this content.
        """
        name = self._get_extension_name(content)
        product = extensionRegistry.get_extension(name).module
        methods = getProductMethods(product)
        return (name, methods)

    def _register_content(self, content, factories, default_factory,
                         icon, zmi_addable=True):
        """ Register the content in Zope.
        """
        menu_factory = None
        extension_name, methods = self._get_extension_detail(content)
        if not len(factories):
            if default_factory is None:
                raise GrokError(
                    "You need to provide a factory for %s." % content.__name__,
                    content)
            factories = [default_factory(content),]
        else:
            factories = map(
                lambda f: resolve('%s.%s' % (content.__module__, f)),
                factories)

        registerFactory(methods, content, factories)

        if zmi_addable:
            menu_factory = 'manage_addProduct/%s/%s' % (
                extension_name, factories[0].__name__)
        registerClass(content, extension_name, zmi_addable, menu_factory)

        if icon:
            registerIcon(extension_name, content, icon)

    def execute(self, content, icon, factory, **kw):
        """Register a Silva Service or a ZMIObject
        """
        default_factory = None
        zmi_addable = True
        if ISilvaService.implementedBy(content):
            default_factory = ServiceFactory
            zmi_addable = ISilvaLocalService.implementedBy(content)
        self._register_content(
            content, factory, default_factory, icon, zmi_addable)
        return True


class ContentBasedGrokker(ZMIObjectGrokker):
    """This grokker register all normal-based content.
    """
    martian.component(Content)
    martian.directive(silvaconf.priority)
    martian.directive(silvaconf.zmiAddable)

    def _register_contentInSilva(self, content, version, priority):
        """Register content in Silva.
        """
        # make sure we can add silva metadata to it
        registerTypeForMetadata(version.meta_type)
        # make it show up in the Silva addables list
        extensionRegistry.addAddable(content.meta_type, priority)

    def execute(self, content, icon, priority, factory, zmiAddable, **kw):
        """Register content type.
        """
        if IVersionedContent.implementedBy(content):
            return False
        self._register_content(content, factory, ContentFactory, icon, zmiAddable)
        self._register_contentInSilva(content, content, priority)
        return True


class AssetBasedGrokker(ContentBasedGrokker):
    martian.component(Asset)


class FolderBasedGrokker(ContentBasedGrokker):
    martian.component(Folder)


class VersionedContentBasedGrokker(ContentBasedGrokker):
    """Grokker for versioned content.
    """
    martian.component(VersionedContent)
    martian.directive(silvaconf.versionClass)
    martian.directive(silvaconf.versionFactory)

    def execute(self, content, icon, priority, factory,
                zmiAddable, versionClass, versionFactory, **kw):
        """Register a versioned content type and the implementation of
        its version.
        """
        if versionClass is None:
            # TODO we could search like grok search context
            raise GrokError(
                "You need to provide a version class for %s." % (
                    content.__name__),
                content)

        version = versionClass
        if isinstance(version, str):
            version = resolve('%s.%s' % (content.__module__, versionClass))
        extension = self._get_extension_name(content)
        defaultFactory = lambda c: VersionedContentFactory(
            extension, c, version)
        self._register_content(content, factory, defaultFactory, icon, zmiAddable)
        self._register_content(version, versionFactory, VersionFactory, None, zmiAddable)
        self._register_contentInSilva(content, version,  priority)
        return True
