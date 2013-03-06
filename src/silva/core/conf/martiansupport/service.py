# -*- coding: utf-8 -*-
# Copyright (c) 2011-2013 Infrae. All rights reserved.
# See also LICENSE.txt


import martian

from zope import component
from silva.core.interfaces import IRoot
from silva.core.interfaces.events import IInstallRootServicesEvent
from silva.core.services.base import SilvaService
from silva.core.conf.martiansupport.directives import default_service


class InstallServiceGrokker(martian.ClassGrokker):
    """This grokker register new services to be added when a new Silva
    Root is installed.
    """
    martian.component(SilvaService)
    martian.directive(default_service, name='info')

    def execute(self, factory, config, info, **kw):
        """Register the creation of a Silva service at installation
        time.
        """
        if info is None:
            return False

        info.prepare(factory)
        config.action(
            discriminator=None,
            callable=component.provideHandler,
            args=(info.install, (IRoot, IInstallRootServicesEvent)))
        return True
