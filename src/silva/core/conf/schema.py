# -*- coding: utf-8 -*-
# Copyright (c) 2002-2010 Infrae. All rights reserved.
# See also LICENSE.txt
# $Id$

from zope.configuration.interfaces import InvalidToken
from zope.interface import implements
from zope.schema import interfaces
from zope import schema

from Products.Silva import mangle
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
        value, err_code = self.args

        if err_code == mangle.Id.CONTAINS_BAD_CHARS:
            return _(u'Sorry, strange characters are in the id. It should only '
                     u'contain letters, digits and ‘_’ or ‘-’ or ‘.’ '
                     u'Spaces are not allowed and the id should start '
                     u'with a letter or digit.')
        elif err_code == mangle.Id.RESERVED_PREFIX:
            prefix = str(value).split('_')[0]+'_'
            return _(u"Sorry, ids starting with ${prefix} are reserved for "
                     u"internal use. Please use another id.",
                     mapping={'prefix': prefix})
        elif err_code == mangle.Id.RESERVED:
            return _(u"Sorry, the id ${id} is reserved for internal use. "
                     u"Please use another id.", mapping={'id': value})
        elif err_code == mangle.Id.IN_USE_CONTENT:
            return _(u"There is already an object with the id ${id} in this "
                     u"folder. Please use a different one.",
                     mapping={'id': value})
        elif err_code == mangle.Id.IN_USE_ASSET:
            return _(u"There is already an asset with the id ${id} in this "
                     u"folder. Please use another id.",
                     mapping={'id': value})
        elif err_code == mangle.Id.RESERVED_POSTFIX:
            return _(u"Sorry, the id ${id} ends with invalid characters. Please "
                     u"use another id.", mapping={'id': value})
        elif err_code == mangle.Id.IN_USE_ZOPE:
            return _(u"Sorry, the id ${id} is already in use by a Zope object. "
                     u"Please use another id.", mapping={'id': value})
        return _(u"(Internal Error): An invalid status ${status_code} occured "
                 u"while checking the id ${id}. Please contact the person "
                 u"responsible for this Silva installation or file a bug report.",
                 mapping={'status_code': err_code, 'id': value})


class ID(schema.TextLine):
    """Zope 3 schema field for mangle.Id fields.
    """

    def _validate(self, value):
        super(ID, self)._validate(value)
        if self.context:
            mangled = mangle.Id(self.context, value)
            err_code = mangled.validate()
            if err_code != mangled.OK:
                raise InvalidID(value, err_code)
        return


class IBytes(interfaces.IBytes):
    """Fields which keeps the FileUpload object.
    """


class Bytes(schema.Bytes):
    """See IStreamBytes
    """

    implements(IBytes)

    def validate(self, value):
        # No validation for the time being.
        pass

