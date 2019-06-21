# Copyright 2019, ETH Zurich - Swiss Seismological Service SED
"""
Project related ORM facilities.
"""

from geoalchemy2 import Geometry
from sqlalchemy import Column, String
from sqlalchemy.orm import relationship

from ramsis.datamodel.base import (ORMBase, CreationInfoMixin, NameMixin,
                                   UniqueOpenEpochMixin)
from ramsis.datamodel.seismics import SeismicCatalog
from ramsis.datamodel.settings import ProjectSettings


class Project(CreationInfoMixin, NameMixin, UniqueOpenEpochMixin, ORMBase):
    """
    RT-RAMSIS project ORM representation. :py:class:`Project` is the root
    object of the RT-RAMSIS data model.
    """
    description = Column(String)
    referencepoint = Column(Geometry(geometry_type='POINTZ',
                                     dimension=3,
                                     srid=4326,
                                     management=True),
                            nullable=False)
    # XXX(damb): Spatial reference system in Proj4 notation representing the
    # local coordinate system;
    # see also: https://www.gdal.org/classOGRSpatialReference.html
    spatialreference = Column(String, nullable=False)

    # relationships
    relationship_config = {'back_populates': 'project',
                           'cascade': 'all, delete-orphan'}
    wells = relationship('InjectionWell', **relationship_config)
    forecasts = relationship('Forecast', **relationship_config)
    # TODO LH: delete-orphan won't work on Generic Associations. Delete orphans
    #   manually (see https://stackoverflow.com/questions/43629364)
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

        Insantiates settings and the main seismic catalog which are both
        integral parts of :class:`Project`.
        """
        super().__init__(**kwargs)
        self.settings = ProjectSettings()
        if 'starttime' in kwargs:
            self.settings.forecast_start = kwargs['starttime']
        self.seismiccatalog = SeismicCatalog()

