# -*- coding: utf-8 -*-
# Copyright (c) 2002-2013 Infrae. All rights reserved.
# See also LICENSE.txt

from AccessControl.PermissionRole import PermissionRole
from Acquisition import aq_base
from App.FactoryDispatcher import FactoryDispatcher
from App.ProductContext import AttrDict
from AccessControl import ClassSecurityInfo
from App.class_init import InitializeClass
from OFS.interfaces import IObjectWillBeRemovedEvent
from zExceptions import BadRequest
import AccessControl.Permission
import Products

from five import grok
from zope.component import provideAdapter
from zope.configuration.name import resolve
from zope.event import notify
from zope.interface import implementedBy, Interface, implements
from zope.lifecycleevent import ObjectCreatedEvent
from zope.location.interfaces import ISite
from zope.publisher.interfaces.browser import IHTTPRequest

from Products.Silva.icon import Icon
from Products.Silva.icon import registry as icon_registry
from Products.Silva.ExtensionRegistry import extensionRegistry
from Products.Five.browser.resource import ImageResourceFactory
from silva.core import interfaces
from silva.core.interfaces import ISilvaNameChooser, IIcon
from silva.core.interfaces.events import ContentCreatedEvent
from silva.core.interfaces.errors import ContentError
from silva.core.conf.martiansupport.utils import get_service_interface
from silva.core.services.base import get_service_id

import os.path


class ISilvaFactoryDispatcher(Interface):
    pass


def normalize_identifier(identifier):
    if isinstance(identifier, unicode):
        return identifier.encode('utf-8')
    return identifier


# Default content factory

def ServiceFactory(factory):
    """A factory for Silva services.
    """
    service_interface = get_service_interface(factory)
    def factory_method(container, identifier=None, REQUEST=None, *args, **kw):
        """Create a instance of that service, callable through the web.
        """
        identifier = get_service_id(factory, identifier)
        identifier = normalize_identifier(identifier)
        if identifier is None:
            raise ValueError("No id for the new service")
        service = factory(identifier, *args, **kw)
        service = registerService(
            container, identifier, service, service_interface)
        notify(ObjectCreatedEvent(service))
        if REQUEST is not None:
            REQUEST.response.redirect(
                service.absolute_url() + '/manage_workspace')
            return ''
        else:
            return service
    return factory_method


def ContentFactory(factory):
    """A factory for Content factories.

    This generates manage_add<Something> for non-versioned content types.
    """
    def factory_method(
        container, identifier, title, no_default_content=False, *args, **kw):
        if ISilvaFactoryDispatcher.providedBy(container):
            container = container.Destination()
        identifier = normalize_identifier(identifier)
        chooser = ISilvaNameChooser(container)
        try:
            chooser.checkName(
                identifier, None, interface=implementedBy(factory))
        except ContentError as e:
            raise ValueError(e.reason)
        content = factory(identifier)
        setattr(content, '__initialization__', True)
        container._setObject(identifier, content)
        content = container._getOb(identifier)
        content.set_title(title)
        for key, value in kw.items():
            if hasattr(aq_base(content), 'set_%s' % key):
                setter = getattr(content, 'set_%s' % key)
                setter(value)
            elif hasattr(aq_base(content), key):
                setattr(content, key, value)
        delattr(content, '__initialization__')
        notify(ContentCreatedEvent(
                content, no_default_content=no_default_content))
        return content
    return factory_method


