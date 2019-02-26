"""
Injection well ORM facilities.
"""

from sqlalchemy import Column, Integer, Boolean, ForeignKey
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import relationship

from ramsis.datamodel.base import (ORMBase, CreationInfoMixin,
                                   RealQuantityMixin)


# FIXME(damb): Caution, this is a dummy implementation.

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
    project = relationship('Project', back_populates='well')
    # relation: Forecast
    forecast_id = Column(Integer, ForeignKey('forecast.id'))
    forecast = relationship('Forecast', back_populates='well')

    # relation: Hydraulics
    hydraulics = relationship('Hydraulics',
                              back_populates='well',
                              cascade='all, delete-orphan')
    # relation: InjectionPlan
    injectionplans = relationship('InjectionPlan',
                                  back_populates='well',
                                  cascade='all, delete-orphan')

    # TODO(damb): WellSection is still a dummy implementation.
    # relation: WellSection
    sections = relationship('WellSection',
                            back_populates='well',
                            cascade='all, delete-orphan')

    @hybrid_property
    def injectionpoint(self):
        return self.welltipx_value, self.welltipy_value, self.welltipz_value

# class InjectionWell


class WellSection(ORMBase):
    """
    Dummy ORM implementation of a well section.
    """
    # TODO(damb): E.g. add positional information
    cased = Column(Boolean)
    # relation: InjectionWell
    well_id = Column(Integer, ForeignKey('injectionwell.id'))
    well = relationship('InjectionWell', back_populates='sections')

# class WellSection


# ----- END OF well.py -----
