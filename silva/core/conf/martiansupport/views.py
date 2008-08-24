# Copyright (c) 2002-2008 Infrae. All rights reserved.
# See also LICENSE.txt
# $Id$

from martian.error import GrokError
import martian

from zope.component import provideAdapter
from zope.contentprovider.interfaces import IContentProvider
from zope.interface import Interface
from zope.interface.interface import InterfaceClass
from zope.publisher.interfaces.browser import IDefaultBrowserLayer, IBrowserRequest

from z3c.resourceinclude.zcml import handler as resourceHandler

from silva.core.views import views as silvaviews
from silva.core.views.interfaces import ITemplate

from silva.core.conf.martiansupport import directives as silvaconf


class ContentProviderGrokker(martian.ClassGrokker):

    martian.component(silvaviews.ContentProvider)
    martian.directive(silvaconf.name)
    martian.directive(silvaconf.context)
    martian.directive(silvaconf.layer)

    def execute(self, provider, name, context, layer, config, **kw):
        """Register a content provider.
        """

        for_ = (context, layer, ITemplate,)
        config.action(
            discriminator=('adapter', for_, IContentProvider, name),
            callable=provideAdapter,
            args=(provider, for_, IContentProvider, name),
            )

        return True


_marker = object()

class ResourceIncludeGrokker(martian.InstanceGrokker):
    martian.component(InterfaceClass)

    def grok(self, name, interface, module_info, config, **kw):

        resources = silvaconf.resource.bind(default=_marker).get(interface)
        if resources is _marker:
            return False

        if not interface.extends(IDefaultBrowserLayer):
            raise GrokError(
                """A resource can be included only on a layer.""")

        if module_info.isPackage():
            resource_dir = module_info.getModule().__name__
        else:
            base = module_info.getModule().__name__
            resource_dir = '.'.join(base.split('.')[:-1])

        resources = [resource_dir + '/' + r for r in resources]

        config.action(
            discriminator = ('resourceInclude', IBrowserRequest, interface, "".join(resources)),
            callable = resourceHandler,
            args = (resources, interface, None, None),
            )

        return True
