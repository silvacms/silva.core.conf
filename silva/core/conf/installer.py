# -*- coding: utf-8 -*-
# Copyright (c) 2002-2008 Infrae. All rights reserved.
# See also LICENSE.txt
# $Id$

from zope.component.interface import provideInterface
from zope import interface

from Products.Silva.install import add_fss_directory_view
from Products.Silva.interfaces import IVersion, IVersionedContent
from Products.Silva.ExtensionRegistry import extensionRegistry

from silva.core.conf.interfaces import IExtensionInstaller
from silva.core import conf as silvaconf

import os.path

class DefaultInstaller(object):

    interface.implements(IExtensionInstaller)

    def __init__(self, name, marker_interface):
        self._name = name
        self._interface = marker_interface
        provideInterface('', self._interface)

    def install(self, root):
        """Default installer.
        """
        extension, contents = self.retrieveExtensionAndContent()

        # Configure addables
        addables = [c['name'] for c in contents if not IVersion.implementedBy(c['instance'])]
        self.configureAddables(root, addables)

        # Configure metadata
        import pdb ; pdb.set_trace()
        meta_types = [c['name'] for c in contents if not IVersionedContent.implementedBy(c['instance'])]
        root.service_metadata.addTypesMapping(
            meta_types,
            ('silva-content', 'silva-extra',))

        # Configure Silva Views
        if self.hasSilvaViews(extension):
            add_fss_directory_view(root.service_views, extension.name,
                                   extension.module.__file__, 'views')

        interface.alsoProvides(root.service_extensions, self._interface)

    def uninstall(self, root):
        """Default uninstaller.
        """
        extension, contents = self.retrieveExtensionAndContent()

        # We should clean addables list as well

        # Unconfigure Silva Views
        if self.hasSilvaViews(extension):
            root.service_views.manage_delObjects([extension.name,])

        interface.noLongerProvides(root.service_extensions, self._interface)

    def is_installed(self, root):
        return self._interface.providedBy(root.service_extensions)


    # Helpers 

    def hasSilvaViews(self, extension):
        return os.path.exists(os.path.join(extension.module_directory, 'views'))

    def retrieveExtensionAndContent(self):
        """Return a tuple (extension, content list).
        """

        extension = extensionRegistry.get_extension(self._name)

        def isAnExtensionContent(c):
            return c['product'] == extension.name

        contents = filter(isAnExtensionContent,
                          extensionRegistry.get_addables())

        return (extension, contents,)

    def configureAddables(self, root, addables):
        """Make sure the right items are addable in the root.
        """
        new_addables = list(root.get_silva_addables_allowed_in_publication())
        for a in addables:
            if a not in new_addables:
                new_addables.append(a)
        root.set_silva_addables_allowed_in_publication(new_addables)



