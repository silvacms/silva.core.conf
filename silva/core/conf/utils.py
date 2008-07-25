# Copyright (c) 2002-2008 Infrae. All rights reserved.
# See also LICENSE.txt
# $Id$

from AccessControl.PermissionRole import PermissionRole
from App.ProductContext import AttrDict
from App.FactoryDispatcher import FactoryDispatcher
from Interface.Implements import instancesOfObjectImplements
from Products.Five.fiveconfigure import unregisterClass
from OFS import misc_ as icons

from zope.configuration.name import resolve
from zope.interface import implementedBy

import AccessControl.Permission
import Globals
import Products

from Products.Silva import mangle
from Products.Silva import interfaces as silvainterfaces
from Products.Silva.icon import registry as icon_registry
from Products.Silva.helpers import add_and_edit, makeContainerFilter
from Products.Silva.ExtensionRegistry import extensionRegistry

import os.path

# Views utils

def getFiveViewNameFor(context):
    """Return the correct name for the view if you want to use a Five
    default one.
    """
    stack = [silvainterfaces.IContainer,
             silvainterfaces.IAsset,
             silvainterfaces.IVersionedContent,
             silvainterfaces.IContent]

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

def ContentFactory(content):
    """A factory for Content factories.

    This generates manage_add<Something> for non-versioned content types.
    """
    def factory_method(self, id, title, *args, **kw):
        container = self
        if not mangle.Id(container, id).isValid():
            return
        object = content(id)
        self._setObject(id, object)
        object = getattr(container, id)
        object.set_title(title)
        add_and_edit(container, id, None)
        return ''
    return factory_method

def VersionedContentFactory(extension_name, content, version):
    """A factory for Versioned Content factories.

    This generates manage_add<Something> for versioned content types. It
    makes sure the first version is already added.
    """
    def factory_method(self, id, title, *args, **kw):
        container = self
        if not mangle.Id(container, id).isValid():
            return
        object = content(id)
        container._setObject(id, object)
        object = getattr(container, id)

        version_factory_name = getFactoryName(version)
        extension = extensionRegistry.get_extension(extension_name)

        version_factory = getattr(
            object.manage_addProduct[extension.product],
            version_factory_name)
        version_factory('0', title, *args, **kw)
        object.create_version('0', None, None)
        add_and_edit(container, id, None)
        return ''
    return factory_method

def VersionFactory(version_class):
    """A factory for Version factories.

    This generateas manage_add<Something>Version for versions.
    """
    def factory_method(self, id, title, *args, **kw):
        container = self
        version = version_class(id, *args, **kw)
        container._setObject(id, version)
        version = container._getOb(id)
        version.set_title(title)
        add_and_edit(container, id, None)
        return ''
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
_register_monkies = []
_meta_type_regs = []

# Registration methods

#visibility can be "Global" or None
def registerClass(class_, extension_name, zmi_addable=False,
                  default_action=None):
    """Register a class with Zope as a type.
    """
    permission = getAddPermissionName(class_)
    interfaces = instancesOfObjectImplements(class_) + list(implementedBy(class_))

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
            'container_filter': makeContainerFilter(zmi_addable)
            }
    Products.meta_types += (info,)

    # register for test cleanup
    _register_monkies.append(class_)
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
    icon = Globals.ImageFile(icon, extension.module_directory)
    icon.__roles__ = None
    if not hasattr(icons.misc_, extension_name):
        setattr(icons.misc_, extension_name,
                icons.Misc_(extension_name, {}))
    getattr(icons.misc_, extension_name)[name] = icon
    icon_path = 'misc_/%s/%s' % (extension_name, name)
    
    icon_registry._icon_mapping[('meta_type', class_.meta_type)] = icon_path
    class_.icon = icon_path

def cleanUp():
    global _register_monkies
    for class_ in _register_monkies:
        unregisterClass(class_)
    _register_monkies = []

    global _meta_type_regs
    Products.meta_types = tuple([ info for info in Products.meta_types
                                  if info['name'] not in _meta_type_regs ])
    _meta_type_regs = []

from zope.testing.cleanup import addCleanUp
addCleanUp(cleanUp)
del addCleanUp
