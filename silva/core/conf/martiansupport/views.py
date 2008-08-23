# Copyright (c) 2002-2008 Infrae. All rights reserved.
# See also LICENSE.txt
# $Id$

import martian

from zope.component import provideAdapter
from zope.contentprovider.interfaces import IContentProvider
from zope.interface import Interface

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

