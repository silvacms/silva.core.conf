# -*- coding: utf-8 -*-
# Copyright (c) 2002-2008 Infrae. All rights reserved.
# See also LICENSE.txt
# $Id$

import zope.cachedescriptors.property
from zope.component import getMultiAdapter
from zope.i18n import translate

import five.grok

import urllib

from silva.core.conf.interfaces import IFeedbackView
import directives as silvadirectives

# Simple views

class SilvaGrokView(five.grok.View):
    """Grok View on Silva objects.
    """

    silvadirectives.baseclass()

    def publishTraverse(self, request, name):
        """In Zope2, if you give a name, index_html is appended to it.
        """
        if name == 'index_html':
            return self
        return super(View, self).publishTraverse(request, name)

    def redirect(self, url):
        # Override redirect to send status information if there is.
        if IFeedbackView.providedBy(self):
            message = self.status
            if message:
                message = translate(message)
                if isinstance(message, unicode):
                    # XXX This won't be decoded correctly at the other end.
                    message = message.encode('utf8')
                to_append = urllib.urlencode({'message': message,
                                              'message_type': self.status_type,})
                join_char = '?' in url and '&' or '?'
                super(SilvaGrokView, self).redirect(url + join_char + to_append)
                return
        super(SilvaGrokView, self).redirect(url)


class View(SilvaGrokView):
    """View on Silva object, support view and preview
    """

    silvadirectives.baseclass()
    silvadirectives.name(u'public_view')

    def __call__(self, preview=False):
        self.is_preview = preview
        return super(View, self).__call__()

    @zope.cachedescriptors.property.CachedProperty
    def content(self):
        if self.is_preview:
            return self.context.get_previewable()
        return self.context.get_viewable()

    def namespace(self):
        return {'content': self.content}


class Viewable(object):
    """Default Five viewable object.
    """

    def view(self):
        """Render the public Five view for this object
        """
        return getMultiAdapter((self, self.REQUEST), name=u'public_view')(preview=False)


    def preview(self):
        """Render the public Five preview for this object
        """
        return getMultiAdapter((self, self.REQUEST), name=u'public_view')(preview=True)


