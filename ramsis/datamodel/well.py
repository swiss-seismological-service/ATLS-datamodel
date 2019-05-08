# Copyright 2019, ETH Zurich - Swiss Seismological Service SED
"""
Injection well ORM facilities.
"""

from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import relationship

from ramsis.datamodel.base import (ORMBase, CreationInfoMixin,
                                   RealQuantityMixin)


# FIXME(damb): Caution, this is a dummy implementation.

class InjectionWell(CreationInfoMixin, ORMBase):
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
    # relation: ForecastScenario
    scenario_id = Column(Integer, ForeignKey('forecastscenario.id'))
    scenario = relationship('ForecastScenario', back_populates='well')

    # relation: WellSection
    sections = relationship('WellSection',
                            back_populates='well',
                            cascade='all, delete-orphan')

    @hybrid_property
    def longitude(self):
        # min topdepth defines top-section
        return min([s for s in self.sections],
                   key=lambda x: x.topdepth).toplongitude

    @hybrid_property
    def latitude(self):
        # min topdepth defines top-section
        return min([s for s in self.sections],
                   key=lambda x: x.topdepth).toplatitude

    @hybrid_property
    def depth(self):
        # max bottomdepth defines bottom-section
        return max([s.bottomdepth for s in self.sections])

    @hybrid_property
    def injectionpoint(self):
        """
        Injection point of the borehole. It is defined by the furthermost
        bottom section without casing.
        """
        isection = min([s for s in self.sections
                       if (not s.casingtype and
                           (not s.casingdiameter or s.casingdiameter == 0))],
                       key=lambda x: x.bottomdepth)

        return (isection.bottomlongitude,
                isection.bottomlatitude,
                isection.bottomdepth)


class WellSection(CreationInfoMixin, ORMBase):
    """
    ORM implementation of a well section.
    """
    # relation: InjectionWell
    well_id = Column(Integer, ForeignKey('injectionwell.id'))
    well = relationship('InjectionWell', back_populates='sections')

    # relation: Hydraulics
    hydraulics = relationship('Hydraulics',
                              back_populates='wellsection',
                              cascade='all, delete-orphan')
    # relation: InjectionPlan
    injectionplans = relationship('InjectionPlan',
                                  back_populates='wellsection',
                                  cascade='all, delete-orphan')
