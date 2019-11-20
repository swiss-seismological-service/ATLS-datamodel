# Copyright 2019, ETH Zurich - Swiss Seismological Service SED
"""
Seismics related ORM facilities.
"""
import functools

from sqlalchemy import Column
from sqlalchemy import Integer, ForeignKey, LargeBinary
from sqlalchemy.orm import relationship, class_mapper

from ramsis.datamodel.base import (ORMBase, CreationInfoMixin,
                                   RealQuantityMixin, TimeQuantityMixin,
                                   DeleteMultiParentOrphanMixin)
from ramsis.datamodel.utils import clone


class SeismicCatalog(DeleteMultiParentOrphanMixin(['project', 'forecast']),
                     CreationInfoMixin,
                     ORMBase):
    """
    ORM representation of a seismic catalog.
    """
    # relation: Project
    project_id = Column(Integer, ForeignKey('project.id'))
    project = relationship('Project', back_populates='seismiccatalogs')
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
        assert callable(filter_cond) or filter_cond is None, \
            f"Invalid filter_cond: {filter_cond!r}"

        if filter_cond is None:
            def no_filter(s):
                return True

            filter_cond = no_filter

        snap = type(self)()
        snap.events = [e.copy() for e in self.events if filter_cond(e)]
        return snap

    def reduce(self, filter_cond=None):
        """
        Remove events from the catalog.

        :param filter_cond: Callable applied on catalog events when removing
            events. Events matching the condition are removed. If `filter_cond`
            is `None` all events are removed.
        :type filter_cond: callable or None
        """
        try:
            self.events = list(
                filter(lambda e: not filter_cond(e), self.events))
        except TypeError:
            if filter_cond is None:
                self.events = []
            else:
                raise

    def merge(self, cat, starttime=None, endtime=None):
        """
        Merge events from :code:`cat` into the seismic catalog. The merging
        strategy applied is a *delete by time* strategy i.e. events overlapping
        with respect to the :code:`datetime_value` attribute value are
        overwritten with by events from :code:`cat`. In addition, the merging
        time window can be modified using the :code:`starttime` and
        :code:`endtime` parameters.

        :param cat: Seismic catalog the events are merged from.
        :type cat: :py:class:`SeismicCatalog`
        :param starttime: Force datetime to merge from
        :type starttime: :py:class:`datetime.datetime` or None
        :param endtime: Force datetime to merge until
        :type endtime: :py:class:`datetime.datetime` or None

        .. note::
            :code:`starttime` and :code:`endtime` parameters are evaluated
            only if :code:`cat` contains events. To remove events from the
            catalog see :py:meth:`~.SeismicCatalog.reduce`.
        """
        assert isinstance(cat, type(self)), \
            "cat is not of type SeismicCatalog."

        if cat.events:
            if None not in (starttime, endtime) and starttime >= endtime:
                raise ValueError('starttime >= endtime.')

            merge_begin = starttime
            merge_end = endtime
            if not merge_begin:
                merge_begin = min(e.datetime_value for e in cat.events)
            if not merge_end:
                merge_end = max(e.datetime_value for e in cat.events)

            if merge_begin > merge_end:
                raise ValueError('merge_begin > merge_end: '
                                 f'{merge_begin} > {merge_end}')

            def filter_by_overlapping_datetime(e):
                return (e.datetime_value >= merge_begin and
                        e.datetime_value <= merge_end)

            self.reduce(filter_cond=filter_by_overlapping_datetime)

            # merge
            for e in cat.events:
                if (e.datetime_value >= merge_begin and
                        e.datetime_value <= merge_end):
                    self.events.append(e.copy())

    def __getitem__(self, item):
        return self.events[item] if self.events else None

    def __iter__(self):
        for e in self.events:
            yield e

    def __len__(self):
        return len(self.events)

    def __repr__(self):
        return "<{}(creationtime={!r})>".format(
            type(self).__name__, self.creationinfo_creationtime)


@functools.total_ordering
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
        return clone(self, with_foreignkeys=with_foreignkeys)

    def __lt__(self, other):
        if isinstance(other, SeismicEvent):
            return ((self.datetime_value, self.magnitude_value) <
                    (other.datetime_value, other.magnitude_value))

        raise ValueError

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

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(self.quakeml)

    def __repr__(self):
        return "<{}(datetime={!r}, magnitude={!r})>".format(
            type(self).__name__, self.datetime_value, self.magnitude_value)
