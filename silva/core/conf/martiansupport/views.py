# Copyright (c) 2002-2008 Infrae. All rights reserved.
# See also LICENSE.txt
# $Id$

from zope.interface import Interface
from zope.component import getMultiAdapter, queryAdapter
from zope.formlib import form

from Products.Five.formlib import formbase
from Products.Silva.ViewCode import ViewCode
from AccessControl import getSecurityManager

import grokcore.view
import five.grok
import martian
import directives

class View(five.grok.View):

    directives.baseclass()
    directives.name(u'five-view')

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

class AddForm(grokcore.view.GrokForm, formbase.AddForm, View):

    directives.baseclass()
    directives.name(u'add')


class EditForm(grokcore.view.GrokForm, formbase.EditForm, View, ViewCode):

    template = grokcore.view.PageTemplateFile('templates/form.pt')

    directives.baseclass()
    directives.name(u'tab_edit')

    def __init__(self, context, request):
        super(EditForm, self).__init__(context, request)
        self.__name__ = self.__view_name__
        self.static = queryAdapter(
            self.request, Interface,
            name = self.module_info.package_dotted_name)

        # Set model on request like SilvaViews
        self.request['model'] = context
        # Set id on template some macros uses template/id
        self.template._template.id = self.__name__

    def namespace(self):
        view_registry = self.context.service_view_registry
        view = view_registry.get_method_on_view('edit', self.context, self.__name__)
        return {'here': view,
                'user': getSecurityManager().getUser(),
                'container': self.context.aq_inner,}