def VersionedContentFactory(extension_name, factory, version):
    """A factory for Versioned Content factories.

    This generates manage_add<Something> for versioned content types. It
    makes sure the first version is already added.
    """
    def factory_method(
        container, identifier, title, no_default_version=False, *args, **kw):
        if ISilvaFactoryDispatcher.providedBy(container):
            container = container.Destination()
        identifier = normalize_identifier(identifier)
        chooser = ISilvaNameChooser(container)
        try:
            chooser.checkName(
                identifier, None, interface=implementedBy(factory))
        except ContentError as e:
            raise ValueError(e.reason)
        content = factory(identifier)
        setattr(content, '__initialization__', True)
        container._setObject(identifier, content)
        content = container._getOb(identifier)

        if no_default_version is False:
            version_factory_name = getFactoryName(version)
            extension = extensionRegistry.get_extension(extension_name)

            content.create_version('0', None, None)
            version_factory = getattr(
                content.manage_addProduct[extension.product],
                version_factory_name)
            version_factory('0', title, *args, **kw)

        delattr(content, '__initialization__')
        notify(ContentCreatedEvent(
                content, no_default_version=no_default_version))
        return content
    return factory_method


def VersionFactory(version_factory):
    """A factory for Version factories.

    This generateas manage_add<Something>Version for versions.
    """
    def factory_method(container, identifier, title, *args, **kw):
        if ISilvaFactoryDispatcher.providedBy(container):
            container = container.Destination()
        version = version_factory(identifier)
        setattr(version, '__initialization__', True)
        container._setObject(identifier, version)
        version = container._getOb(identifier)
        if title is not None:
            version.set_title(title)
        for key, value in kw.items():
            if hasattr(aq_base(version), 'set_%s' % key):
                setter = getattr(version, 'set_%s' % key)
                setter(value)
            elif hasattr(aq_base(version), key):
                setattr(version, key, value)
        delattr(version, '__initialization__')
        notify(ObjectCreatedEvent(version))
        return version
    return factory_method


# Helpers

def makeZMIFilter(content, zmi_addable=True):
    """
    You can add:

    1. A Silva Root not inside a Silva Root
    2. A local Silva service in a local site.
    3. A ZMI object anywhere inside a Silva Root.
    4. A Silva Object in a Silva Container.
    5. A Version in a VersionedObject.
    """

    def SilvaZMIFilter(container, filter_addable=False):
        if filter_addable and not zmi_addable:
            return False
        try:
            inside_silva = interfaces.IRoot.providedBy(container.get_root())
        except AttributeError:
            inside_silva = False
        if not inside_silva:
            # Outsite of Silva, you can only add a Silva Root.
            return interfaces.IRoot.implementedBy(content)

        if interfaces.IZMIObject.implementedBy(content):
            if interfaces.ISilvaLocalService.implementedBy(content):
                # Add local service in a site.
                return ISite.providedBy(container)
            # ZMIObject are addable, but not the non-local services
            # (they must be installed).
            return not interfaces.ISilvaService.implementedBy(content)

        if interfaces.IRoot.implementedBy(content):
            # Silva Root are not addable inside Silva.
            return False

        if interfaces.IContainer.providedBy(container):
            # In a Container, you can add content.
            return interfaces.ISilvaObject.implementedBy(content)

        if interfaces.IVersionedObject.providedBy(container):
            # In a Versioned object, you can add version.
            return interfaces.IVersion.implementedBy(content)

        return False
    return SilvaZMIFilter


def getFactoryDispatcher(product):
    """Get the Factory Dispatcher, some Zope 2 magic.
    """
    factories = getattr(product, '__FactoryDispatcher__', None)
    if factories is None:
        class __FactoryDispatcher__(FactoryDispatcher):
            """Factory Dispatcher for a Specific Product
            """
            implements(ISilvaFactoryDispatcher)

        factories = product.__FactoryDispatcher__ = __FactoryDispatcher__
    return factories

def getProductMethods(product):
    """Get the methods dictionary for a product.

    This can be used to register product-level methods, such as factory
    functions like manage_addFoo.
    """
    try:
        return product._m
    except AttributeError:
        factories = getFactoryDispatcher(product)
        product._m = AttrDict(factories)
        return product._m

def getAddPermissionName(class_):
    return 'Add %ss' % class_.meta_type

def getFactoryName(class_):
    return 'manage_add' + class_.__name__


# for use in test cleanup
_meta_type_regs = []

