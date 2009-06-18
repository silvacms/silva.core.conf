# Copyright (c) 2002-2009 Infrae. All rights reserved.
# See also LICENSE.txt
# $Id$

from zope.configuration.interfaces import InvalidToken
from zope.i18n import translate
from zope.interface import implements
from zope.schema import interfaces
from zope import schema, component
from zope.app.intid.interfaces import IIntIds

from Products.Silva import mangle

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


from Products.Silva.i18n import translate as _
from zope.i18n import translate

class InvalidID(interfaces.InvalidValue):

    def doc(self):
        value, err_code = self.args

        if err_code == mangle.Id.CONTAINS_BAD_CHARS:
            return _('Sorry, strange characters are in the id. It should only'
                     'contain letters, digits and "_" or "-" or'
                     '"." Spaces are not allowed in Internet addresses,'
                     'and the id should start with a letter or digit.')
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


class IContentReference(interfaces.IObject):
    """Field to store a reference to an object
    """

    def fromRelativePath(context, path):
        """Return the value from a relative path.
        """

    def toRelativePath(context, value):
        """Return the value as a relative path.
        """


class ContentReference(schema.Object):
    """Zoep 3 schema field to store a reference to an object.
    """

    implements(IContentReference)

    def fromRelativePath(self, context, path):
        parts = path.split('/')
        if not parts[0]:
            # path start with '/'
            context = context.get_root()
            parts.pop(0)
        return context.restrictedTraverse(parts)

    def toRelativePath(self, context, value):
        return mangle.Path.fromObject(context.getPhysicalPath(), value)


_marker = object()

class ContentReferenceProperty(object):

    def __init__(self, name):
        self.__name = name
        self.__cache_name = '_v_%s' % name

    def __get__(self, inst, klass):
        if inst is None:
            return self

        cache = inst.__dict__.get(self.__cache_name, _marker)
        if cache is not _marker:
            return cache

        iid = inst.__dict__.get(self.__name, None)
        if iid is not None:
            utility = component.getUtility(IIntIds)
            obj =  utility.getObject(iid)
            inst.__dict__[self.__cache_name] = obj
            return obj
        return None

    def __set__(self, inst, value):
        iid = None
        if value is not None:
            utility = component.getUtility(IIntIds)
            iid = utility.register(value)
        inst.__dict__[self.__cache_name] = value
        inst.__dict__[self.__name] = iid
        inst.__dict__['_p_changed'] = True


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

