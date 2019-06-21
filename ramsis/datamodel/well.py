# Copyright 2019, ETH Zurich - Swiss Seismological Service SED
"""
Injection well ORM facilities.
"""

from sqlalchemy import Column, Integer, Boolean, String, ForeignKey
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import relationship

from ramsis.datamodel.base import (ORMBase, CreationInfoMixin, PublicIDMixin,
                                   UniqueOpenEpochMixin, RealQuantityMixin)


class InjectionWell(PublicIDMixin,
                    CreationInfoMixin,
                    RealQuantityMixin('bedrockdepth', optional=True),
                    ORMBase):
    """
    ORM injection well representation.

    .. note::

        *Point quantities* are implemented as `QuakeML
        <https://quake.ethz.ch/quakeml>`_ real quantities.
    """
    # relation: Project
    project_id = Column(Integer, ForeignKey('project.id'))
    project = relationship('Project', back_populates='wells')
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
                   key=lambda x: x.topdepth_value).toplongitude_value

    @hybrid_property
    def latitude(self):
        # min topdepth defines top-section
        return min([s for s in self.sections],
                   key=lambda x: x.topdepth_value).toplatitude_value

    @hybrid_property
    def depth(self):
        # max bottomdepth defines bottom-section
        return max([s.bottomdepth_value for s in self.sections])

    @hybrid_property
    def injectionpoint(self):
        """
        Injection point of the borehole. It is defined by the uppermost
        section's bottom with casing and an open bottom.

        .. note::

            The implementation requires boreholes to be linear.
        """
        isection = min([s for s in self.sections
                       if s.casingdiameter_value and not s.bottomclosed],
                       key=lambda x: x.bottomdepth_value, default=None)

        if not isection:
            raise ValueError('Cased borehole has a closed bottom.')

        return (isection.bottomlongitude_value,
                isection.bottomlatitude_value,
                isection.bottomdepth_value)

    def __iter__(self):
        for s in self.sections:
            yield s

    def __repr__(self):
        return ("<{}(publicid={!r}, longitude={}, latitude={}, "
                "depth={})>").format(type(self).__name__, self.publicid,
                                     self.longitude, self.latitude, self.depth)


class WellSection(PublicIDMixin,
                  CreationInfoMixin,
                  UniqueOpenEpochMixin,
                  RealQuantityMixin('toplongitude'),
                  RealQuantityMixin('toplatitude'),
                  RealQuantityMixin('topdepth'),
                  RealQuantityMixin('bottomlongitude'),
                  RealQuantityMixin('bottomlatitude'),
                  RealQuantityMixin('bottomdepth'),
                  RealQuantityMixin('holediameter', optional=True),
                  RealQuantityMixin('casingdiameter', optional=True),
                  ORMBase):
    """
    ORM implementation of a well section.
    """
    topclosed = Column(Boolean, default=False)
    bottomclosed = Column(Boolean, default=False)
    sectiontype = Column(String)
    casingtype = Column(String)
    description = Column(String)

    # relation: InjectionWell
    well_id = Column(Integer, ForeignKey('injectionwell.id'))
    well = relationship('InjectionWell', back_populates='sections')

    # relation: Hydraulics
    hydraulics = relationship('Hydraulics',
                              back_populates='wellsection',
                              uselist=False,
                              cascade='all, delete-orphan')
    # relation: InjectionPlan
    injectionplan = relationship('InjectionPlan',
                                 back_populates='wellsection',
                                 uselist=False,
                                 cascade='all, delete-orphan')