# Registration methods
def registerService(context, id, service, interface):
    """Set and register the service id, using interface.
    """
    if not ISite.providedBy(context.aq_base):
        site = context.Destination()
        if not ISite.providedBy(site):
            raise BadRequest("A service can only be created in a local site")
    else:
        site = context
    site._setObject(id, service)
    service = site._getOb(id)
    sm = site.getSiteManager()
    sm.registerUtility(service, interface)
    return service


def unregisterService(service, interface):
    """Unregister the service using the given interface.
    """
    site = service.aq_parent
    if not ISite.providedBy(site):
        raise ValueError("Service parent is not a site.")
    sm = ISite(site).getSiteManager()
    sm.unregisterUtility(service, interface)


@grok.subscribe(interfaces.ISilvaService, IObjectWillBeRemovedEvent)
def unregisterByDefaultServices(service, event):
    interface = get_service_interface(service, is_class=False)
    unregisterService(service, interface)


def registerClass(class_, extension_name, zmi_addable=False,
                  default_action=None):
    """Register a class with Zope as a type.
    """
    permission = getAddPermissionName(class_)
    interfaces = list(implementedBy(class_))

    if default_action is None:
        default_action = 'manage_main'

    #There are two ways to remove this object from the list,
    #by either specifying "visibility: none", in which case
    #the object is never visible (and copy support is broken)
    #or by specifying a container_filter, which can return true
    #if the container is an ISilvaObject.  I'm opting for the latter,
    #as at least the objects aren't addable from outside the Silva Root then.
    #Also, Products.Silva.Folder will override ObjectManager.filtered_meta_types
    #to also remove any ISilvaObject types from the add list
    info = {'name': class_.meta_type,
            'action': default_action,
            'product': extension_name,
            'permission': permission,
            'visibility': "Global",
            'interfaces': interfaces,
            'instance': class_,
            'container_filter': makeZMIFilter(class_, zmi_addable)
            }
    Products.meta_types += (info,)
 
    # register for test cleanup
    _meta_type_regs.append(class_.meta_type)

def registerFactory(methods, class_, factory):
    """Register a manage_add<Something> style factory method.
    """
    permission = getAddPermissionName(class_)
    default = ('Manager',)
    AccessControl.Permission.registerPermissions(((permission, (), default),))
    permission_setting = PermissionRole(permission, default)
    if not (isinstance(factory, tuple) or isinstance(factory, list)):
        factory = [factory,]
    for method in factory:
        name = method.__name__
        if not name.startswith('manage_add'):
            method.__name__ = name = getFactoryName(class_)
            module = resolve(class_.__module__)
            setattr(module, name, method)
        methods[name] = method
        methods[name + '__roles__'] = permission_setting


# Icon handling


class IconResource(ImageResourceFactory.resource):
    """An icon is a publicly available image.
    """
    security = ClassSecurityInfo()
    security.declarePublic('__call__')

InitializeClass(IconResource)


class IconResourceFactory(ImageResourceFactory):
    resource = IconResource


def registerIcon(config, extension_name, cls, icon):
    """Register icon for a class.
    """
    if icon is None:
        return

    if not IIcon.providedBy(icon):
        extension = extensionRegistry.get_extension(extension_name)
        fs_path = os.path.join(extension.module_directory, icon)
        name = ''.join((
                'icon-',
                cls.meta_type.strip().replace(' ', '-'),
                os.path.splitext(icon)[1] or '.png'))

        factory = IconResourceFactory(name, fs_path)
        config.action(
            discriminator = ('resource', name, IHTTPRequest, Interface),
            callable = provideAdapter,
            args = (factory, (IHTTPRequest,), Interface, name))

        icon = Icon("++resource++" + name)

    icon_registry.register(('meta_type', cls.meta_type), icon)
    cls.icon = icon.icon


def cleanUp():
    global _meta_type_regs
    Products.meta_types = tuple([ info for info in Products.meta_types
                                  if info['name'] not in _meta_type_regs ])
    _meta_type_regs = []

try:
    from infrae.testing import layerCleanUp
except ImportError:
    pass
else:
    layerCleanUp.add(cleanUp)
