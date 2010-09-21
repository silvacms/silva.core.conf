# -*- coding: utf-8 -*-
# Copyright (c) 2002-2010 Infrae. All rights reserved.
# See also LICENSE.txt
# $Id$

import os.path

import zope.cachedescriptors.property
from zope.component.interface import provideInterface
from zope import interface

from Products.Silva import roleinfo
from Products.Silva.install import add_fss_directory_view
from Products.Silva.ExtensionRegistry import extensionRegistry

from silva.core import interfaces


class SystemExtensionInstaller(object):
    """Installer for system extension: there are always installed.
    """
    interface.implements(interfaces.IExtensionInstaller)

    def install(self, root):
        pass

    def uninstall(self, root):
        pass

    def refresh(self, root):
        pass

    def is_installed(self, root):
        return True


class InstallationStatus(object):

    def __init__(self):
        self.reset()

    def reset(self):
        self.addables = False
        self.security = False
        self.metadata = False


class DefaultInstaller(object):
    """Default installer for extension.
    """
    interface.implements(interfaces.IExtensionInstaller)

    not_globally_addables = []
    default_permissions = {}

    def __init__(self, name, marker_interface):
        self._name = name
        self.__interface = marker_interface
        # Track which steps are done
        self.__is_installed = InstallationStatus()
        provideInterface('', self.__interface)

    def install(self, root):
        """Default installer.
        """
        self.__is_installed.reset()
        # Don't install already installed extension
        if self.is_installed(root):
            return
        self.install_custom(root)
        contents = self.extension.get_content()

        # Configure addables
        if not self.__is_installed.addables:
            addables = []
            not_addables = []
            for content in contents:
                if self.is_silva_content(content):
                    if self.is_globally_addable(content):
                        addables.append(content['name'])
                    else:
                        not_addables.append(content['name'])
            self.configure_addables(root, addables, not_addables)
        if not self.__is_installed.security:

            def need_security(content):
                cls = content['instance']
                return (interfaces.ISilvaObject.implementedBy(cls) or
                        interfaces.IVersion.implementedBy(cls))

            secured_contents = [c['name'] for c in contents if need_security(c)]
            self.configure_security(root, secured_contents)

        # Configure metadata
        if not self.__is_installed.metadata:
            root.service_metadata.addTypesMapping(
                [c['name'] for c in contents if self.has_default_metadata(c)],
                ('silva-content', 'silva-extra',))

        # Configure Silva Views, only if extension has SilvaViews AND
        #  the views do not already exist
        if self.has_silva_views and \
           not hasattr(root.service_views.aq_explicit,self.extension.name):
            add_fss_directory_view(root.service_views, self.extension.name,
                                   self.extension.module.__file__, 'views')

        interface.alsoProvides(root.service_extensions, self.__interface)

    def install_custom(self, root):
        """Custom installation steps.
        """
        pass

    def uninstall(self, root):
        """Default uninstaller.
        """
        if not self.is_installed(root):
            return              # Don't uninstall uninstalled extension.
        self.uninstall_custom(root)
        contents = self.extension.get_content()

        # Clear addables
        not_addables_anymore = [c['name'] for c in contents]
        self.configure_addables(root, [], not_addables_anymore)

        # Unconfigure Silva Views
        if self.has_silva_views:
            root.service_views.manage_delObjects([self.extension.name,])

        interface.noLongerProvides(root.service_extensions, self.__interface)

    def uninstall_custom(self, root):
        """Custom uninstall steps.
        """
        pass

    def refresh(self, root):
        """Refresh extension.  Default is to uninstall/install
        """
        self.uninstall(root)
        self.install(root)

    def is_installed(self, root):
        return self.__interface.providedBy(root.service_extensions)

    def configure_metadata(self, root, mapping, where=None):
        self.__is_installed.metadata = True
        if where is None:
            where = globals()
        product = os.path.dirname(where['__file__'])
        schema = os.path.join(product, 'schema')
        collection = root.service_metadata.getCollection()

        for types, setids in mapping.items():
            for setid in setids:
                if not setid in collection.objectIds():
                    xmlfile = os.path.join(schema, setid+'.xml')
                    definition = open(xmlfile, 'r')
                    collection.importSet(definition)
            root.service_metadata.addTypesMapping(types, setids)
        root.service_metadata.initializeMetadata()

    def unconfigure_metadata(self, root, mapping):
        service = root.service_metadata
        all_types = []
        all_sets = []
        for types, setids in mapping.items():
            for typename in types:
                if typename in all_types:
                    continue
                all_types.append(typename)
            for setid in setids:
                if setid in all_sets:
                    continue
                all_sets.append(setid)
        service.removeTypesMapping(all_types, all_sets)
        service.initializeMetadata()

        # delete metadata description if there and no longer in use
        setids = set()
        for values in mapping.values():
            setids.update(values)
        used_setids = set()
        for mapping in service.getTypeMapping().getTypeMappings():
            used_setids.update(
                map(lambda m: m.getId(), mapping.getMetadataSets()))
        collection = service.getCollection()
        for setid in setids.difference(used_setids):
            if hasattr(collection, setid):
                collection.manage_delObjects([setid,])

    @zope.cachedescriptors.property.CachedProperty
    def extension(self):
        return extensionRegistry.get_extension(self._name)

    @property
    def has_silva_views(self):
        return os.path.exists(os.path.join(
                self.extension.module_directory, 'views'))

    def configure_addables(self, root, addables, not_addables=[]):
        """Make sure the right items are addable in the root.
        """
        self.__is_installed.addables = True
        new_addables = list(root.get_silva_addables_allowed_in_container())
        for addable in not_addables:
            if addable in new_addables:
                new_addables.remove(addable)
        for addable in addables:
            if addable not in new_addables:
                new_addables.append(addable)
        root.set_silva_addables_allowed_in_container(new_addables)

    def configure_security(self, root, contents, roles=roleinfo.AUTHOR_ROLES):
        """Configure the security of a list of content.
        """
        self.__is_installed.security = True
        for content in contents:
            roles = self.default_permissions.get(content, roles)
            root.manage_permission("Add %ss" % content, roles)

    def is_silva_content(self, content):
        """Is the content a Silva content ?
        """
        cls = content['instance']
        return (interfaces.ISilvaObject.implementedBy(cls) and
                not interfaces.IVersion.implementedBy(cls))

    def is_globally_addable(self, content):
        """Tell if the content should be addable by default.

        You can override this method in a subclass to add exceptions
        and prevent to be able to add content in the root for
        instance.
        """
        if content['name'] in self.not_globally_addables:
            return False
        return self.is_silva_content(content)

    def has_default_metadata(self, content):
        """Tell if the content should have default metadata set sets.

        You can override this method in a subclass to change this behaviour.
        """
        cls = content['instance']
        return ((interfaces.ISilvaObject.implementedBy(cls) and
                 not interfaces.IVersionedContent.implementedBy(cls)) or
                interfaces.IVersion.implementedBy(cls))

    # BBB
    configureMetadata = configure_metadata
    unconfigureMetadata = unconfigure_metadata
    configureAddables = configure_addables
    configureSecurity = configure_security
    isGloballyAddable = is_globally_addable
    hasDefaultMetadata = has_default_metadata
