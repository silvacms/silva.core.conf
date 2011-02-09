# Copyright (c) 2002-2010 Infrae. All rights reserved.
# See also LICENSE.txt
# $Id$

from AccessControl.PermissionRole import PermissionRole
from Acquisition import aq_base
from App.FactoryDispatcher import FactoryDispatcher
from App.ImageFile import ImageFile
from App.ProductContext import AttrDict
from OFS import misc_ as icons
from OFS.interfaces import IObjectWillBeRemovedEvent
from zExceptions import BadRequest
import AccessControl.Permission
import Products

from five import grok
from zope.configuration.name import resolve
from zope.event import notify
from zope.interface import implementedBy, providedBy, Interface, implements
from zope.lifecycleevent import ObjectCreatedEvent
from zope.location.interfaces import ISite

from Products.Silva import mangle
from Products.Silva.icon import registry as icon_registry
from Products.Silva.ExtensionRegistry import extensionRegistry
from silva.core import interfaces

import os.path


class ISilvaFactoryDispatcher(Interface):
    pass


# Views utils

def getFiveViewNameFor(context):
    """Return the correct name for the view if you want to use a Five
    default one.
    """
    stack = [(interfaces.IContainer, 'Five Container'),
             (interfaces.INonPublishable, 'Five Asset'),
             (interfaces.IVersionedContent, 'Five VersionedContent'),
             (interfaces.IContent, 'Five Content')]

    for interface, name in stack:
        if interface.providedBy(context):
            return name


def getSilvaViewFor(context, view_type, obj):
    """Lookup a Silva view, fallback on a Five default one if it
    doesn't exists.
    """

    view_registry = context.service_view_registry
    try:
        # Try first the correct view. It might be None if one is
        # registered but doesn't exists.
        view = view_registry.get_view(view_type, obj.meta_type)
        if view is not None:
            return view
    except KeyError:
        # Not found, search default Five one.
        pass
    return view_registry.get_view(view_type, getFiveViewNameFor(obj))


# Default content factory


def getServiceInterface(factory, isclass=True):
    """Get service interface.
    """
    if isclass:
        implemented = list(implementedBy(factory).interfaces())
    else:
        implemented = list(providedBy(factory).interfaces())
    if (not len(implemented) or
        interfaces.ISilvaService.extends(implemented[0])):
        raise ValueError(
            "Service %r doesn't implements a service interface" % (
                factory,))
    return implemented[0]


def ServiceFactory(factory):
    """A factory for Silva services.
    """
    service_interface = getServiceInterface(factory)
    def factory_method(container, identifier=None, REQUEST=None, *args, **kw):
        """Create a instance of that service, callable through the web.
        """
        if identifier is None:
            if not hasattr(factory, 'default_service_identifier'):
                raise ValueError("No id for the new service")
            identifier = factory.default_service_identifier
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
    def factory_method(container, identifier, title, *args, **kw):
        if ISilvaFactoryDispatcher.providedBy(container):
            container = container.Destination()
        identifier = mangle.Id(container, identifier)
        identifier.cook()
        if not identifier.isValid():
            raise ValueError(
                u'Invalid identifier %s for new content' % identifier)
        identifier = str(identifier)

        content = factory(identifier)
        container._setObject(identifier, content)
        content = getattr(container, identifier)
        content.set_title(title)
        for key, value in kw.items():
            if hasattr(aq_base(content), 'set_%s' % key):
                setter = getattr(content, 'set_%s' % key)
                setter(value)
            elif hasattr(aq_base(content), key):
                setattr(content, key, value)
        notify(ObjectCreatedEvent(content))
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
        identifier = mangle.Id(container, identifier)
        identifier.cook()
        if not identifier.isValid():
            raise ValueError(
                u'Invalid identifier %s for new content' % identifier)
        identifier = str(identifier)

        content = factory(identifier)
        container._setObject(identifier, content)
        content = getattr(container, identifier)

        if no_default_version is False:
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
    def factory_method(container, identifier, title, *args, **kw):
        if ISilvaFactoryDispatcher.providedBy(container):
            container = container.Destination()
        version = version_factory(identifier)
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
        notify(ObjectCreatedEvent(version))
        return version
    return factory_method


# Helpers

def makeZMIFilter(content, zmi_addable=True):
    """
     make a container_filter.  See doc/developer_changes for more info
     this returns a closure that can be used for a container filter
     for a content type during product registration.  The content
     class is also passed into this function.  This closure then knows
     whether and in what containers the particular content type should
     be listed in the zmi add list, Tests are done on the object
     manager (container) and the content class to determine whether
     and what containers the content should appear in.

     Common cases:

     1) object_manager is an ISite, and the content is an
     ISilvaLocalService
     2) object_manager is an IContainer and content is an
        ISilvaObject, IZMIObject, or ISilvaService
     3) object_manager is IVersionedContent and content is IVersion
     4) content is IRoot can only be added outside of a Silva Root
        (i.e.  not within Silva containers
    """
    def SilvaZMIFilter(object_manager, filter_addable=False):
        if filter_addable and not zmi_addable:
            return False
        addable = False
        if ISite.providedBy(object_manager) and \
                interfaces.ISilvaLocalService.implementedBy(content):
            # Services in  sites
            addable = True
        elif interfaces.IContainer.providedBy(object_manager):
            if interfaces.ISilvaObject.implementedBy(content) or \
                    (interfaces.IZMIObject.implementedBy(content) and \
                     not interfaces.ISilvaService.implementedBy(content)):
                # Silva and ZMI content in Silva objects
                addable = True
        elif interfaces.IVersionedContent.providedBy(object_manager) and \
                interfaces.IVersion.implementedBy(content):
                # Let version been added in a versionned
                # object. Should match the correct version of course ...
                addable = True
        if interfaces.IRoot.implementedBy(content):
            return not addable
        return addable
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
    service = getattr(site, id)
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
    interface = getServiceInterface(service, isclass=False)
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

    icon_registry.registerIcon(('meta_type', class_.meta_type), icon_path)
    class_.icon = icon_path

def cleanUp():
    global _meta_type_regs
    Products.meta_types = tuple([ info for info in Products.meta_types
                                  if info['name'] not in _meta_type_regs ])
    _meta_type_regs = []

from zope.testing.cleanup import addCleanUp
addCleanUp(cleanUp)
del addCleanUp
