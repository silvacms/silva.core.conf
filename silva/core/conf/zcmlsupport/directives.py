# Copyright (c) 2002-2008 Infrae. All rights reserved.
# See also LICENSE.txt
# $Id$

from zope import interface
from zope import schema

from zope.configuration.fields import GlobalObject, PythonIdentifier, Path

from silva.core.conf.fields import TupleTokens

class IExtensionDirective(interface.Interface):
    """Register Product as a Silva Extension.
    """
    name = PythonIdentifier(
        title=u"Name",
        required=True,
        )

    title = schema.TextLine(
        title=u"Title",
        required=True,
        )

    depends = TupleTokens(
        value_type=PythonIdentifier(),
        title=u"Dependency",
        default=(u'Silva',),
        )

class IContentDirective(interface.Interface):
    """Register the implementation of an non-versioned content type for Silva.
    """    
    extension_name = PythonIdentifier(
        title=u"Extension name",
        required=True,
        )
    
    content = GlobalObject(
        title=u"Content class",
        required=True,
        )

    priority = schema.Float(
        title=u"The priority in the add list",
        required=False,
        default=0.0
        )

    icon = Path(
        title=u"The path of the icon",
        required=False,
        )

    content_factory = GlobalObject(
        title=u"manage_addSomething factory method",
        description=(u"manage_addSomething factory method; use for "
                     u"backwards compatibility purposes only. Normally "
                     u"this factory can be autogenerated."),
        required=False,
        )

    zmi_addable = schema.Bool(
        title=u"Appear in ZMI Add list?",
        description=(u"allow this object to appear in the ZMI Add list"),
        required=False,
        default=False
        )

class IVersionedContentDirective(IContentDirective):
    """Register the implementation of a versioned content type for
    Silva.
    """

    version = GlobalObject(
        title=u"Version class",
        required=True,
        )

    version_factory = GlobalObject(
        title=u"manage_addSomethingVersion factory method",
        description=(u"manage_addSomethingVersion factory method; use for "
                     u"backwards compatibility purposes only. Normally "
                     u"this factory can be autogenerated."),
        required=False,
        )

