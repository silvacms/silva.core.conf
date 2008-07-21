# Copyright (c) 2002-2008 Infrae. All rights reserved.
# See also LICENSE.txt
# $Id$

import martian

from Products.Silva.Content import Content
from Products.Silva.Asset import Asset
from Products.Silva.Folder import Folder
from Products.Silva.Group import BaseGroup
from Products.Silva.VersionedContent import VersionedContent
from Products.Silva.BaseService import ZMIObject
from Products.Silva.interfaces import IVersionedContent

from zope.configuration.name import resolve

from Products.SilvaMetadata.Compatibility import registerTypeForMetadata
from Products.Silva.ExtensionRegistry import extensionRegistry

from silva.core.conf.utils import getProductMethods
from silva.core.conf.utils import ContentFactory, VersionFactory, VersionedContentFactory
from silva.core.conf.utils import registerIcon, registerFactory, registerClass

import silva.core.conf.martiansupport.directives as silvadirectives

    
class ZMIObjectGrokker(martian.ClassGrokker):
    """This grokker register new services and ZMI objects.
    """

    martian.component(ZMIObject)
    martian.directive(silvadirectives.icon)
    martian.directive(silvadirectives.factory)
    martian.priority(600)

    def _retrieveName(self, content):
        """Lookup the name of the extension containing this class.
        """
        name = extensionRegistry.get_name_for_class(content)
        if name is None:
            raise ValueError, "Cannot find which to product belongs this content"
        return name

    def _retrieveInfo(self, content):
        """Lookup information for this content.
        """
        name = self._retrieveName(content)
        product = extensionRegistry.get_product(name).module
        methods = getProductMethods(product)
        return (name, methods)

    def _registerContent(self, content, factories, default_factory,
                         icon, zmi_addable=False):
        """ Register the content in Zope.
        """
        menu_factory = None
        extension_name, methods = self._retrieveInfo(content)
        if not len(factories):
            if default_factory is None:
                msg = 'You need to provide a factory for %s'
                raise ValueError, msg % content.__name__
            zmi_addable = False
            factories = [default_factory(content),]
        else:
            if zmi_addable and factories[0].endswith('Form'):
                menu_factory = 'manage_addProduct/%s/%s' % (extension_name, factories[0])
            factories = map(lambda f: resolve('%s.%s' % (content.__module__, f)),
                            factories)

        registerClass(content, extension_name, zmi_addable, menu_factory)
        registerFactory(methods, content, factories)
        if icon:
            registerIcon(extension_name, content, icon)

    def execute(self, content, icon, factory, **kw):
        """Register a Silva Service or a ZMIObject
        """
        self._registerContent(content, factory, None, icon, True)
        return True


class ContentBasedGrokker(ZMIObjectGrokker):
    """This grokker register all normal-based content.
    """

    martian.component(Content)
    martian.directive(silvadirectives.priority)

    def _registerContentInSilva(self, content, version, priority):    
        """Register content in Silva.
        """
        # make sure we can add silva metadata to it
        registerTypeForMetadata(version.meta_type)
        # make it show up in the Silva addables list
        extensionRegistry.addAddable(content.meta_type, priority)

    def execute(self, content, icon, priority, factory, **kw):
        """Register content type.
        """
        if IVersionedContent.implementedBy(content):
            return False
        self._registerContent(content, factory, ContentFactory, icon)
        self._registerContentInSilva(content, content, priority)
        return True
    

class AssetBasedGrokker(ContentBasedGrokker):
    martian.component(Asset)


class FolderBasedGrokker(ContentBasedGrokker):
    martian.component(Folder)


class GroupBasedGrokker(ContentBasedGrokker):
    martian.component(BaseGroup)


class VersionedContentBasedGrokker(ContentBasedGrokker):
    """Grokker for versioned content.
    """

    martian.component(VersionedContent)
    martian.directive(silvadirectives.versionClass)
    martian.directive(silvadirectives.versionFactory)

    def execute(self, content, icon, priority, factory, versionClass,
                versionFactory, **kw):
        """Register a versioned content type and the implementation of
        its version.
        """
        if versionClass is None:
            msg = 'You need to provide a version class (versionClass) for %s'
            raise ValueError, msg % content.__name__

        version = resolve('%s.%s' % (content.__module__, versionClass))
        extension = self._retrieveName(content)
        defaultFactory = lambda c: VersionedContentFactory(extension, c, version)
        self._registerContent(content, factory, defaultFactory, icon)
        self._registerContent(version, versionFactory, VersionFactory, None)
        self._registerContentInSilva(content, version,  priority)
        return True
