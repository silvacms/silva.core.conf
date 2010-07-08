# -*- coding: utf-8 -*-
# Copyright (c) 2002-2010 Infrae. All rights reserved.
# See also LICENSE.txt
# $Id$

from silva.core.conf.schema import ID
from silva.translations import translate as _
from zope.schema import TextLine
from zope.interface import Interface


class IIdentifiedContent(Interface):
    """A content with an identifier.
    """
    id = ID(
        title=_(u"id"),
        description=_(u"No spaces or special characters besides "
                      u"‘_’ or ‘-’ or ‘.’"),
        required=True)


class ITitledContent(IIdentifiedContent):
    """A content with an identifier and a title.
    """
    title = TextLine(
        title=_(u"title"),
        description=_(u"The title will be publicly visible, "
                      u"and is used for the link in indexes."),
        required=True)
