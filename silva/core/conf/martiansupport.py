# Copyright (c) 2002-2008 Infrae. All rights reserved.
# See also LICENSE.txt
# $Id$

import martian
import martiandirectives as silvadirectives

from Products.Silva.Content import Content
from Products.Silva.Asset import Asset
from Products.Silva.Folder import Folder
from Products.Silva.Group import BaseGroup
from Products.Silva.VersionedContent import VersionedContent
from Products.Silva.BaseService import ZMIObject
from Products.Silva import upgrade as silvaupgrade
from Products.Silva.interfaces import IVersionedContent
from Products.Silva.transform.renderer.xsltrendererbase import XSLTRendererBase
from Products.Silva.transform.rendererreg import getRendererRegistry

from zope.configuration.name import resolve

from Products.SilvaMetadata.Compatibility import registerTypeForMetadata
from Products.Silva.ExtensionRegistry import extensionRegistry
from Products.Silva.silvaxml import xmlimport
from Products.Silva.fssite import registerDirectory

from handlers import getProductMethods
from handlers import ContentFactory, VersionFactory, VersionedContentFactory
from handlers import registerIcon, registerFactory, registerClass

try:
    import lxml
    NO_XSLT = False
except ImportError:
    NO_XSLT = True


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

    martian.component(silvaupgrade.BaseUpgrader)
    martian.priority(200)

    def grok(self, name, instance, module_info, config, **kw):
        silvaupgrade.registry.registerUpgrader(instance)
        return True


class XSLTRendererGrokker(martian.ClassGrokker):
    """This lookup XSLTRenderer and register them.
    """

    martian.component(XSLTRendererBase)
    martian.directive(silvadirectives.title)
    martian.directive(silvadirectives.metaType)
    martian.directive(silvadirectives.XSLT)
    martian.priority(200)

    def grok(self, name, class_, module_info, config, **kw):
        if NO_XSLT:
            return False

        module = None
        values = {}
        if module_info is not None:
            module = module_info.getModule()

        for d in martian.directive.bind().get(self.__class__):
            values[d.name] = d.get(class_, module, **kw)

        registry = getRendererRegistry()
        renderer = class_(values['XSLT'], module_info.path)
        registry.registerRenderer(values['metaType'],
                                  values['title'],
                                  renderer)
        return True


class XMLImporterGrokker(martian.ClassGrokker):
    """Collect importer for contents.
    """

    martian.component(xmlimport.SilvaBaseHandler)
    martian.directive(silvadirectives.namespace)
    martian.directive(silvadirectives.name)
    martian.priority(200)

    def execute(self, importer, namespace, name=None, **kw):
        if name is None:
            return False
        xmlimport.theXMLImporter.registerHandler((namespace, name), importer)
        return True

    
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
                raise ValueError, 'you have to provide a factory'
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
        version = resolve('%s.%s' % (content.__module__, versionClass))
        extension = self._retrieveName(content)
        defaultFactory = lambda c: VersionedContentFactory(extension, c, version)
        self._registerContent(content, factory, defaultFactory, icon)
        self._registerContent(version, versionFactory, VersionFactory, None)
        self._registerContentInSilva(content, version,  priority)
        return True
