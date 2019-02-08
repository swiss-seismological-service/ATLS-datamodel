"""
Seismics related ORM facilities.
"""

from sqlalchemy import Column
from sqlalchemy import Integer, ForeignKey, PickleType
from sqlalchemy.orm import relationship, class_mapper

from ramsis.datamodel.base import (ORMBase, CreationInfoMixin,
                                   RealQuantityMixin, TimeQuantityMixin)


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

    Due to integrity issues with `fdsnws-event
    <https://www.fdsn.org/webservices/>`_ :py:class:`SeismicEvent` is designed
    to store the original `QuakeML <https://quake.ethz.ch/quakeml/QuakeML>`_
    XML representation. Besides, data relevant for RT-RAMSIS is extracted from
    the XML, if necessary converted, and kept alongside using a flat
    representation.
    """
    quakeml = Column(PickleType)

    # relation: SeismicCatalog
    seismiccatalog_id = Column(Integer, ForeignKey('seismiccatalog.id'))
    seismiccatalog = relationship('SeismicCatalog',
                                  back_populates='events')

    def copy(self, with_foreignkeys=False):
        """
        Copy a seismic event omitting primary keys.

        :param bool with_foreignkeys: Include foreign keys while copying

        :returns: Copy of seismic event
        :rtype: :py:class:`SeismicEvent`
        """
        mapper = class_mapper(type(self))
        new = type(self)()

        pk_keys = set([c.key for c in mapper.primary_key])
        rel_keys = set([c.key for c in mapper.relationships])
        omit = pk_keys | rel_keys

        if with_foreignkeys:
            fk_keys = set([c.key for c in mapper.columns if c.foreign_keys])
            omit = omit | fk_keys

        for attr in [p.key for p in mapper.iterate_properties
                     if p.key not in omit]:
            try:
                value = getattr(self, attr)
                setattr(new, attr, value)
            except AttributeError:
                pass

        return new

    # copy ()

    def __eq__(self, other):
        if isinstance(other, SeismicEvent):
            mapper = class_mapper(type(self))

            pk_keys = set([c.key for c in mapper.primary_key])
            rel_keys = set([c.key for c in mapper.relationships])
            fk_keys = set([c.key for c in mapper.columns if c.foreign_keys])

            omit = pk_keys | rel_keys | fk_keys

            return all(getattr(self, attr) == getattr(other, attr)
                       for attr in [p.key for p in mapper.iterate_properties
                                    if p.key not in omit])

        raise TypeError

    # __eq__ ()

    def __ne__(self, other):
        return not self.__eq__(other)

    def __str__(self):
        return "M%.1f @ %s" % (self.magnitude_value,
                               self.datetime_value.ctime())

    def __repr__(self):
        return "<{}(datetime={!r}, magnitude={!r})>".format(
            type(self).__name__, self.datetime_value, self.magnitude_value)
#
#    def copy(self):
#        """ Return a copy of this event """
#        copy = SeismicEvent(self.date_time, self.magnitude,
#                            (self.lat, self.lon, self.depth))
#        for attr in SeismicEvent.copy_attrs:
#            setattr(copy, attr, getattr(self, attr))
#        return copy
#
# class SeismicEvent
