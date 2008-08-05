# Copyright (c) 2002-2008 Infrae. All rights reserved.
# See also LICENSE.txt
# $Id$

from zope.interface import implements
from zope.schema.interfaces import IFromUnicode, InvalidValue
from zope.configuration.interfaces import InvalidToken
from zope import schema

from Products.Silva import mangle

#the TupleTokens field was created to support multiple values
# in the depends_on attribute of silva:extension.  There is a
# Tokens field in zope.configuration.fields, but it extends from schema.List
# it doesn't support the 'default' parameter, as the default then has to be
# a list, and lists aren't hashable.  TupleTokens supports default values

class TupleTokens(schema.Tuple):

    implements(IFromUnicode)

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
    

class ID(schema.TextLine):
    """Zope 3 schema field for mangle.Id fields.
    """

    def _validate(self, value):
        super(ID, self)._validate(value)
        if self.context:
            mangled = mangle.Id(self.context, value)
            err_code = mangled.validate()
            if err_code != mangled.OK:
                raise InvalidValue
        return
