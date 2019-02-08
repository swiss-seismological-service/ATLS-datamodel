# Copyright (C) 2013, ETH Zurich - Swiss Seismological Service SED

"""
Provides a class to manage Ramsis project data
"""
import datetime

from geoalchemy2 import Geometry
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship, reconstructor

from ramsis.datamodel.base import (ORMBase, CreationInfoMixin, NameMixin)
from ramsis.datamodel.forecast import ForecastSet
from ramsis.datamodel.hydraulics import Hydraulics
from ramsis.datamodel.seismics import SeismicCatalog
from ramsis.datamodel.settings import ProjectSettings
from ramsis.datamodel.signal import Signal
from ramsis.datamodel.well import InjectionWell


class Project(CreationInfoMixin, NameMixin, ORMBase):
    """
    RT-RAMSIS project ORM representation. :py:class:`Project` corresponds to
    the root object of the RT-RAMSIS data model.
    """
    description = Column(String)
    referencepoint = Column(Geometry(geometry_type='POINT_ZM',
                                     dimension=4,
                                     srid=4326), nullable=False)
    # XXX(damb): Spatial reference system in Proj4 notation representing the
    # local coordinate system;
    # see also: https://www.gdal.org/classOGRSpatialReference.html
    spatialreference = Column(String, nullable=False)

    # relationships
    relationship_config = {'back_populates': 'project',
                           'cascade': 'all, delete-orphan'}
    well = relationship('InjectionWell', **relationship_config)
    hydraulics = relationship('Hydraulics', **relationship_config)
    forecastset = relationship('ForecastSet', **relationship_config)
    seismiccatalog = relationship('SeismicCatalog', **relationship_config)
    # relation: Settings
    settings_id = Column(Integer, ForeignKey('settings.id'))
    settings = relationship('Settings')

    # TODO(damb):
    # * Implement a project factory/builder instead of using/abusing the
    #   constructor

    def __init__(self, name=''):
        super(Project, self).__init__()
        self.name = name
        self.creationinfo_creationtime = datetime.datetime.utcnow().replace(
            second=0, microsecond=0)

        self.forecastset = ForecastSet()
        self.hydraulics = Hydraulics()
        self.seismiccatalog = SeismicCatalog()
        self.well = InjectionWell()

        self.settings = ProjectSettings()

        # FIXME: hardcoded for testing purposes
        # These are the basel well tip coordinates (in CH-1903)
        self.injection_well = InjectionWell(4740.3, 270645.0, 611631.0)

        self._project_time = self.start_date
        self.settings['forecast_start'] = self.creationinfo_creationtime
        self.settings.commit()

        # Signals
        self.will_close = Signal()
        self.project_time_changed = Signal()

    # __init__ ()

    @reconstructor
    def init_on_load(self):
        self.will_close = Signal()
        self.project_time_changed = Signal()
        self._project_time = self.start_date

    def close(self):
        """
        Closes the project file. Before closing, the *will_close* signal is
        emitted. After closing, the project is not usable anymore and will have
        to be reinstatiated if it is needed again.

        """
        self.will_close.emit(self)

    @property
    def project_time(self):
        return self._project_time

    # Event information

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
            eh = self.injection_history[0]
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
            eh = self.injection_history[-1]
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

    # TODO (damb): Use property-setter
    def update_project_time(self, t):
        self._project_time = t
        self.project_time_changed.emit(t)
