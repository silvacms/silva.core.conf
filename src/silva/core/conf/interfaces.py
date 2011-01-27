# -*- coding: utf-8 -*-
# Copyright (c) 2002-2010 Infrae. All rights reserved.
# See also LICENSE.txt
# $Id$

from silva.core.conf.schema import ID
from silva.translations import translate as _
from zope.schema import TextLine, Text
from zope.interface import Interface


class IIdentifiedContent(Interface):
    """A content with an identifier.
    """
    id = ID(
        title=_(u"id"),
        description=_(u"No spaces or special characters besides "
                      u"‘_’ or ‘-’ or ‘.’"),
        required=True)

class IBasicTitledContent(IIdentifiedContent):
    """A content with an identifier and a title.
    """
    title = TextLine(
        title=_(u"title"),
        description=_(u"The title will be publicly visible, "
                      u"and is used for the link in indexes."),
        required=True)


class ITitledContent(IBasicTitledContent):
    """A content with an identifier, title, shortitle and description.
    """
    shorttitle = TextLine(
        title=_(u"short title"),
        description=_(u"The primary navigation title. It will be used in the "
                      u"html title if that title is too long. This will also "
                      u"be used in the left navigation menu and breadcrumbs if "
                      u"no navigation title is specified.The title will be "
                      u"publicly visible, "),
        required=False)
    
    description = Text(
        title=_(u"description"),
        description=_(u"The description of the content."),
        required=False)