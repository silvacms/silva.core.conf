# -*- coding: utf-8 -*-
# Copyright (c) 2002-2010 Infrae. All rights reserved.
# See also LICENSE.txt
# $Id$

import re

from zope.configuration.interfaces import InvalidToken
from zope.interface import implements
from zope.schema import interfaces
from zope.schema.vocabulary import SimpleTerm, SimpleVocabulary
from zope import schema

from Products.Silva import mangle
from silva.core.interfaces import IVersion, ISilvaObject
from silva.translations import translate as _


# the TupleTokens field was created to support multiple values in the
# depends_on attribute of silva:extension.  There is a Tokens field in
# zope.configuration.fields, but it extends from schema.List it
# doesn't support the 'default' parameter, as the default then has to
# be a list, and lists aren't hashable.  TupleTokens supports default
# values

class TupleTokens(schema.Tuple):

    implements(interfaces.IFromUnicode)

    def fromUnicode(self, u):
        u = u.strip()
        if u:
            vt = self.value_type.bind(self.context)
            values = []
            for s in u.split():
                try:
                    v = vt.fromUnicode(s)
                except schema.ValidationError, v:
                    raise InvalidToken("%s in %s" % (v, u))
                else:
                    values.append(v)
            values = tuple(values)
        else:
            values = ()
        self.validate(values)
        return values


class InvalidID(interfaces.InvalidValue):

    def doc(self):
        return self.args[0]


class ID(schema.TextLine):
    """Zope 3 schema field for mangle.Id fields.
    """

    def _validate(self, value):
        super(ID, self)._validate(value)
        if self.context:
            context = self.context
            if IVersion.providedBy(context) or ISilvaObject.providedBy(context):
                context = context.get_container()
            error = mangle.Id(context, value).verify()
            if error is not None:
                raise InvalidID(error.reason)
        return


class IBytes(interfaces.IBytes):
    """Fields which keeps the FileUpload object.
    """


class Bytes(schema.Bytes):
    """See IBytes
    """
    implements(IBytes)

    def validate(self, value):
        # No validation for the time being.
        pass


class IHTMLText(interfaces.IText):
    """HTML text.
    """


class HTMLText(schema.Text):
    """See IHTMLText
    """
    implements(IHTMLText)



class ICropCoordinates(interfaces.ITextLine):
    """ interfaces for crop coordinates schema field
    """


CROP_COORDINATES_FORMAT = re.compile(
    r'^([0-9]+)[Xx]([0-9]+)-([0-9]+)[Xx]([0-9]+)')


class InvalidCropCoordinates(interfaces.InvalidValue):

    def doc(self):
        return _(u"Invalid crop coordinates.")


class CropCoordinates(schema.TextLine):
    """ crop coordinates schema field
    """
    implements(ICropCoordinates)

    def _validate(self, value):
        if not CROP_COORDINATES_FORMAT.match(value):
            raise InvalidCropCoordinates()


class Term(SimpleTerm):

    def __init__(self, value, token=None, title=None, icon=None):
        super(Term, self).__init__(value, token, title)
        self.icon = icon


class Vocabulary(SimpleVocabulary):
    pass

