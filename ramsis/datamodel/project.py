# Copyright 2019, ETH Zurich - Swiss Seismological Service SED
"""
Project related ORM facilities.
"""

from geoalchemy2 import Geometry
from sqlalchemy import Column, String
from sqlalchemy.orm import relationship

from ramsis.datamodel.base import (ORMBase, CreationInfoMixin, NameMixin,
                                   UniqueOpenEpochMixin)
from ramsis.datamodel.settings import ProjectSettings


class Project(CreationInfoMixin, NameMixin, UniqueOpenEpochMixin, ORMBase):
    """
    RT-RAMSIS project ORM representation. :py:class:`Project` is the root
    object of the RT-RAMSIS data model.
    """
    description = Column(String)
    # XXX(damb): Should be nullable.
    referencepoint = Column(Geometry(geometry_type='POINTZ',
                                     dimension=3,
                                     management=True),
                            )
    # XXX(damb): Spatial reference system in Proj4 notation representing the
    # local coordinate system;
    # see also: https://www.gdal.org/classOGRSpatialReference.html
    spatialreference = Column(String, nullable=False)

    # relationships
    wells = relationship('InjectionWell',
                         back_populates='project',
                         cascade='all')
    forecasts = relationship('Forecast',
                             order_by='Forecast.starttime',
                             back_populates='project',
                             cascade='all, delete-orphan')
    seismiccatalog = relationship('SeismicCatalog',
                                  back_populates='project',
                                  cascade='all',
                                  uselist=False)
    settings = relationship('ProjectSettings', uselist=False)

    # TODO(damb):
    # * Implement a project factory/builder instead of using/abusing the
    #   constructor

    def __init__(self, **kwargs):
        """
        Project initializer

        Instantiates settings and *real-time* the project dependent
        infrastructure (i.e. a seismic catalog and injectionwell).
        """
        super().__init__(**kwargs)
        self.settings = ProjectSettings()

    def forecast_iter(self, filter_cond=None):
        """
        Return a forecast iterator.

        :param callable filter_cond: Callable used for forecast filtering. If
            :code:`None` an iterator over all available forecasts is returned.
        """
        if filter_cond is None:
            def no_filter(f):
                return True

            filter_cond = no_filter

        for fc in self.forecasts:
            if filter_cond(fc):
                yield fc
