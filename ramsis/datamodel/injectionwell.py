# Copyright (C) 2013, ETH Zurich - Swiss Seismological Service SED
"""
Injection well ORM facilities.
"""

from sqlalchemy import Column, Integer, Boolean, ForeignKey
from sqlalchemy.orm import relationship

from ramsis.datamodel.base import (ORMBase, CreationInfoMixin,
                                   RealQuantityMixin)


class InjectionWell(CreationInfoMixin,
                    RealQuantityMixin('welltipx'),
                    RealQuantityMixin('welltipy'),
                    RealQuantityMixin('welltipz'),
                    ORMBase):
    """
    ORM injection well representation (draft state).

    .. note::

        Dummy implementation. The mapping is currently still in draft state. In
        future, a well should be defined according to the *real world* needs.

    .. note::

        *Point quantities* are implemented as `QuakeML
        <https://quake.ethz.ch/quakeml>`_ real quantities.
    """
    # relation: Project
    project_id = Column(Integer, ForeignKey('project.id'))
    project = relationship('Project', back_populates='injectionwell')

    # relation: Hydraulics
    hydraulics = relationship('Hydraulics', back_populates='injectionwell',
                              cascade='all, delete-orphan')
    # relation: InjectionPlan
    injectionplans = relationship('InjectionPlan',
                                  back_populates='injectionwell',
                                  cascade='all, delete-orphan')

    # TODO(damb): WellSection is still a dummy implementation.
    # relation: WellSection
    sections = relationship('WellSection', back_populates='injectionwell',
                            cascade='all, delete-orphan')

    @property
    def injection_point(self):
        # TODO(damb): To be implemented.
        return 4740.3, 270645.0, 611631.0

# class InjectionWell


class WellSection(ORMBase):
    """
    Dummy ORM implementation of a well section.
    """
    # TODO(damb): E.g. add positional information
    cased = Column(Boolean)
    # relation: InjectionWell
    injectionwell_id = Column(Integer, ForeignKey('injectionwell.id'))
    injectionwell = relationship('InjectionWell', back_populates='sections')

# class WellSection
