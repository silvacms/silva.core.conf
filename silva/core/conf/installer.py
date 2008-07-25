# -*- coding: utf-8 -*-
# Copyright (c) 2002-2008 Infrae. All rights reserved.
# See also LICENSE.txt
# $Id$

import zope.cachedescriptors.property
from zope.component.interface import provideInterface
from zope import interface

from Products.Silva import interfaces as silvainterfaces
from Products.Silva.install import add_fss_directory_view
from Products.Silva.ExtensionRegistry import extensionRegistry

from silva.core import conf as silvaconf

import os.path

class DefaultInstaller(object):

    interface.implements(silvainterfaces.IExtensionInstaller)

    def __init__(self, name, marker_interface):
        self._name = name
        self._interface = marker_interface
        provideInterface('', self._interface)

    def install(self, root):
        """Default installer.
        """
        contents = self.extension.get_content()

        # Configure addables
        addables = [c['name'] for c in contents if self.isAddable(c)]
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
        # We should clean addables list as well

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

    def configureAddables(self, root, addables):
        """Make sure the right items are addable in the root.
        """
        new_addables = list(root.get_silva_addables_allowed_in_publication())
        for a in addables:
            if a not in new_addables:
                new_addables.append(a)
        root.set_silva_addables_allowed_in_publication(new_addables)

    def isAddable(self, content):
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