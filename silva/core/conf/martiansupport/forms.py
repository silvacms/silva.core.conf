# -*- coding: utf-8 -*-
# Copyright (c) 2002-2008 Infrae. All rights reserved.
# See also LICENSE.txt
# $Id$

from zope.configuration.name import resolve
from zope.component import queryAdapter
from zope.component import getSiteManager
from zope.component.interfaces import IFactory
from zope.formlib import form
from zope import event
from zope import interface
from zope import lifecycleevent

from Products.Five.formlib import formbase
from Products.Silva.i18n import translate as _
from Products.Silva.interfaces import IVersionedContent
from Products.Silva.ViewCode import ViewCode
from Products.Silva.ExtensionRegistry import extensionRegistry
from AccessControl import getSecurityManager

from grokcore.view.formlib import action
import grokcore.view
import five.grok
import martian

from silva.core.conf.martiansupport.views import SilvaGrokView
from silva.core.conf.interfaces import IDefaultAddFields, IFeedbackView
from silva.core.conf.utils import getFactoryName, getSilvaViewFor
import directives as silvadirectives


# Forms

class SilvaGrokForm(grokcore.view.GrokForm, ViewCode):
    """Silva Grok Form mixin.
    """

    interface.implements(IFeedbackView)

    silvadirectives.baseclass()

    template = grokcore.view.PageTemplateFile('templates/form.pt')

    def __init__(self, context, request):
        super(SilvaGrokForm, self).__init__(context, request)
        # Missing init code of grokcore.view.components.Views
        self.__name__ = self.__view_name__
        self.static = queryAdapter(
            self.request, interface.Interface,
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

    @property
    def status_type(self):
        # Return message_type for status.
        return self.errors and 'error' or 'feedback'


class PageForm(SilvaGrokForm, formbase.PageForm, SilvaGrokView):
    """Generic form.
    """

    silvadirectives.baseclass()


class AddForm(SilvaGrokForm, formbase.AddForm, SilvaGrokView):
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

    @action(_(u"save"), condition=form.haveInputWidgets)
    def handle_save(self, **data):
        obj = self.createAndAdd(data)
        self.redirect('%s/edit' % self.context.absolute_url())

    @action(_(u"save + edit"), condition=form.haveInputWidgets)
    def handle_save_and_enter(self, **data):
        obj = self.createAndAdd(data)
        self.redirect('%s/edit' % obj.absolute_url())

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

        editable_obj = obj.get_editable()
        for key, value in data.iteritems():
            if key not in IDefaultAddFields:
                setattr(editable_obj, key, value)

        # Update last author information
        obj.sec_update_last_author_info()
        self.context.sec_update_last_author_info()

        # Set status
        self.status = _(u'Created ${meta_type} "${obj_id}".',
                        mapping={'obj_id': obj_id,
                                 'meta_type': obj.meta_type,})

        return obj



class EditForm(SilvaGrokForm, formbase.EditForm, SilvaGrokView):
    """Edition form.
    """

    silvadirectives.baseclass()
    silvadirectives.name(u'tab_edit')

    ## If we refactor the Silva views correctly, we should be able to
    ## remove the two followings property, and use the same template
    ## than a PageForm. if.

    template = grokcore.view.PageTemplateFile('templates/edit_form.pt')

    propose_new_version = False
    is_editable = True
    
    @property
    def propose_to_publish(self):
        if not IVersionedContent.providedBy(self.context):
            return False
        sm = getSecurityManager()
        return (self.context.get_unapproved_version() and
                sm.checkPermission('Approve Silva content', self.context))

    ## End of useless duplication.

    def setUpWidgets(self, ignore_request=False):
        self.adapters = {}
        # We should use the editable version to setup the widgets.
        editable_obj =  self.context.get_editable()
        if editable_obj is None:
            # If there is no editable version, create an empty list of fields.
            self.widgets = form.Widgets([], self.prefix)
            self.propose_new_version = IVersionedContent.providedBy(self.context)
            self.is_editable = False
        else:
            self.widgets = form.setUpEditWidgets(
                self.form_fields, self.prefix, editable_obj, self.request,
                adapters=self.adapters, ignore_request=ignore_request)
        
    @action(_("save"), condition=form.haveInputWidgets)
    def handle_edit_action(self, **data):
        editable_obj = self.context.get_editable()
        if form.applyChanges(editable_obj, self.form_fields, data, self.adapters):
            event.notify(lifecycleevent.ObjectModifiedEvent(editable_obj))
            self.status = _(u'${meta_type} changed.',
                            mapping={'meta_type': self.context.meta_type,})
        else:
            self.status = _(u'No changes')



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
