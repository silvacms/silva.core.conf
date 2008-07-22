# Copyright (c) 2002-2008 Infrae. All rights reserved.
# See also LICENSE.txt
# $Id$

from zope.component import getMultiAdapter

import five.grok
import martian

class View(five.grok.View):

    martian.baseclass()
    five.grok.name(u'five-view')

    def publishTraverse(self, request, name):
        """In Zope2, if you give a name, index_html is appended to it.
        """
        if name == 'index_html':
            return self
        return super(View, self).publishTraverse(request, name)


class Viewable(object):
    """Default Five viewable object.
    """

    def view(self):
        """ render the public Five view for this object
        """
        # if a parameter ?include is in the request, call the original view,
        # and use it as input for the include view. When using ?include we expect
        # that '/view' was added to the url, and it will return a page suitable
        # for including in other documents
        # XXX maybe we should use an adapter here?
        result = getMultiAdapter((self, self.REQUEST), name=u'five-view')()
        if self.REQUEST.form.has_key('include'):
            view = getMultiAdapter((self, self.REQUEST), name=u'five-include')
            result = view(content=result)
        return result

    preview = view
