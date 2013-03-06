# -*- coding: utf-8 -*-
# Copyright (c) 2002-2013 Infrae. All rights reserved.
# See also LICENSE.txt

from martian.error import GrokError
import martian

from zope.configuration.name import resolve

from Products.Silva.Publishable import NonPublishable
from Products.Silva.Content import Content
from Products.Silva.ExtensionRegistry import extensionRegistry
from Products.Silva.Folder import Folder
from Products.Silva.VersionedContent import VersionedObject

from silva.core.conf.martiansupport import directives as silvaconf
from silva.core.conf.utils import ContentFactory, VersionFactory
from silva.core.conf.utils import VersionedContentFactory, ServiceFactory
from silva.core.conf.utils import getProductMethods
from silva.core.conf.utils import registerIcon, registerFactory, registerClass
from silva.core.interfaces import ISilvaService, ISilvaLocalService
from silva.core.interfaces import IVersionedObject
from silva.core.services.base import ZMIObject


class ZMIObjectGrokker(martian.ClassGrokker):
    """This grokker register new services and ZMI objects.
    """
    martian.component(ZMIObject)
    martian.directive(silvaconf.icon)
    martian.directive(silvaconf.factory)
    martian.directive(silvaconf.zmi_addable)
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

    def _register_content(
        self, config, content, factories, default_factory, icon,
        zmi_addable=True):
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
            registerIcon(config, extension_name, content, icon[None])

    def execute(
        self, content, config, icon, factory, zmi_addable, **kw):
        """Register a Silva Service or a ZMIObject
        """
        default_factory = None
        if ISilvaService.implementedBy(content):
            default_factory = ServiceFactory
            zmi_addable = ISilvaLocalService.implementedBy(content)
        self._register_content(
            config, content, factory, default_factory, icon, zmi_addable)
        return True


class ContentBasedGrokker(ZMIObjectGrokker):
    """This grokker register all normal-based content.
    """
    martian.component(Content)
    martian.directive(silvaconf.priority)
    martian.directive(silvaconf.zmi_addable)

    def _register_silva(self, content, priority, version=None):
        """Register content in Silva.
        """
        # make it show up in the Silva addables list
        content = content.meta_type
        if version is not None:
            version = version.meta_type
        extensionRegistry.add_addable(content, priority, version)

    def execute(
        self, content, config, icon, priority, factory, zmi_addable, **kw):
        """Register content type.
        """
        if IVersionedObject.implementedBy(content):
            return False
        self._register_content(
            config, content, factory, ContentFactory, icon, zmi_addable)
        self._register_silva(content, priority)
        return True


class NonPublishableBasedGrokker(ContentBasedGrokker):
    martian.component(NonPublishable)


class FolderBasedGrokker(ContentBasedGrokker):
    martian.component(Folder)


class VersionedContentBasedGrokker(ContentBasedGrokker):
    """Grokker for versioned content.
    """
    martian.component(VersionedObject)
    martian.directive(silvaconf.version_class)
    martian.directive(silvaconf.version_factory)

    def execute(
        self, content, config, icon, priority, factory,
        zmi_addable, version_class, version_factory, **kw):
        """Register a versioned content type and the implementation of
        its version.
        """
        if version_class is None:
            # TODO we could search like grok search context
            raise GrokError(
                "You need to provide a version class for %s." % (
                    content.__name__),
                content)

        version = version_class
        if isinstance(version, str):
            version = resolve('%s.%s' % (content.__module__, version_class))
        extension = self._get_extension_name(content)
        default_factory = lambda c: VersionedContentFactory(extension, c, version)
        self._register_content(
            config, content, factory, default_factory, icon, zmi_addable)
        self._register_content(
            config, version, version_factory, VersionFactory, None, zmi_addable)
        self._register_silva(
            content, priority,  version)
        return True
