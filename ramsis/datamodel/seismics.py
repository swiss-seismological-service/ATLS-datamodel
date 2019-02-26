"""
Seismics related ORM facilities.
"""

from sqlalchemy import Column
from sqlalchemy import Integer, ForeignKey, LargeBinary
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

    def snapshot(self, filter_cond=None):
        """
        Create a snapshot of the catalog.

        :param filter_cond: Callable applied on catalog events when creating
            the snapshot
        :type filter_cond: callable or None

        :returns: Snapshot of the catalog
        :rtype: :py:class:`SeismicCatalog`
        """
        snap = type(self)()
        snap.events = filter(filter_cond, self.events)

        return snap

    # snapshot ()

    def reduce(self, filter_cond=None):
        """
        Remove events from the catalog.

        :param filter_cond: Callable applied on catalog events when removing
            events. Events matching the condition are removed. If `filter_cond`
            is `None` all events are removed.
        :type filter_cond: callable or None
        """
        try:
            self.events = filter(lambda e: not filter_cond(e), self.events)
        except TypeError:
            if filter_cond is None:
                self.events = []

    # reduce ()

    def dumps(self, oformat="QUAKEML", encoding=None, **kwargs):
        """
        Return a string representing a seismic catalog in the format specified.

        :param str oformat: Seismic catalog output format. See the *Supported
            Formats* list, below.
        :param encoding: Encoding of the output catalog
        :type encoding: str or None

        :returns: Seismic catalog in the output format specified
        :rtype: bytes or str

        **Supported Formats**:

            - `QUAKEML`
        """
        QUAKEML_HEADER = (
            b'<?xml version="1.0" encoding="UTF-8"?>'
            b'<q:quakeml xmlns="http://quakeml.org/xmlns/bed/1.2" '
            b'xmlns:q="http://quakeml.org/xmlns/quakeml/1.2">'
            b'<eventParameters publicID="smi:scs/0.7/EventParameters">')

        QUAKEML_FOOTER = b'</eventParameters></q:quakeml>'

        if oformat != "QUAKEML":
            raise ValueError('Unsupported output format')

        # XXX(damb): Create a seismic catalog by simply concatenating the
        # QuakeML formatted events
        retval = QUAKEML_HEADER
        for e in self.events:
            retval += e.quakeml

        retval += QUAKEML_FOOTER

        if encoding:
            retval = retval.decode(encoding)

        return retval

    # dumps ()

    def __getitem__(self, item):
        return self.events[item] if self.events else None

    def __iter__(self):
        for e in self.events:
            yield e

    def __len__(self):
        return len(self.events)

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
    quakeml = Column(LargeBinary, nullable=False)

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

        raise ValueError

    # __eq__ ()

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(self.quakeml)

    def __str__(self):
        return "M%.1f @ %s" % (self.magnitude_value,
                               self.datetime_value.ctime())

    def __repr__(self):
        return "<{}(datetime={!r}, magnitude={!r})>".format(
            type(self).__name__, self.datetime_value, self.magnitude_value)

# class SeismicEvent


# ----- END OF seismics.py -----
