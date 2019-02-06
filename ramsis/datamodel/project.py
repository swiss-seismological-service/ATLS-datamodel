# Copyright (C) 2013, ETH Zurich - Swiss Seismological Service SED

"""
Provides a class to manage Ramsis project data
"""
import datetime

from sqlalchemy import (Column, Integer, String, DateTime, ForeignKey,
                        PickleType, event)
from sqlalchemy.orm import relationship, reconstructor, Session

from ramsis.datamodel.base import (ORMBase, CreationInfoMixin, NameMixin)
from ramsis.datamodel.forecast import ForecastSet
from ramsis.datamodel.hydraulics import Hydraulics
from ramsis.datamodel.seismics import SeismicCatalog
from ramsis.datamodel.settings import ProjectSettings
from ramsis.datamodel.signal import Signal
from ramsis.datamodel.well import InjectionWell


def _delete_orphans(entity):
    """
    Factory function returning an `SQLAlchemy
    event handler <https://docs.sqlalchemy.org/en/latest/core/event.html>`_
    deleting orphaned child entities from projects.

    :param entity: Child entity of project
    """

    @event.listens_for(Session, 'after_flush')
    def delete(session, ctx):
        """
        Seismic catalogs can have different kinds of parents (i.e.
        Project<->SeismicCatalog corresponds to a many to many relation), so a
        simple 'delete-orphan' statement on the relation doesn't work. Instead
        we check after each flush to the db if there are any orphaned catalogs
        and delete them if necessary.

        :param Session session: The current session
        """
        if any(isinstance(i, entity) for i in session.dirty):
            query = session.query(entity).\
                    filter_by(project=None)
            for orphan in query.all():
                session.delete(orphan)

    # delete ()

# _delete_orphans ()


_ENTITIES = (SeismicCatalog, InjectionWell)


for e in _ENTITIES:
    _delete_orphans(e)


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

    well = relationship('InjectionWell', **relationship_config)
    hydraulics = relationship('Hydraulics', **relationship_config)
    forecastset = relationship('ForecastSet', **relationship_config)
    # XXX(heilukas): Handle delete-orphan manually for seismic catalogs
    seismiccatalog = relationship('SeismicCatalog',
                                  back_populates='project',
                                  cascade='all')

    # relation: Settings
    settings_id = Column(Integer, ForeignKey('settings.id'))
    settings = relationship('Settings')

    # TODO(damb):
    # * Check reference point implementation. Verify if a POINT_Z would suit
    #   better our needs.
    # * Implement a project factory instead of using/abusing the constructor

    def __init__(self, name=''):
        super(Project, self).__init__()
        self.name = name

        self.forecastset = ForecastSet()
        self.hydraulics = Hydraulics()
        self.seismiccatalog = SeismicCatalog()
        self.well = InjectionWell()

        self.start_date = datetime.datetime.utcnow().replace(
            second=0, microsecond=0)
        self.end_date = self.start_date + datetime.timedelta(days=365)

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
