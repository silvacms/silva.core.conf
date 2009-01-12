# -*- coding: utf-8 -*-
# Copyright (c) 2002-2009 Infrae. All rights reserved.
# See also LICENSE.txt
# $Id$

import zope.cachedescriptors.property
from zope.component.interface import provideInterface
from zope import interface

from Products.Silva import interfaces as silvainterfaces
from Products.Silva.install import add_fss_directory_view
from Products.Silva.ExtensionRegistry import extensionRegistry

import os.path

class SystemExtensionInstaller(object):
    """Installer for system extension: there are always installed.
    """

    interface.implements(silvainterfaces.IExtensionInstaller)

    def install(self, root):
        pass

    def uninstall(self, root):
        pass

    def is_installed(self, root):
        return True

class DefaultInstaller(object):
    """Default installer for extension.
    """

    interface.implements(silvainterfaces.IExtensionInstaller)

    def __init__(self, name, marker_interface):
        self._name = name
        self._interface = marker_interface
        provideInterface('', self._interface)

    def install(self, root):
        """Default installer.
        """

        if self.is_installed(root):
            return              # Don't install already installed extension

        contents = self.extension.get_content()

        # Configure addables
        addables = [c['name'] for c in contents if self.isGloballyAddable(c)]
        self.configureAddables(root, addables)

        # Configure metadata
        meta_types = [c['name'] for c in contents if self.hasDefaultMetadata(c)]
        root.service_metadata.addTypesMapping(
            meta_types,
            ('silva-content', 'silva-extra',))

        # Configure Silva Views
        if self.hasSilvaViews:
            add_fss_directory_view(root.service_views, self.extension.name,
                                   self.extension.module.__file__, 'views')

        interface.alsoProvides(root.service_extensions, self._interface)

    def uninstall(self, root):
        """Default uninstaller.
        """

        if not self.is_installed(root):
            return              # Don't uninstall uninstalled extension.

        contents = self.extension.get_content()

        # Clear addables
        not_addables_anymore = [c['name'] for c in contents]
        self.configureAddables(root, [], not_addables_anymore)

        # Unconfigure Silva Views
        if self.hasSilvaViews:
            root.service_views.manage_delObjects([self.extension.name,])

        interface.noLongerProvides(root.service_extensions, self._interface)

    def is_installed(self, root):
        return self._interface.providedBy(root.service_extensions)


    # Helpers

    @zope.cachedescriptors.property.CachedProperty
    def extension(self):
        return extensionRegistry.get_extension(self._name)

    @property
    def hasSilvaViews(self):
        return os.path.exists(os.path.join(self.extension.module_directory, 'views'))

    def configureAddables(self, root, addables, not_addables=[]):
        """Make sure the right items are addable in the root.
        """
        new_addables = list(root.get_silva_addables_allowed_in_container())
        for a in not_addables:
            if a in new_addables:
                new_addables.remove(a)
        for a in addables:
            if a not in new_addables:
                new_addables.append(a)
        root.set_silva_addables_allowed_in_container(new_addables)

    def isGloballyAddable(self, content):
        """Tell if the content should be addable.

        You can override this method in a subclass to add exceptions.
        """
        class_ = content['instance']
        return (silvainterfaces.ISilvaObject.implementedBy(class_) and
                not silvainterfaces.IVersion.implementedBy(class_))

    def hasDefaultMetadata(self, content):
        """Tell if the content should have default metadata set sets.

        You can override this method in a subclass to change this behaviour.
        """
        class_ = content['instance']
        return ((silvainterfaces.ISilvaObject.implementedBy(class_) and
                 not silvainterfaces.IVersionedContent.implementedBy(class_)) or
                silvainterfaces.IVersion.implementedBy(class_))
