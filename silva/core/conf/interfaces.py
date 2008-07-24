# -*- coding: utf-8 -*-
# Copyright (c) 2002-2008 Infrae. All rights reserved.
# See also LICENSE.txt
# $Id$

from zope import interface
from zope import schema

from silva.core.conf.fields import ID

from Products.Silva.i18n import translate as _

class IDefaultAddFields(interface.Interface):
    """Default fields used in a add form. You don't have to defines this fields.
    """

    id = ID(
        title=_(u"id"),
        description=_(u"No spaces or special characters besides ‘_’ or ‘-’ or ‘.’"),
        required=True)
    title = schema.TextLine(
        title=_(u"title"),
        description=_(u"The title will be publicly visible, and is used for the link in indexes."),
        required=True)
