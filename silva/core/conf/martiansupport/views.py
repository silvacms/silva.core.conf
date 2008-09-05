# Copyright (c) 2002-2008 Infrae. All rights reserved.
# See also LICENSE.txt
# $Id$

from martian.error import GrokError
import martian

from zope.component import provideAdapter, provideUtility
from zope.component.interfaces import IFactory
from zope.contentprovider.interfaces import IContentProvider
from zope.interface import Interface
from zope.interface.interface import InterfaceClass
from zope.publisher.interfaces.browser import IDefaultBrowserLayer, IBrowserRequest

from z3c.resourceinclude.zcml import handler as resourceHandler
from grokcore.view.meta import default_view_name

from silva.core.views import views as silvaviews
from silva.core.views.interfaces import ITemplate
from silva.core.views.baseforms import SilvaMixinAddForm
from silva.core.conf.martiansupport import directives as silvaconf


class ContentProviderGrokker(martian.ClassGrokker):

    martian.component(silvaviews.ContentProvider)
    martian.directive(silvaconf.name, get_default=default_view_name)
    martian.directive(silvaconf.context)
    martian.directive(silvaconf.layer)
    martian.directive(silvaconf.view)

    def grok(self, name, provider, module_info, **kw):
        # Store module_info on the object.
        provider.__view_name__ = name
        provider.module_info = module_info
        return super(ContentProviderGrokker, self).grok(
            name, provider, module_info, **kw)

    def execute(self, provider, name, context, view, layer, config, **kw):
        """Register a content provider.
        """

        if view is None:
            # Can't set default on the directive because of import loop.
            view = ITemplate

        templates = provider.module_info.getAnnotation('grok.templates', None)
        if templates is not None:
            config.action(
                discriminator=None,
                callable=self.checkTemplates,
                args=(templates, provider.module_info, provider)
                )

        for_ = (context, layer, view,)
        config.action(
            discriminator=('adapter', for_, IContentProvider, name),
            callable=provideAdapter,
            args=(provider, for_, IContentProvider, name),
            )

        return True

    def checkTemplates(self, templates, module_info, provider):
        def has_render(provider):
            return provider.render != silvaviews.ContentProvider.render
        def has_no_render(provider):
            return not has_render(provider)
        templates.checkTemplates(module_info, provider, 'contentprovider',
                                 has_render, has_no_render)


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


class AddFormGrokker(martian.ClassGrokker):
    """Grok add form and register them as factories.
     """

    martian.component(SilvaMixinAddForm)
    martian.directive(silvaconf.name)

    def execute(self, form, name, config, **kw):
        config.action(
            discriminator = ('utility', IFactory, name),
            callable = provideUtility,
            args = (form, IFactory, name),
            )
        return True
