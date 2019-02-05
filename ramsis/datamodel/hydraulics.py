"""
Hydraulics related ORM facilities.
"""

# TODO(damb): Remove dependencies unrelated to ORM.
import logging

from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import relationship, reconstructor
from .signal import Signal

from ramsis.datamodel.base import (ORMBase, CreationInfoMixin,
                                   RealQuantityMixin, TimeQuantityMixin)


log = logging.getLogger(__name__)


# NOTE(damb): Currently, basically both Hydraulics and InjectionPlan implement
# the same facilities i.e. a timeseries of hydraulics data shipping some
# metadata. That is why, I propose that they inherit from a common base class.
# Perhaps a mixin approach should be considered, too.

class Hydraulics(CreationInfoMixin, ORMBase):
    """
    ORM representatio of a hydraulics time series.
    """
    # relation: Project
    project_id = Column(Integer, ForeignKey('project.id'))
    project = relationship('Project', back_populates='hydraulics')
    # relation: HydraulicsEvent
    samples = relationship('HydraulicsSample',
                           back_populates='hydraulics',
                           cascade='all')

    # relation: InjectionWell
    well_id = Column(Integer, ForeignKey('injectionwell.id'))
    well = relationship('InjectionWell', back_populates='hydraulics')

    def __init__(self):
        self.history_changed = Signal()

    @reconstructor
    def init_on_load(self):
        self.history_changed = Signal()

    # FIXME(damb): Why is this method necessary if there is *hydws*
#    def import_events(self, importer):
#        """
#        Imports hydraulic events from a csv file by using an EventReporter
#
#        The EventReporter must return the following fields (which must thus
#        be present in the csv file). All imported events are simply added to
#        any existing one. If you want to overwrite existing events, call
#        :meth:`clear_events` first.
#
#        - ``flow_dh``: flow down hole [l/min]
#        - ``flow_xt``: flow @ x-mas tree (top hole) [l/min]
#        - ``pr_dh``: pressure down hole [bar]
#        - ``pr_xt``: pressure @ x-mas tree (top hole) [bar]
#
#        :param importer: an EventReporter object
#        :type importer: EventImporter
#
#        """
#        events = []
#        try:
#            for date, fields in importer:
#                event = HydraulicsEvent(date,
#                                        flow_dh=float(
#                                           fields.get('flow_dh') or 0),
#                                        flow_xt=float(
#                                           fields.get('flow_xt') or 0),
#                                        pr_dh=float(fields.get('pr_dh') or 0),
#                                        pr_xt=float(fields.get('pr_xt') or 0))
#                events.append(event)
#        except Exception:
#            log.error('Failed to import hydraulic events. Make sure '
#                      'the .csv file contains top and bottom hole '
#                      'flow and pressure fields and that the date '
#                      'field has the format dd.mm.yyyyTHH:MM:SS. The '
#                      'original error was ' + traceback.format_exc())
#        else:
#            self.samples.extend(events)
#            log.info('Imported {} hydraulic events.'.format(
#                len(events)))
#            self.history_changed.emit()
#
#    def clear_events(self, time_range=(None, None)):
#        """
#        Clear all hydraulic events from the database
#
#        If time_range is given, only the events that fall into the time range
#
#        """
#        time_range = (time_range[0] or datetime.min,
#                      time_range[1] or datetime.max)
#
#        to_delete = (s for s in self.samples
#                     if time_range[1] >= s.date_time >= time_range[0])
#        count = 0
#        for s in to_delete:
#            self.samples.remove(s)
#            count += 1
#        log.info('Cleared {} hydraulic events.'.format(count))
#        self.history_changed.emit()

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

# class Hydraulics


class InjectionPlan(CreationInfoMixin, ORMBase):
    """
    ORM representation of a planned injection.
    """
    # relation: HydraulicsEvent
    samples = relationship('HydraulicsEvent',
                           back_populates='injection_plan')
    # relation: Scenario
    scenario_id = Column(Integer, ForeignKey('scenario.id'))
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
                      RealQuantityMixin('downholeflow'),
                      RealQuantityMixin('downholepressure'),
                      RealQuantityMixin('topholeflow'),
                      RealQuantityMixin('topholepressure'),
                      ORMBase):
    """
    Represents a hydraulics event (i.e. a flowrate and pressure)

    :param datetime_value: Datetime when the event occurred
    :type datetime_value: :py:class:`datetime.datetime`
    :param float downholeflow_value: Flow downhole :code:`[l/min]`
    :param float downholepressure_value: Pressure downhole :code:`[bar]`
    :param float topholeflow_value: Flow tophole :code:`[l/min]`
    :param float topholepressure_value: Pressure tophole :code:`[bar]`

    .. note::

        *Quantities* are implemented as `QuakeML
        <https://quake.ethz.ch/quakeml>`_ quantities.
    """
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

    # Data attributes (required for flattening)
    # FIXME(damb): Use SQLAlchemy facilities instead; alternatively rename to
    # _fields (see collections.namedtuple)
    data_attrs = ['date_time', 'flow_dh', 'flow_xt', 'pr_dh', 'pr_xt']

    def __init__(self, date_time, flow_dh, flow_xt, pr_dh, pr_xt):
        # TODO(damb): Check why this ctor is required.
        self.datetime_value = date_time
        self.topholeflow_value = flow_dh
        self.topholepressure_value = pr_xt
        self.downholeflow_value = flow_dh
        self.downholepressure_value = pr_xt

    def __str__(self):
        return "Flow: %.1f @ %s" % (self.downholeflow_value,
                                    self.datetime_value.ctime())

    def __repr__(self):
        return "<{}(datetime={!r}, downholeflow={!r})>".format(
            type(self).__name__, self.datetime_value, self.downholeflow_value)

    # TODO(damb): Is using functools.total_ordering an option?
    def __eq__(self, other):
        if isinstance(other, HydraulicsEvent):
            return (
                self.datetime_value == other.datetime_value and
                self.downholeflow_value == other.downholeflow_value and
                self.topholeflow_value == other.topholeflow_value and
                self.downholepressure_value == other.downholepressure_value and
                self.topholepressure_value == other.topholepressure_value)
        raise TypeError

    def __ne__(self, other):
        return not self.__eq__(other)

    # TODO(damb)
    # https://docs.python.org/3/reference/datamodel.html#object.__hash__
    # recommends to mix together the hash values of the components of the
    # object that also play a part in comparison of objects by packing them
    # into a tuple and hashing the tuple
    def __hash__(self):
        return id(self)

# class HydraulicsEvent


# ----- END OF hydraulics.py -----
