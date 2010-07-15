# Copyright (c) 2002-2010 Infrae. All rights reserved.
# See also LICENSE.txt
# $Id$

import martian

from Products.Silva.transform.renderer.xsltrendererbase import XSLTRendererBase
from Products.Silva.transform.rendererreg import getRendererRegistry

import silva.core.conf.martiansupport.directives as silvadirectives


class XSLTRendererGrokker(martian.ClassGrokker):
    """This lookup XSLTRenderer and register them.
    """
    martian.component(XSLTRendererBase)
    martian.directive(silvadirectives.title)
    martian.directive(silvadirectives.context)
    martian.directive(silvadirectives.XSLT)
    martian.priority(200)

    def grok(self, name, class_, module_info, config, **kw):
        module = None
        values = {}
        if module_info is not None:
            module = module_info.getModule()

        for d in martian.directive.bind().get(self.__class__):
            values[d.name] = d.get(class_, module, **kw)

        registry = getRendererRegistry()
        renderer = class_(values['XSLT'], module_info.path)
        registry.registerRenderer(values['context'].meta_type,
                                  values['title'],
                                  renderer)
        return True
