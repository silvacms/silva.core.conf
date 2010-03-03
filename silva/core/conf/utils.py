# Copyright (c) 2002-2010 Infrae. All rights reserved.
# See also LICENSE.txt
# $Id$

from AccessControl.PermissionRole import PermissionRole
from App.FactoryDispatcher import FactoryDispatcher
from App.ImageFile import ImageFile
from App.ProductContext import AttrDict
from OFS import misc_ as icons
import AccessControl.Permission
import Products

from zope.configuration.name import resolve
from zope.event import notify
from zope.interface import implementedBy
from zope.lifecycleevent import ObjectCreatedEvent
from zope.location.interfaces import ISite

from Products.Silva import mangle
from Products.Silva.icon import registry as icon_registry
from Products.Silva.helpers import makeZMIFilter
from Products.Silva.ExtensionRegistry import extensionRegistry
from silva.core import interfaces

import os.path

# Views utils

def getFiveViewNameFor(context):
    """Return the correct name for the view if you want to use a Five
    default one.
    """
    stack = [interfaces.IContainer,
             interfaces.IAsset,
             interfaces.IVersionedContent,
             interfaces.IContent]

    for interface in stack:
        if interface.providedBy(context):
            return 'Five %s' % interface.__name__[1:]


def getSilvaViewFor(context, view_type, obj):
    """Lookup a Silva view, fallback on a Five default one if it
    doesn't exists.
    """

    view_registry = context.service_view_registry
    try:
        # Try first the correct view
        return view_registry.get_view(view_type, obj.meta_type)
    except KeyError:
        # Not found, search default Five one.
        return view_registry.get_view(view_type, getFiveViewNameFor(obj))


# Default content factory

def ServiceFactory(factory):
    """A factory for Silva services.
    """
    service_interface = list(implementedBy(factory).interfaces())
    if not len(service_interface) or \
            interfaces.ISilvaService.extends(service_interface[0]):
        raise ValueError("Service %r doesn't implements a service interface" % (
                factory,))
    service_interface = service_interface[0]
    def factory_method(container, identifier, *args, **kw):
        service = factory(identifier)
        container._setObject(identifier, service)
        service = getattr(container, identifier)
        registerService(container, identifier, service, interface)
        notify(ObjectCreatedEvent(service))
        return service
    return factory_method


def ContentFactory(factory):
    """A factory for Content factories.

    This generates manage_add<Something> for non-versioned content types.
    """
    def factory_method(container, identifier, title, *args, **kw):
        identifier = mangle.Id(container, identifier)
        identifier.cook()
        if not identifier.isValid():
            return
        identifier = str(identifier)

        content = factory(identifier)
        container._setObject(identifier, content)
        content = getattr(container, identifier)
        content.set_title(title)
        notify(ObjectCreatedEvent(content))
        return content
    return factory_method


def VersionedContentFactory(extension_name, factory, version):
    """A factory for Versioned Content factories.

    This generates manage_add<Something> for versioned content types. It
    makes sure the first version is already added.
    """
    def factory_method(self, identifier, title, *args, **kw):
        container = self
        identifier = mangle.Id(container, identifier)
        identifier.cook()
        if not identifier.isValid():
            return
        identifier = str(identifier)

        content = factory(identifier)
        container._setObject(identifier, content)
        content = getattr(container, identifier)

        version_factory_name = getFactoryName(version)
        extension = extensionRegistry.get_extension(extension_name)

        version_factory = getattr(
            content.manage_addProduct[extension.product],
            version_factory_name)
        version_factory('0', title, *args, **kw)
        content.create_version('0', None, None)
        notify(ObjectCreatedEvent(content))
        return content
    return factory_method


def VersionFactory(version_factory):
    """A factory for Version factories.

    This generateas manage_add<Something>Version for versions.
    """
    def factory_method(self, identifier, title, *args, **kw):
        container = self
        version = version_factory(identifier, *args, **kw)
        container._setObject(identifier, version)
        version = container._getOb(identifier)
        version.set_title(title)
        notify(ObjectCreatedEvent(version))
        return version
    return factory_method


# Helpers

def getFactoryDispatcher(product):
    """Get the Factory Dispatcher, some Zope 2 magic.
    """
    fd = getattr(product, '__FactoryDispatcher__', None)
    if fd is None:
        class __FactoryDispatcher__(FactoryDispatcher):
            "Factory Dispatcher for a Specific Product"

        fd = product.__FactoryDispatcher__ = __FactoryDispatcher__
    return fd

def getProductMethods(product):
    """Get the methods dictionary for a product.

    This can be used to register product-level methods, such as factory
    functions like manage_addFoo.
    """
    try:
        return product._m
    except AttributeError:
        fd = getFactoryDispatcher(product)
        product._m = result = AttrDict(fd)
        return result

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
            raise BadRequest, "A service can only be created in a local site"
    else:
        site = context
    site._setObject(id, service)
    service = getattr(site, id)
    sm = site.getSiteManager()
    sm.registerUtility(service, interface)
    return service


def unregisterService(service, interface):
    """Unregister the service using the given interface.
    """
    site = service.aq_parent
    if not ISite.providedBy(site):
        raise ValueError, "Service parent is not a site."
    sm = ISite(site).getSiteManager()
    sm.unregisterUtility(service, interface)


#visibility can be "Global" or None
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
    pr = PermissionRole(permission, default)
    if isinstance(factory, tuple) or isinstance(factory, list):
        # just register the factories
        for method in factory:
            name = method.__name__
            if not name.startswith('manage_add'):
                name = getFactoryName(class_)
                module = resolve(class_.__module__)
                setattr(module, name, method)
            methods[name] = method
            methods[name + '__roles__'] = pr
    else:
        # only register this method, and save it in the module with a
        # good name to be imported.
        name = getFactoryName(class_)
        module = resolve(class_.__module__)
        setattr(module, name, factory)
        methods[name] = factory
        methods[name + '__roles__'] = pr

def registerIcon(extension_name, class_, icon):
    """Register icon for a class.
    """
    if not icon:
        return

    name = os.path.basename(icon)
    extension = extensionRegistry.get_extension(extension_name)
    icon = ImageFile(icon, extension.module_directory)
    icon.__roles__ = None
    if not hasattr(icons.misc_, extension_name):
        setattr(icons.misc_, extension_name,
                icons.Misc_(extension_name, {}))
    getattr(icons.misc_, extension_name)[name] = icon
    icon_path = 'misc_/%s/%s' % (extension_name, name)

    icon_registry._icon_mapping[('meta_type', class_.meta_type)] = icon_path
    class_.icon = icon_path

def cleanUp():
    global _meta_type_regs
    Products.meta_types = tuple([ info for info in Products.meta_types
                                  if info['name'] not in _meta_type_regs ])
    _meta_type_regs = []

from zope.testing.cleanup import addCleanUp
addCleanUp(cleanUp)
del addCleanUp
