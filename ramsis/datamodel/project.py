# Copyright (C) 2013, ETH Zurich - Swiss Seismological Service SED

"""
Provides a class to manage Ramsis project data
"""

from datetime import datetime, timedelta

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, \
    PickleType
from sqlalchemy.orm import relationship, reconstructor
from .settings import ProjectSettings
from .seismics import SeismicCatalog
from .hydraulics import InjectionHistory
from .forecast import ForecastSet
from .injectionwell import InjectionWell
from .eqstats import SeismicRateHistory

from ramsis.datamodel.base import (ORMBase, CreationInfoMixin, NameMixin)
from ramsis.datamodel.signal import Signal


class Project(CreationInfoMixin, NameMixin, ORMBase):
    """
    RT-RAMSIS project ORM representation. :py:class:`Project` corresponds to
    the root object of the RT-RAMSIS data model.
    """
    description = Column(String)

    # TODO(damb): Check the purpose of this property.
    end_date = Column(DateTime)

    # XXX(damb): Reference point used when projecting data into a local CS.
    # To be verified if PickleType suits the needs.
    reference_point = Column(PickleType)

    relationship_config = {'back_populates': 'project',
                           'cascade': 'all, delete-orphan'}

    injectionwell = relationship('InjectionWell',
                                 **relationship_config)
    hydraulics = relationship('Hydraulics',
                              **relationship_config)
    forecastset = relationship('ForecastSet',
                               **relationship_config)
    # XXX(heilukas): Handle delete-orphan manually for seismic catalogs
    seismiccatalog = relationship('SeismicCatalog',
                                  back_populates='project',
                                  cascade='all')

    # relation: Settings
    settings_id = Column(Integer, ForeignKey('settings.id'))
    settings = relationship('Settings')


    # TODO(damb):
    # * Projects are saved within a store; hence it would be better style to
    #   implement a utility function such as Project.save(store) instead of
    #   passing the store parameter as a ctor arg.
    # * Check reference point implementation. Verify if a POINT_Z would suit
    #   better our needs.
    # * 
    def __init__(self, store=None, title=''):
        super(Project, self).__init__()
        self.store = store
        self.seismic_catalog = SeismicCatalog()
        self.injection_history = InjectionHistory()
        self.rate_history = SeismicRateHistory()
        self.forecast_set = ForecastSet()
        self.title = title
        self.start_date = datetime.utcnow().replace(second=0, microsecond=0)
        self.end_date = self.start_date + timedelta(days=365)
        self.reference_point = {'lat': 47.379, 'lon': 8.547, 'h': 450.0}
        self.settings = ProjectSettings()

        # Signals
        self.will_close = Signal()
        self.project_time_changed = Signal()

        # These inform us when new IS forecasts become available

        # FIXME: hardcoded for testing purposes
        # These are the basel well tip coordinates (in CH-1903)
        self.injection_well = InjectionWell(4740.3, 270645.0, 611631.0)

        self._project_time = self.start_date
        self.settings['forecast_start'] = self.start_date
        self.settings.commit()
        if self.store:
            self.store.session.add(self)

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

    def save(self):
        if self.store:
            self.store.commit()

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
