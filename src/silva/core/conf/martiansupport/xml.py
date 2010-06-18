# Copyright (c) 2002-2010 Infrae. All rights reserved.
# See also LICENSE.txt
# $Id$

import martian

from Products.Silva.silvaxml import xmlimport

import silva.core.conf.martiansupport.directives as silvadirectives

class XMLImporterGrokker(martian.ClassGrokker):
    """Collect importer for contents.
    """

    martian.component(xmlimport.SilvaBaseHandler)
    martian.directive(silvadirectives.namespace)
    martian.directive(silvadirectives.name)
    martian.priority(200)

    def execute(self, importer, namespace, name=None, **kw):
        if not name:
            return False
        xmlimport.theXMLImporter.registerHandler((namespace, name), importer)
        return True
