"""
Seismics related ORM facilities.
"""

from sqlalchemy import Column
from sqlalchemy import Integer, String, ForeignKey
from sqlalchemy.orm import relationship, reconstructor

from ramsis.datamodel.base import (ORMBase, CreationInfoMixin,
                                   RealQuantityMixin, TimeQuantityMixin)
from ramsis.datamodel.signal import Signal


class SeismicCatalog(CreationInfoMixin, ORMBase):
    """
    ORM representation of a seismic catalog.
    """
    # relation: Project
    project_id = Column(Integer, ForeignKey('project.id'))
    project = relationship('Project', back_populates='seismiccatalog')
    # relation: Forecast
    forecast_id = Column(Integer, ForeignKey('forecast.id'))
    forecast = relationship('Forecast',
                            back_populates='seismiccatalog')
    # relation: SeismicEvent
    events = relationship('SeismicEvent',
                          back_populates='seismiccatalog',
                          cascade='all, delete-orphan',
                          order_by='SeismicEvent.datetime_value')

    def __init__(self):
        super(SeismicCatalog, self).__init__()
        self.history_changed = Signal()

    @reconstructor
    def init_on_load(self):
        self.history_changed = Signal()

    def __getitem__(self, item):
        return self.events[item] if self.events else None

    def __iter__(self):
        for e in self.events:
            yield e

    def __len__(self):
        return len(self.events)

#    def events_before(self, end_date, mc=0):
#        """ Returns all events >mc before *end_date* """
#        return [e for e in self.seismic_events
#                if e.date_time < end_date and e.magnitude > mc]
#
#    def clear_events(self, time_range=(None, None)):
#        """
#        Clear all seismic events from the database
#
#        If time_range is given, only the events that fall into the time range
#        are cleared.
#
#        """
#        time_range = (time_range[0] or datetime.min,
#                      time_range[1] or datetime.max)
#
#        to_delete = (s for s in self.seismic_events
#                     if time_range[1] >= s.date_time >= time_range[0])
#        count = 0
#        for s in to_delete:
#            self.seismic_events.remove(s)
#            count += 1
#        log.info('Cleared {} seismic events.'.format(count))
#        self.history_changed.emit()
#
#    def snapshot(self, t):
#        """
#        Create a snapshot of the catalog.
#
#        Deep copies the catalog with all events up to time t
#
#        :return SeismicCatalog: copy of the catalog
#
#        """
#        snapshot = SeismicCatalog()
#        snapshot.catalog_date = datetime.utcnow()
#        snapshot.seismic_events = [s.copy() for s in self.seismic_events
#                                   if s.date_time < t]
#        return snapshot

# class SeismicCatalog


class SeismicEvent(TimeQuantityMixin('datetime'),
                   RealQuantityMixin('x'),
                   RealQuantityMixin('y'),
                   RealQuantityMixin('z'),
                   RealQuantityMixin('magnitude'),
                   ORMBase):
    """
    ORM representation of a seismic event. The definition is based on the
    `QuakeML <https://quake.ethz.ch/quakeml/QuakeML>`_ standard.
    """
    publicid = Column(String, nullable=False)
    originpublicid = Column(String, nullable=False)
    magnitudepublicid = Column(String, nullable=False)
    focalmechanismpublicid = Column(String, nullable=False)

    # relation: SeismicCatalog
    seismiccatalog_id = Column(Integer, ForeignKey('seismiccatalog.id'))
    seismiccatalog = relationship('SeismicCatalog',
                                  back_populates='events')

    def __eq__(self, other):
        if isinstance(other, SeismicEvent):
            return (
                self.publicid == other.publicid and
                self.originpublicid == other.originpublicid and
                self.magnitudepublicid == other.magnitudepublicid and
                self.focalmechanismpublicid == other.focalmechanismpublicid)

        raise TypeError

    def __ne__(self, other):
        return not self.__eq__(other)

    def __str__(self):
        return "M%.1f @ %s" % (self.magnitude_value,
                               self.datetime_value.ctime())

    def __repr__(self):
        return "<{}(datetime={!r}, magnitude={!r})>".format(
            type(self).__name__, self.datetime_value, self.magnitude_value)
#
    # Data attributes (required for copying, serialization to matlab)
#    copy_attrs = ['public_id', 'public_origin_id', 'public_magnitude_id']

#    def in_region(self, region):
#        """
#        Tests if the event is located inside **region**
#
#        :param Cube region: Region to test (cube)
#        :return: True if the event is inside the region, false otherwise
#
#        """
#        return Point(self.x, self.y, self.z).in_cube(region)
#
#    def copy(self):
#        """ Return a copy of this event """
#        copy = SeismicEvent(self.date_time, self.magnitude,
#                            (self.lat, self.lon, self.depth))
#        for attr in SeismicEvent.copy_attrs:
#            setattr(copy, attr, getattr(self, attr))
#        return copy
#
#    def __init__(self, date_time, magnitude, location):
#        self.date_time = date_time
#        self.magnitude = magnitude
#        self.lat, self.lon, self.depth = location

# class SeismicEvent
