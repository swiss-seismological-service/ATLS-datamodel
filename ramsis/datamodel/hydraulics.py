# Copyright 2019, ETH Zurich - Swiss Seismological Service SED
"""
Hydraulics related ORM facilities.
"""

from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship, class_mapper

from ramsis.datamodel.base import (ORMBase, CreationInfoMixin,
                                   RealQuantityMixin, TimeQuantityMixin,
                                   DeleteMultiParentOrphanMixin)
from ramsis.datamodel.utils import clone

# NOTE(damb): Currently, basically both Hydraulics and InjectionPlan implement
# the same facilities i.e. a timeseries of hydraulics data shipping some
# metadata. That is why, I propose that they inherit from a common base class.
# Perhaps a mixin approach should be considered, too.


class Hydraulics(CreationInfoMixin, ORMBase):
    """
    ORM representation of a hydraulic time series.
    """
    # relation: HydraulicSample
    samples = relationship('HydraulicSample',
                           back_populates='hydraulics',
                           single_parent=True,
                           cascade='all')

    # relation: WellSection
    wellsection_id = Column(Integer, ForeignKey('wellsection.id'))
    wellsection = relationship('WellSection', back_populates='hydraulics')

    def snapshot(self, filter_cond=None):
        """
        Snapshot hydraulics.

        :param filter_cond: Filter conditions applied to samples when
            performing the snapshot.
        :type filter_cond: callable or None

        :returns: Snapshot of hydraulics
        :rtype: :py:class:`Hydraulics`
        """
        assert callable(filter_cond) or filter_cond is None, \
            f"Invalid filter_cond: {filter_cond!r}"

        if filter_cond is None:
            def no_filter(s):
                return True

            filter_cond = no_filter

        snap = type(self)()
        snap.samples = [s.copy() for s in self.samples if filter_cond(s)]

        return snap

    def reduce(self, filter_cond=None):
        """
        Remove samples from the hydraulic time series.

        :param filter_cond: Callable applied to hydraulic samples when removing
            events. Events matching the condition are removed. If
            :code:`filter_cond` is :code:`None` all samples are removed.
        :type filter_cond: callable or None
        """
        try:
            self.samples = list(
                filter(lambda e: not filter_cond(e), self.samples))
        except TypeError:
            if filter_cond is None:
                self.samples = []
            else:
                raise

    def merge(self, other):
        """
        Merge samples from :code:`other` into the hydraulics. The merging
        strategy applied is a *delete by time* strategy i.e. samples
        overlapping with respect to the :code:`datetime_value` attribute value
        are overwritten with by samples from :code:`other`.

        :param other: Hydraulics to be merged
        :type other: :py:class:`Hydraulics`
        """
        assert isinstance(other, type(self)) or other is None, \
            "other is not of type Hydraulics."

        if other and other.samples:
            first_sample = min(e.datetime_value for e in other.samples)
            last_sample = max(e.datetime_value for e in other.samples)

            def filter_by_overlapping_datetime(s):
                return (s.datetime_value >= first_sample and
                        s.datetime_value <= last_sample)

            self.reduce(filter_cond=filter_by_overlapping_datetime)

            # merge
            for s in other.samples:
                self.samples.append(s.copy())

    def __eq__(self, other):
        if isinstance(other, Hydraulics):
            if len(self.samples) != len(other.samples):
                return False

            for i, j in zip(self.samples, other.samples):
                if i != j:
                    return False

            return True

        raise ValueError

    def __ne__(self, other):
        return not self.__eq__(other)

    def __iter__(self):
        for s in self.samples:
            yield s

    def __getitem__(self, item):
        return self.samples[item] if self.samples else None

    def __len__(self):
        return len(self.samples)

    def __repr__(self):
        return '<%s(creationtime=%s, samples=%d)>' % (
            type(self).__name__, self.creationinfo_creationtime,
            len(self.samples))


class InjectionPlan(CreationInfoMixin, ORMBase):
    """
    ORM representation of a planned injection.

    .. note::

        Injection plan rules and behaviours:

        * Samples in an injection plan are interpolated linearly
        * This includes interpolation from the last sample of the injection
          history to the first sample of the injection plan
        * A sample must always be provided for the end time of the forecast
          period, except if no sample is provided at all. In this case, it
          is assumed that the injection will stop (default plan).

    """
    # relation: HydraulicSample
    samples = relationship('HydraulicSample',
                           back_populates='injectionplan',
                           single_parent=True,
                           cascade='all')
    # relation: WellSection
    wellsection_id = Column(Integer, ForeignKey('wellsection.id'))
    wellsection = relationship('WellSection', back_populates='injectionplan')

    def __iter__(self):
        for s in self.samples:
            yield s

    def __getitem__(self, item):
        return self.samples[item] if self.samples else None

    def __len__(self):
        return len(self.samples)

    def __repr__(self):
        return '<%s(creationtime=%s, samples=%d)>' % (
            type(self).__name__, self.creationinfo_creationtime,
            len(self.samples))


class HydraulicSample(DeleteMultiParentOrphanMixin(['injectionplan',
                                                    'hydraulics']),
                      TimeQuantityMixin('datetime'),
                      RealQuantityMixin('bottomtemperature', optional=True),
                      RealQuantityMixin('bottomflow', optional=True),
                      RealQuantityMixin('bottompressure', optional=True),
                      RealQuantityMixin('toptemperature', optional=True),
                      RealQuantityMixin('topflow', optional=True),
                      RealQuantityMixin('toppressure', optional=True),
                      RealQuantityMixin('fluiddensity', optional=True),
                      RealQuantityMixin('fluidviscosity', optional=True),
                      RealQuantityMixin('fluidph', optional=True),
                      ORMBase):
    """
    Represents a hydraulic measurement. The definition is based on `QuakeML
    <https://quake.ethz.ch/quakeml/QuakeML2.0/Hydraulic>`_.

    .. note::

        *Quantities* are implemented as `QuakeML
        <https://quake.ethz.ch/quakeml>`_ quantities.
    """
    fluidcomposition = Column(String)

    # relation: Hydraulics
    hydraulics_id = Column(Integer,
                           ForeignKey('hydraulics.id'))
    hydraulics = relationship('Hydraulics',
                              back_populates='samples')
    # relation: InjectionPlan
    injectionplan_id = Column(Integer,
                              ForeignKey('injectionplan.id'))
    injectionplan = relationship('InjectionPlan',
                                 back_populates='samples')

    def copy(self, with_foreignkeys=False):
        """
        Copy a seismic event omitting primary keys.

        :param bool with_foreignkeys: Include foreign keys while copying

        :returns: Copy of hydraulic sample
        :rtype: :py:class:`HydraulicSample`
        """
        return clone(self, with_foreignkeys=with_foreignkeys)

    # TODO(damb): Is using functools.total_ordering an option?
    def __eq__(self, other):
        if isinstance(other, HydraulicSample):
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

    def __str__(self):
        return "<{}(datetime={})>".format(type(self).__name__,
                                          self.datetime_value.isoformat())

    # TODO(damb)
    # https://docs.python.org/3/reference/datamodel.html#object.__hash__
    # recommends to mix together the hash values of the components of the
    # object that also play a role in comparison of objects by packing them
    # into a tuple and hashing the tuple
    def __hash__(self):
        return id(self)
