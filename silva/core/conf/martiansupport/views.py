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
    """Grok View on Silva objects.
    """

    directives.baseclass()
    directives.name(u'public_view')

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
        """Render the public Five view for this object
        """
        result = getMultiAdapter((self, self.REQUEST), name=u'public_view')()
        return result

    preview = view


class SilvaGrokForm(grokcore.view.GrokForm, ViewCode):
    """Silva Grok Form mixin.
    """

    directives.baseclass()

    template = grokcore.view.PageTemplateFile('templates/form.pt')

    def __init__(self, context, request):
        super(SilvaGrokForm, self).__init__(context, request)
        # Missing init code of grokcore.view.components.Views
        self.__name__ = self.__view_name__
        self.static = queryAdapter(
            self.request, Interface,
            name = self.module_info.package_dotted_name)

        # Set model on request like SilvaViews
        self.request['model'] = context
        # Set id on template some macros uses template/id
        self.template._template.id = self.__name__


    def namespace(self):
        # This add to the template namespace global variable used in
        # Zope 2 and Silva templates.  Here should be bind at the
        # correct place in the Silva view registry so you should be
        # able to use silva macro in your templates.
        view_registry = self.context.service_view_registry
        view = view_registry.get_method_on_view('edit', self.context, self.__name__)
        return {'here': view,
                'user': getSecurityManager().getUser(),
                'container': self.context.aq_inner,}


class PageForm(SilvaGrokForm, formbase.PageForm, View):
    """Generic form.
    """

    directives.baseclass()


class AddForm(SilvaGrokForm, formbase.AddForm, View):
    """Add form.
    """

    directives.baseclass()
    directives.name(u'add')


class EditForm(SilvaGrokForm, formbase.EditForm, View):
    """Edition form.
    """

    directives.baseclass()
    directives.name(u'tab_edit')


