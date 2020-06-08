# Copyright 2019, ETH Zurich - Swiss Seismological Service SED
"""
Forecast related ORM facilities.
"""
from enum import Enum
import itertools
import sqlalchemy
from sqlalchemy import Column, Boolean, Integer, ForeignKey
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import relationship

from ramsis.datamodel.base import (ORMBase, NameMixin, CreationInfoMixin,
                                   EpochMixin)
from ramsis.datamodel.type import JSONEncodedDict
from ramsis.datamodel.utils import clone
from ramsis.datamodel.hazard import HazardModel


class Forecast(CreationInfoMixin,
               EpochMixin('interval', epoch_type='finite', column_prefix=''),
               NameMixin, ORMBase):
    """
    Implementation of a forecast. :py:class:`Forecast` represents a top-level
    interface for a *RT-RAMSIS* forecast.

    A forecast maps a collection of :py:class:`Scenario` instances (including
    their corresponding results) and the real *input* data i.e. both a
    :py:class:`SeismicCatalog` and :py:class:`InjectionWell`.
    """
    config = Column(MutableDict.as_mutable(JSONEncodedDict))
    enabled = Column(Boolean, default=True)
    status = relationship('Status', back_populates='forecast',
                          uselist=False, cascade='all, delete-orphan', lazy="joined")

    # relation: Project
    project_id = Column(Integer, ForeignKey('project.id'))
    project = relationship('Project', back_populates='forecasts',
                              lazy="joined")
    seismiccatalog = relationship('SeismicCatalog', uselist=True,
                                  back_populates='forecast',
                                  cascade='all')
    well = relationship('InjectionWell', uselist=True,
                        back_populates='forecast',
                        cascade='all')
    scenarios = relationship('ForecastScenario',
                             back_populates='forecast',
                             cascade='all, delete-orphan')

    @hybrid_property
    def duration(self):
        return self.endtime - self.starttime

    def __iter__(self):
        for s in self.scenarios:
            yield s

    def append(self, scenario):
        if isinstance(scenario, ForecastScenario):
            self.scenarios.append(scenario)

    def clone(self, with_results=False):
        """
        Clone a forecast.

        :param bool with_results: If :code:`True`, append results and related
            data while cloning, otherwise results are excluded.
        """
        new = clone(self, with_foreignkeys=False)
        if with_results:
            new.seismiccatalog = self.seismiccatalog
            new.well = self.well

        for scenario in self.scenarios:
            new.append(scenario.clone(with_results=False))

        return new

    def reset(self):
        """
        Resets the forecast by deleting all results

        This keeps the configuration and scenarios but deletes anything that
        is a result of running the forecast, including the catalog snapshot.
        After reset a forecast can be re-run.

        """
        self.seismiccatalog = []
        for scenario in self.scenarios:
            scenario.reset()


class ForecastScenario(NameMixin, ORMBase):
    """
    A :py:class:`ForecastScenario` describes the forecast input data which
    is configurable by the end-user.

    In general, a :py:class:`ForecastScenario` provides a container for:
        * scenario specific end-user configuration,
        * an :py:class:`InjectionWell`,
        * a set of :py:class:`ForecastStage` objects,
        * geometric description of a reservoir.

    .. note::

        Currently, a scenario does only cover a single injection well scenario
        (:code:`uselist=False`).

    """
    config = Column(MutableDict.as_mutable(JSONEncodedDict))
    enabled = Column(Boolean, default=True)
    status = relationship('Status', back_populates='scenario',
                          uselist=False, cascade='all, delete-orphan', lazy="joined")

    reservoirgeom = Column(MutableDict.as_mutable(JSONEncodedDict))

    # relation: Forecast
    forecast_id = Column(Integer, ForeignKey('forecast.id'))
    forecast = relationship('Forecast', back_populates='scenarios', lazy="joined")
    # relation: InjectionWell
    well = relationship('InjectionWell',
                        back_populates='scenario',
                        uselist=False,
                        cascade='all')
    # XXX(damb): How to perform the cascade?
    # cascade='all, delete-orphan')
    stages = relationship('ForecastStage', back_populates='scenario',
                          cascade='all, delete-orphan')

    def __contains__(self, stage_type):
        for s in self.stages:
            if s._type == stage_type:
                return True
        return False

    def __getitem__(self, stage_type):
        if not isinstance(stage_type, EStage):
            raise TypeError(f"{stage_type!r}")

        for s in self.stages:
            if s._type == stage_type:
                return s
        raise KeyError(f"{stage_type!r}")

    def clone(self, with_results=False):
        """
        Clone a scenario.

        :param bool with_results: If :code:`True`, append results and related
            data while cloning, otherwise results are excluded.
        """
        new = clone(self, with_foreignkeys=False)
        # XXX(damb): The future borehole/hydraulics cover the entire forecast
        # period. The data is interpretated accordingly by the models
        # themselves.
        new.well = self.well

        for stage in self.stages:
            new.stages.append(stage.clone(with_results=with_results))

        return new

    def reset(self):
        """
        Resets the forecast scenario by deleting all results

        This keeps the configuration and scenarios but deletes any computed
        results. After that, the scenario can be re-run

        """
        for stage in self.stages:
            stage.reset()


