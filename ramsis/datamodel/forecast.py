# This is <forecast.py>
# ----------------------------------------------------------------------------
#
# Copyright (c) 2018 by Lukas Heiniger (SED, ETHZ),
#                       Daniel Armbruster (SED, ETHZ)
#
# REVISIONS and CHANGES
#    2018/01/24   V1.0   Daniel Armbruster (damb)
#
# ============================================================================
"""
Forecast related ORM facilities.
"""

from math import log, factorial

from geoalchemy2 import Geometry
from sqlalchemy import Column, Boolean, Enum, Integer, ForeignKey
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import relationship

from ramsis.datamodel.base import (ORMBase, NameMixin, CreationInfoMixin,
                                   EpochMixin)
from ramsis.datamodel.model import EModel
from ramsis.datamodel.type import JSONEncodedDict
from ramsis.datamodel.signal import Signal

# TODO(damb): Add facilities from calculationstatus.py


class ForecastSet(ORMBase):
    """
    Implements a container for :py:class:`Forecast` objects.
    """
    project_id = Column(Integer, ForeignKey('project.id'))
    project = relationship('Project', back_populates='forecastset')

    forecasts = relationship('Forecast', back_populates='forecastset',
                             cascade='all, delete-orphan',
                             order_by='Forecast.interval_starttime')

    def __iter__(self):
        for f in self.forecasts:
            yield f

    # __iter__ ()

    """
    def __init__(self):
        self.forecasts_changed = Signal()

    @reconstructor
    def init_on_load(self):
        self.forecasts_changed = Signal()

    def add_forecast(self, forecast):
        # Appends a new forecast and fires the changed signal
        self.forecasts.append(forecast)
        self.forecasts_changed.emit()

    def forecast_at(self, t):
        # Return the forecast scheduled for t
        try:
            return next(f for f in self.forecasts if f.forecast_time == t)
        except StopIteration:
            return None
    """

# class ForecastSet


class Forecast(CreationInfoMixin,
               EpochMixin('interval', epoch_type='finite', column_prefix=''),
               NameMixin, ORMBase):
    """
    Implementation of a forecast. :py:class:`Forecast` represents a top-level
    interface for a *RT-RAMSIS* forecast.

    A forecast maps a collection of :py:class:`Scenario` instances (including
    their corresponding results) and the real *input* data i.e. both a
    :py:class:`SeismicCatalog` and :py:class:`Hydraulics`.
    """
    forecastset_id = Column(Integer, ForeignKey('forecastset.id'))
    forecastset = relationship('ForecastSet', back_populates='forecasts')

    # TODO(damb): delete-orphane to be handled manually?
    seismiccatalog = relationship('SeismicCatalog',
                                  uselist=False,
                                  back_populates='forecast',
                                  cascade='all, delete-orphan')

    hydraulics = relationship('Hydraulics',
                              uselist=False,
                              back_populates='forecast',
                              cascade='all, delete-orphan')

    # relation: Scenario
    scenarios = relationship('ForecastScenario', back_populates='forecast',
                             cascade='all, delete-orphan')

    @hybrid_property
    def duration(self):
        return self.endtime - self.starttime

    def __iter__(self):
        for s in self.scenarios:
            yield s

    # __iter__ ()

    """
    @property
    def complete(self):
        # FIXME: also check all stages are complete
        if len(self.input.scenarios) == len(self.results):
            return True
        else:
            return False

    @property
    def project(self):
        # Shortcut to the project
        return self.forecast_set.project

    def add_scenario(self, scenario):
        # Appends a new scenario and fires the changed signal
        self.input.scenarios.append(scenario)
        self.input.forecast.forecast_set.forecasts_changed.emit()

    def remove_scenario(self, scenario):
        # Removes a scenario and fires the changed signal
        self.input.scenarios.remove(scenario)
        self.input.forecast.forecast_set.forecasts_changed.emit()
    """

# class Forecast


