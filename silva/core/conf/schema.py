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
    

from Products.Silva.i18n import translate as _
from zope.i18n import translate

class InvalidID(InvalidValue):

    def doc(self):
        value, err_code = self.args
        
        if err_code == mangle.Id.CONTAINS_BAD_CHARS:
            return _("Sorry, strange characters are in the id. It should only"
                     "contain letters, digits and &#8216;_&#8217; or &#8216;-&#8217; or"
                     "&#8216;.&#8217; Spaces are not allowed in Internet addresses,"
                     "and the id should start with a letter or digit.")
        elif err_code == mangle.Id.RESERVED_PREFIX:
            prefix = str(value).split('_')[0]+'_'
            return _("Sorry, ids starting with ${prefix} are reserved for "
                     "internal use. Please use another id.",
                     mapping={'prefix': prefix})
        elif err_code == mangle.Id.RESERVED:
            return _("Sorry, the id ${id} is reserved for internal use. "
                     "Please use another id.", mapping={'id': value})
        elif err_code == mangle.Id.IN_USE_CONTENT:
            return _("There is already an object with the id ${id} in this "
                     "folder. Please use a different one.",
                     mapping={'id': value})
        elif err_code == mangle.Id.IN_USE_ASSET:
            return _("There is already an asset with the id ${id} in this "
                     "folder. Please use another id.",
                     mapping={'id': value})
        elif err_code == mangle.Id.RESERVED_POSTFIX:
            return _("Sorry, the id ${id} ends with invalid characters. Please "
                     "use another id.", mapping={'id': value})
        elif err_code == mangle.Id.IN_USE_ZOPE:
            return _("Sorry, the id ${id} is already in use by a Zope object. "
                     "Please use another id.", mapping={'id': value})
        return _("(Internal Error): An invalid status ${status_code} occured "
                 "while checking the id ${id}. Please contact the person "
                 "responsible for this Silva installation or file a bug report.""",
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
