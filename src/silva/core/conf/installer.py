# -*- coding: utf-8 -*-
# Copyright (c) 2002-2013 Infrae. All rights reserved.
# See also LICENSE.txt

import os.path

from zope.component.interface import provideInterface
from zope.interface import implements, alsoProvides, noLongerProvides
from zope.event import notify

from Products.Silva import roleinfo

from silva.core import interfaces
from silva.core.interfaces import ISilvaObject, IViewableObject, IVersion
from silva.core.interfaces import IAddableContents
from silva.core.interfaces.events import InstalledExtensionEvent


class InstallationStatus(object):

    def __init__(self):
        self.reset()

    def reset(self):
        self.addables = False
        self.security = False
        self.metadata = False


class Installer(object):
    """Installer for system extension: they are always installed.
    """
    not_globally_addables = []
    default_permissions = {}

    def __init__(self):
        # Track which steps are done
        self._is_installed = InstallationStatus()

    def is_silva_addable(self, content):
        """Is the content a Silva addable ?

        You can override this method in a subclass to change this behaviour.
        """
        cls = content['instance']
        return (ISilvaObject.implementedBy(cls) and
                not IVersion.implementedBy(cls))

    def is_silva_content(self, content):
        """Is the content a Silva content ?

        You can override this method in a subclass to change this behaviour.
        """
        cls = content['instance']
        return (ISilvaObject.implementedBy(cls) or
                IVersion.implementedBy(cls))

    def has_default_metadata(self, content):
        """Tell if the content should have default metadata set sets.

        You can override this method in a subclass to change this behaviour.
        """
        cls = content['instance']
        return ((ISilvaObject.implementedBy(cls) and
                 not interfaces.IVersionedObject.implementedBy(cls)) or
                IVersion.implementedBy(cls))

    def configure_content(self, root, extension):
        """Configure extension content: metadata, addables, security.
        """
        contents = extension.get_content()

        # Configure addables
        if not self._is_installed.addables:
            addables = []
            not_addables = []
            for content in contents:
                if self.is_silva_addable(content):
                    if content['name'] not in self.not_globally_addables:
                        addables.append(content['name'])
                    else:
                        not_addables.append(content['name'])
            self.configure_addables(root, addables, not_addables)

        # Configure security
        if not self._is_installed.security:
            secured_contents = []
            for content in contents:
                if self.is_silva_content(content):
                    secured_contents.append(content['name'])
            self.configure_security(root, secured_contents)

        # Configure metadata
        if not self._is_installed.metadata:
            viewables = []
            others = []
            for content in contents:
                if self.has_default_metadata(content):
                    if (IViewableObject.implementedBy(content['instance']) or
                        IVersion.implementedBy(content['instance'])):
                        viewables.append(content['name'])
                    else:
                        others.append(content['name'])
            if viewables:
                root.service_metadata.addTypesMapping(
                    viewables,
                    ('silva-content', 'silva-extra', 'silva-settings'))
            if others:
                root.service_metadata.addTypesMapping(
                    others,
                    ('silva-content', 'silva-extra'))

    def unconfigure_content(self, root, extension):
        """Unconfigure content.
        """
        contents = extension.get_content()

        # Clear addables
        not_addables_anymore = [c['name'] for c in contents]
        self.configure_addables(root, [], not_addables_anymore)

    def configure_metadata(self, root, mapping, where=None):
        """Configure metadata, import metadata sets, and configure
        content type mapping to use them.
        """
        self._is_installed.metadata = True
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
        """Clean ununsed metadata mapping.
        """
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
        collection = service.getCollection()
        for mapping in service.getTypeMapping().getTypeMappings():
            for setid in mapping.iterChain():
                if setid in used_setids:
                    continue
                try:
                    setid = collection.getMetadataSet(setid).getId()
                    used_setids.add(setid)
                except AttributeError:
                    continue
        for setid in setids.difference(used_setids):
            if hasattr(collection, setid):
                collection.manage_delObjects([setid,])

    def configure_addables(self, root, addables, not_addables=[]):
        """Configuration addable on a Silva root.
        """
        self._is_installed.addables = True
        current_addables = root.get_silva_addables_allowed_in_container()
        if not (current_addables or not_addables):
            return
        new_addables = IAddableContents(root).get_container_addables()
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
        self._is_installed.security = True
        for content in contents:
            roles = self.default_permissions.get(content, roles)
            root.manage_permission("Add %ss" % content, roles)


class SystemExtensionInstaller(Installer):
    """Installer for system extension: they are always installed.
    """
    implements(interfaces.IExtensionInstaller)

    def install(self, root, extension):
        pass

    def uninstall(self, root, extension):
        pass

    def refresh(self, root, extension):
        pass

    def is_installed(self, root, extension):
        return True


class DefaultInstaller(Installer):
    """Default installer for extension.
    """
    implements(interfaces.IExtensionInstaller)

    def __init__(self, name=None, interface=None):
        super(DefaultInstaller, self).__init__()
        assert interface is not None, u"You must provide an interface"
        self._interface = interface
        provideInterface('', self._interface)

    def install(self, root, extension):
        """Default installer.
        """
        self._is_installed.reset()
        if self.is_installed(root, extension):
            return         # Don't install already installed extension
        self.install_custom(root)
        self.configure_content(root, extension)

        alsoProvides(root.service_extensions, self._interface)
        notify(InstalledExtensionEvent(extension, root))

    def install_custom(self, root):
        """Custom installation steps.
        """
        pass

    def uninstall(self, root, extension):
        """Default uninstaller.
        """
        if not self.is_installed(root, extension):
            return              # Don't uninstall uninstalled extension.
        self.uninstall_custom(root)
        self.unconfigure_content(root, extension)

        noLongerProvides(root.service_extensions, self._interface)

    def uninstall_custom(self, root):
        """Custom uninstall steps.
        """
        pass

    def refresh(self, root, extension):
        """Refresh extension. Default is to uninstall/install.
        """
        self.uninstall(root, extension)
        self.install(root, extension)

    def is_installed(self, root, extension):
        return self._interface.providedBy(root.service_extensions)