class ForecastScenario(NameMixin, ORMBase):
    # TODO(damb): to be refactored
    """
    A :py:class:`ForecastScenario` describes the forecast input data which
    is configurable by the end-user.

    In general, a :py:class:`ForecastScenario` provides a container for:
        * scenario specific end-user configuration,
        * an :py:class:`InjectionPlan`,
        * a set of :py:class:`ForecastStage` objects,
        * geometric description of a reservoir.
    """
    config = Column(MutableDict.as_mutable(JSONEncodedDict))

    reservoirgeom = Column(Geometry(geometry_type='GEOMETRYZ', dimension=3),
                           nullable=False)

    # relation: Forecast
    forecast = Column(Integer, ForeignKey('forecast.id'))
    forecast = relationship('Forecast', back_populates='scenarios')
    # relation: InjectionPlan
    injection_plan = relationship('InjectionPlan',
                                  back_populates='scenario',
                                  cascade='all, delete-orphan',
                                  uselist=False)

    """
    # ForecastResult relation
    forecast_result_id = Column(Integer, ForeignKey('forecast_results.id'))
    forecast_result = relationship('ForecastResult',
                                   back_populates='scenario')
    # Summary status
    # These are only informational only (for the user) and are computed from
    # individual calculation statuses and stage configurations.
    PENDING = 'Pending'  # Nothing has been computed yet
    COMPLETE = 'Complete'  # All calculations complete
    INCOMPLETE = 'Incomplete'  # Some pending calculations
    RUNNING = 'Running'  # Currently computing

    def __init__(self):
        super().__init__()
        self.config = {
            'run_is_forecast': True,
            'run_hazard': True,
            'run_risk': True,
            'disabled_models': []
        }
        self.scenario_changed = Signal()

    @property
    def summary_status(self):
        fr = self.forecast_result
        if fr is None:
            return self.PENDING
        all_results = list(fr.model_results.values()) + \
                      [fr.hazard_result, fr.risk_result]
        if all(r.state == CS.PENDING for r in all_results if r):
            return self.PENDING
        if any(r.state == CS.RUNNING for r in all_results if r):
            return self.RUNNING
        if self.config['run_risk'] and not fr.risk_result.status.finished:
            return self.INCOMPLETE
        if self.config['run_hazard'] and not fr.hazard_result.status.finished:
            return self.INCOMPLETE
        if self.config['run_is_forecast']:
            expected = []
            scenario_disabled = self.config['disabled_models']
            for id, conf in self.project.settings['forecast_models'].items():
                if conf['enabled'] and id not in scenario_disabled:
                    expected.append(id)
            if any(id not in fr.model_results for id in expected):
                return self.INCOMPLETE
            if any(fr.model_results[id].status.finished is False
                   for id in expected):
                return self.INCOMPLETE
        return self.COMPLETE

    def has_errors(self):
        fr = self.forecast_result
        if fr is None:
            return False
        all_results = list(fr.model_results.values()) + \
                      [fr.hazard_result, fr.risk_result]
        return any(r.state == CS.ERROR for r in all_results if r)

    @reconstructor
    def init_on_load(self):
        self.scenario_changed = Signal()
    """


# class ForecastScenario


class ForecastStage(ORMBase):
    """
    Abstract base class for RT-RAMSIS forecast stages.
    :py:class:`ForecastStage` is intended grouping :py:class`ModelRun`
    implementations of a certain type.

    Concrete implementations are used by a :py:class:`ForecastScenario`.

    .. note::

        Inheritance is implemented following the `SQLAlchemy Joined Table
        Inheritance
        <https://docs.sqlalchemy.org/en/latest/orm/inheritance.html#joined-table-inheritance>`_
        paradigm.
    """
    config = Column(MutableDict.as_mutable(JSONEncodedDict))
    enabled = Column(Boolean, default=True)
    _type = Column(Enum(EModel))

    # TODO(damb): Calculation status needs to be introduced for forecast
    # stages.

    __mapper_args__ = {
        'polymorphic_identity': 'stage',
        'polymorphic_on': _type,
    }

# class ForecastStage


class SeismicityForecastStage(ForecastStage):
    """
    Concrete :py:class:`ForecastStage` container for
    :py:class:`SeismicityModelRun` implementations.
    """
    __tablename__ = 'seismicityforecaststage'
    id = Column(Integer, ForeignKey('forecaststage.id'), primary_key=True)

    runs = relationship('SeismicityModelRun',
                        back_populates='forecast_stage',
                        cascades='all, delete-orphan')

    __mapper_args__ = {
        'polymorphic_identity': EModel.SEISMICITY,
    }

# class SeismicityForecastStage


def log_likelihood(forecast, observation):
    """
    Computes the log likelihood of an observed rate given a forecast

    The forecast value is interpreted as expected value of a poisson
    distribution. The function expects scalars or numpy arrays as input. In the
    latter case it computes the LL for each element.

    :param float forecast: forecasted rate
    :param float observation: observed rate
    :return: log likelihood for each element of the input

    """
    ll = -forecast + observation * log(forecast) - log(factorial(observation))
    return ll


# ----- END OF forecast.py -----
