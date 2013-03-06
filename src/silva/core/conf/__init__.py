# -*- coding: utf-8 -*-
# Copyright (c) 2002-2013 Infrae. All rights reserved.
# See also LICENSE.txt

# Martian directive for contents
from silva.core.conf.martiansupport.directives import *

# Grokcore helpers
from grokcore.component import subscribe
from grokcore import component
from grokcore.view import template, templatedir, require

from zope.interface import implements


def protect(permission):
    """Protect an adapter method with a permission.
    """
    from AccessControl.security import checkPermission
    from zExceptions import Unauthorized

    def wrapper(func):

        def wrapped(self, *args, **kwargs):
            if not checkPermission(permission, self.context):
                raise Unauthorized(
                    "You don't have access to %s on %s" % (
                        func.func_name,
                        '/'.join(self.context.getPhysicalPath())))
            return func(self, *args, **kwargs)

        return wrapped

    return wrapper