class EStage(Enum):
    SEISMICITY = 0
    SEISMICITY_SKILL = 1
    HAZARD = 2
    RISK = 3


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
    status = relationship('Status', back_populates='stage',
                          uselist=False, cascade='all, delete-orphan', lazy="joined")
    _type = Column(sqlalchemy.Enum(EStage))

    scenario_id = Column(Integer, ForeignKey('forecastscenario.id'))
    scenario = relationship('ForecastScenario', back_populates='stages', lazy="joined")

    # TODO(damb): Calculation status needs to be introduced for forecast
    # stages.

    __mapper_args__ = {
        'polymorphic_identity': 'stage',
        'polymorphic_on': _type,
    }

    @staticmethod
    def create(stage_type, *args, **kwargs):
        """
        Create and return a corresponding forecast stage instance

        The *args and **kwargs are directly passed on to the stage initializer.

        :param EStage stage_type: Type of stage to create
        :param args: Positional init params for stage
        :param kwargs: Keyword init params for stage
        :return: Instance of stage
        :rtype: ForecastStage
        """
        stage_map = {
            EStage.SEISMICITY: SeismicityForecastStage,
            EStage.SEISMICITY_SKILL: SeismicitySkillStage,
            EStage.HAZARD: HazardStage,
            EStage.RISK: RiskStage
        }
        return stage_map[stage_type](*args, **kwargs)

    def clone(self, with_results=False):
        """
        Clone a forecast stage.

        :param bool with_results: If :code:`True`, append results and related
            data while cloning, otherwise results are excluded.
        """
        return clone(self, with_foreignkeys=False)

    def reset(self):
        """
        Resets the stage by deleting all results

        This keeps the configuration but deletes any computed results. After
        that, the stage can be re-run

        """
        raise NotImplementedError

    @hybrid_property
    def result_times(self):
        result_times = [run.result_times for run in self.runs if run.enabled]
        retval = list(set(itertools.chain(*result_times)))
        if not retval:
            raise ValueError("Seismicity run results contains no samples. "
                    "SeismicityStage.id: {self.id}")
        return retval



class SeismicityForecastStage(ForecastStage):
    """
    Concrete :py:class:`ForecastStage` container for
    :py:class:`SeismicityModelRun` implementations.
    """
    __tablename__ = 'seismicityforecaststage'
    id = Column(Integer, ForeignKey('forecaststage.id'), primary_key=True)

    runs = relationship('SeismicityModelRun',
                        back_populates='forecaststage',
                        cascade='all, delete-orphan',
                        lazy="joined")

    __mapper_args__ = {
        'polymorphic_identity': EStage.SEISMICITY,
    }

    def clone(self, with_results=False):
        """
        Clone a seismicity forecast stage.

        :param bool with_results: If :code:`True`, append results and related
            data while cloning, otherwise results are excluded.
        """
        new = clone(self, with_foreignkeys=False)

        for run in self.runs:
            new.runs.append(run.clone(with_results=with_results))

        return new

    def reset(self):
        for run in self.runs:
            # ToDo LH: not sure if we should reset to EStatus.PENDING instead
            #   Does a run always have a status? Or only after it has started?
            # TODO(damb): Use EStatus.INITIALIZED instead
            run.status = None


class SeismicitySkillStage(ForecastStage):
    """
    Concrete :py:class:`ForecastStage` container for seismicity model skill
    testing.

    """
    # TODO LH: Implement
    __tablename__ = 'seismicityskillstage'
    id = Column(Integer, ForeignKey('forecaststage.id'), primary_key=True)

    __mapper_args__ = {
        'polymorphic_identity': EStage.SEISMICITY_SKILL,
    }

    def reset(self):
        pass


class HazardStage(ForecastStage):
    """
    Concrete :py:class:`ForecastStage` container for hazard computations

    """
    __tablename__ = 'hazardstage'
    id = Column(Integer, ForeignKey('forecaststage.id'), primary_key=True)

    runs = relationship('HazardModelRun',
                        back_populates='forecaststage',
                        cascade='all, delete-orphan',
                        lazy="joined")
    model_id = Column(Integer, ForeignKey("hazardmodel.id"))
    model = relationship(HazardModel, lazy="joined")

    __mapper_args__ = {
        'polymorphic_identity': EStage.HAZARD,
    }

    def reset(self):
        pass


class RiskStage(ForecastStage):
    """
    Concrete :py:class:`ForecastStage` container for risk computations

    """
    # TODO LH: Implement
    __tablename__ = 'riskstage'
    id = Column(Integer, ForeignKey('forecaststage.id'), primary_key=True)

    __mapper_args__ = {
        'polymorphic_identity': EStage.RISK,
    }

    def reset(self):
        pass
