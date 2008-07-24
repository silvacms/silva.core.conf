# Copyright (c) 2002-2008 Infrae. All rights reserved.
# See also LICENSE.txt
# $Id$

from zope.configuration.name import resolve
from zope.component import getMultiAdapter, queryAdapter
from zope.component import getSiteManager
from zope.component.interfaces import IFactory
from zope.interface import Interface
from zope.formlib import form

from Products.Five.formlib import formbase
from Products.Silva.ViewCode import ViewCode
from Products.Silva.ExtensionRegistry import extensionRegistry
from AccessControl import getSecurityManager

import grokcore.view
import five.grok
import martian

from silva.core.conf.interfaces import IDefaultAddFields
from silva.core.conf.utils import getFactoryName, getSilvaViewFor
import directives as silvadirectives

# Simple views

class View(five.grok.View):
    """Grok View on Silva objects.
    """

    silvadirectives.baseclass()
    silvadirectives.name(u'public_view')

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


# Forms

class SilvaGrokForm(grokcore.view.GrokForm, ViewCode):
    """Silva Grok Form mixin.
    """

    silvadirectives.baseclass()

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


    def _silvaView(self):
        # Lookup the correct Silva edit view so forms are able to use
        # silva macros.
        return getSilvaViewFor(self.context, 'edit', self.context)

    def namespace(self):
        # This add to the template namespace global variable used in
        # Zope 2 and Silva templates.  Here should be bind at the
        # correct place in the Silva view registry so you should be
        # able to use silva macro in your templates.
        view = self._silvaView()
        return {'here': view,
                'user': getSecurityManager().getUser(),
                'container': self.context.aq_inner,}


class PageForm(SilvaGrokForm, formbase.PageForm, View):
    """Generic form.
    """

    silvadirectives.baseclass()


class AddForm(SilvaGrokForm, formbase.AddForm, View):
    """Add form.
    """

    silvadirectives.baseclass()

    template = grokcore.view.PageTemplateFile('templates/add_form.pt')

    def _silvaView(self):
        view_registry = self.context.service_view_registry
        ## Then you add a element, you have the edit view of the
        ## container wrapped by the add view.
        parent_view = super(AddForm, self)._silvaView()
        return view_registry.get_view('add', 'Five Content').__of__(parent_view)

    def setUpWidgets(self, ignore_request=False):
        # Add missing fields from IDefaultAddFields
        field_to_add = form.FormFields()
        for field in IDefaultAddFields:
            if self.form_fields.get(field) is None:
                field_to_add += form.FormFields(IDefaultAddFields[field])
        if field_to_add:
            self.form_fields = field_to_add + self.form_fields
        # Setup widgets
        super(AddForm, self).setUpWidgets(ignore_request)

    def createAndAdd(self, data):
        addable = filter(lambda a: a['name'] == self.__name__,
                         extensionRegistry.get_addables())
        if len(addable) != 1:
            raise ValueError, "Content cannot be found. " \
               "Check that the name of add is the meta type of your content." 
        addable = addable[0]
        factory = getattr(resolve(addable['instance'].__module__),
                          getFactoryName(addable['instance']))
        # Build the content
        obj_id = str(data['id'])
        factory(self.context, obj_id, data['title'])
        obj = getattr(self.context, obj_id)
        for key, value in data.iteritems():
            if key not in IDefaultAddFields:
                setattr(obj, key, value)

        # Update last author information
        obj.sec_update_last_author_info()
        self.context.sec_update_last_author_info()

        self.redirect('%s/edit' % self.context.absolute_url())


class EditForm(SilvaGrokForm, formbase.EditForm, View):
    """Edition form.
    """

    silvadirectives.baseclass()
    silvadirectives.name(u'tab_edit')

# Grokkers for forms.

class AddFormGrokker(martian.ClassGrokker):
    """Grok add form and register them as factories.
    """

    martian.component(AddForm)
    martian.directive(silvadirectives.name)

    def execute(self, form, name, **kw):
        sm = getSiteManager()
        sm.registerUtility(form, IFactory, name=name)
        return True
