"""
Hydraulics related ORM facilities.
"""

from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship, class_mapper

from ramsis.datamodel.base import (ORMBase, CreationInfoMixin,
                                   RealQuantityMixin, TimeQuantityMixin)

# NOTE(damb): Currently, basically both Hydraulics and InjectionPlan implement
# the same facilities i.e. a timeseries of hydraulics data shipping some
# metadata. That is why, I propose that they inherit from a common base class.
# Perhaps a mixin approach should be considered, too.


class Hydraulics(CreationInfoMixin, ORMBase):
    """
    ORM representatio of a hydraulics time series.
    """
    # relation: HydraulicsEvent
    samples = relationship('HydraulicsEvent',
                           back_populates='hydraulics',
                           single_parent=True,
                           cascade='all, delete-orphan')

    # relation: InjectionWell
    well_id = Column(Integer, ForeignKey('injectionwell.id'))
    well = relationship('InjectionWell', back_populates='hydraulics')

    def __iter__(self):
        for s in self.samples:
            yield s

    # __iter__ ()

    def __getitem__(self, item):
        return self.samples[item] if self.samples else None

    def __repr__(self):
        return '<%s(creationtime=%s, samples=%d)>' % (
            type(self).__name__, self.creationinfo_creationtime,
            len(self.samples))

# class Hydraulics


class InjectionPlan(CreationInfoMixin, ORMBase):
    """
    ORM representation of a planned injection.
    """
    # relation: HydraulicsEvent
    samples = relationship('HydraulicsEvent',
                           back_populates='injectionplan',
                           single_parent=True,
                           cascade='all, delete-orphan')
    # relation: ForecastScenario
    scenario_id = Column(Integer, ForeignKey('forecastscenario.id'))
    scenario = relationship('ForecastScenario',
                            back_populates='injectionplan')

    # relation: InjectionWell
    well_id = Column(Integer, ForeignKey('injectionwell.id'))
    well = relationship('InjectionWell', back_populates='injectionplans')

    def __iter__(self):
        for s in self.samples:
            yield s

    # __iter__ ()

    def __getitem__(self, item):
        return self.samples[item] if self.samples else None

    def __repr__(self):
        return '<%s(creationtime=%s, samples=%d)>' % (
            type(self).__name__, self.creationinfo_creationtime,
            len(self.samples))

    # __repr__ ()

# class InjectionPlan


class HydraulicsEvent(TimeQuantityMixin('datetime'),
                      RealQuantityMixin('downholetemperature'),
                      RealQuantityMixin('downholeflow'),
                      RealQuantityMixin('downholepressure'),
                      RealQuantityMixin('topholetemperature'),
                      RealQuantityMixin('topholeflow'),
                      RealQuantityMixin('topholepressure'),
                      RealQuantityMixin('fuiddensity'),
                      RealQuantityMixin('fluidviscosity'),
                      RealQuantityMixin('fluidph'),
                      ORMBase):
    """
    Represents a hydraulics event. The definition is based on `QuakeML
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

    # TODO(damb): Is using functools.total_ordering an option?
    def __eq__(self, other):
        if isinstance(other, HydraulicsEvent):
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
        return "Flow: %.1f @ %s" % (self.downholeflow_value,
                                    self.datetime_value.ctime())

    def __repr__(self):
        return "<{}(datetime={!r}, downholeflow={!r})>".format(
            type(self).__name__, self.datetime_value, self.downholeflow_value)

    # TODO(damb)
    # https://docs.python.org/3/reference/datamodel.html#object.__hash__
    # recommends to mix together the hash values of the components of the
    # object that also play a role in comparison of objects by packing them
    # into a tuple and hashing the tuple
    def __hash__(self):
        return id(self)

# class HydraulicsEvent


# ----- END OF hydraulics.py -----
