# -*- coding: utf-8 -*-
# Copyright (c) 2002-2009 Infrae. All rights reserved.
# See also LICENSE.txt
# $Id$

import zope.cachedescriptors.property
from zope.component.interface import provideInterface
from zope import interface


class SystemExtensionInstaller(object):
    """Installer for system extension: there are always installed.
    """

    def install(self, root):
        pass

    def uninstall(self, root):
        pass

    def is_installed(self, root):
        return True

class DefaultInstaller(object):
    """Default installer for extension.
    """


    def __init__(self, name, marker_interface):
        self._name = name
        self._interface = marker_interface
        provideInterface('', self._interface)

    def install(self, root):
        """Default installer.
        """

        if self.is_installed(root):
            return              # Don't install already installed extension
        self.install_custom(root)
        interface.alsoProvides(root.service_extensions, self._interface)

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
        interface.noLongerProvides(root.service_extensions, self._interface)

    def uninstall_custom(self, root):
        """Custom uninstall steps.
        """
        pass

    def is_installed(self, root):
        return self._interface.providedBy(root.service_extensions)

    def configure_metadata(root, mapping):
        product = package_home(globals())
        schema = path.join(product, 'schema')
        collection = root.service_metadata.getCollection()

        for types, setids in mapping.items():
            for setid in setids:
                if not setid in collection.objectIds():
                    xmlfile = path.join(schema, setid+'.xml')
                    definition = open(xmlfile, 'r')
                    collection.importSet(definition)
            root.service_metadata.addTypesMapping(types, setids)
        root.service_metadata.initializeMetadata()

    def unconfigure_metadata(root, mapping):
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
        root.service_metadata.removeTypesMapping(all_types, all_sets)
        root.service_metadata.initializeMetadata()

