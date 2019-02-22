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

    def close(self):
        """
        Closes the project file. Before closing, the *will_close* signal is
        emitted. After closing, the project is not usable anymore and will have
        to be reinstatiated if it is needed again.

        """
        self.will_close.emit(self)

    def event_time_range(self):
        """
        Returns the time range of all events in the project as a (start_time,
        end_time) tuple.

        """
        earliest = self.earliest_event()
        latest = self.latest_event()
        start = earliest.date_time if earliest else None
        end = latest.date_time if latest else None
        return start, end

    def earliest_event(self):
        """
        Returns the earliest event in the project, either seismic or hydraulic.

        """
        try:
            es = self.seismic_catalog[0]
            eh = self.well.hydraulics[0]
        except IndexError:
            return None
        if es is None and eh is None:
            return None
        elif es is None:
            return eh
        elif eh is None:
            return es
        else:
            return eh if eh.date_time < es.date_time else es

    def latest_event(self):
        """
        Returns the latest event in the project, either seismic or hydraulic.

        """
        try:
            es = self.seismic_catalog[-1]
            eh = self.well.hydraulics[-1]
        except IndexError:
            return None
        if es is None and eh is None:
            return None
        elif es is None:
            return eh
        elif eh is None:
            return es
        else:
            return eh if eh.date_time > es.date_time else es

# class Project


# ----- END OF project.py -----
