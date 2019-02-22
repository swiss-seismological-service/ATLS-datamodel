# Copyright (C) 2019, ETH Zurich - Swiss Seismological Service SED
"""
Project related ORM facilities.
"""

from geoalchemy2 import Geometry
from sqlalchemy import Column, String
from sqlalchemy.orm import relationship

from ramsis.datamodel.base import (ORMBase, CreationInfoMixin, NameMixin,
                                   UniqueOpenEpochMixin)


class Project(CreationInfoMixin, NameMixin, UniqueOpenEpochMixin, ORMBase):
    """
    RT-RAMSIS project ORM representation. :py:class:`Project` is the root
    object of the RT-RAMSIS data model.
    """
    description = Column(String)
    referencepoint = Column(Geometry(geometry_type='POINTZM',
                                     dimension=4,
                                     srid=4326,
                                     management=True,
                                     use_st_prefix=False),
                            nullable=False)
    # XXX(damb): Spatial reference system in Proj4 notation representing the
    # local coordinate system;
    # see also: https://www.gdal.org/classOGRSpatialReference.html
    spatialreference = Column(String, nullable=False)

    # relationships
    relationship_config = {'back_populates': 'project',
                           'cascade': 'all, delete-orphan'}
    well = relationship('InjectionWell', **relationship_config)
    forecasts = relationship('Forecast', **relationship_config)
    seismiccatalog = relationship('SeismicCatalog', **relationship_config)
    settings = relationship('ProjectSettings')

    # TODO(damb):
    # * Implement a project factory/builder instead of using/abusing the
    #   constructor

# class Project


# ----- END OF project.py -----
