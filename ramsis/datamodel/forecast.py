# Copyright 2019, ETH Zurich - Swiss Seismological Service SED
"""
Forecast related ORM facilities.
"""
from enum import Enum
from geoalchemy2 import Geometry
import sqlalchemy
from sqlalchemy import Column, Boolean, Integer, ForeignKey
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import relationship

from ramsis.datamodel.base import (ORMBase, NameMixin, CreationInfoMixin,
                                   EpochMixin)
from ramsis.datamodel.hydraulics import InjectionPlan
from ramsis.datamodel.seismicity import SeismicityModelRun
from ramsis.datamodel.type import JSONEncodedDict


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
    # relation: Project
    project_id = Column(Integer, ForeignKey('project.id'))
    project = relationship('Project', back_populates='forecasts')
    # XXX(damb): Catalogs used for a forecast are snapshots. Thus, a
    # delete-orphan is appropriate.
    # TODO LH: delete-orphan won't work on Generic Associations. Delete orphans
    #   manually (see https://stackoverflow.com/questions/43629364)
    seismiccatalog = relationship('SeismicCatalog',
                                  uselist=False,
                                  back_populates='forecast',
                                  cascade='all')
    well = relationship('InjectionWell',
                        uselist=False,
                        back_populates='forecast')
    scenarios = relationship('ForecastScenario',
                             back_populates='forecast',
                             cascade='all, delete-orphan')

    @hybrid_property
    def duration(self):
        return self.endtime - self.starttime

    @classmethod
    def create_interactive(cls, start_time, end_time, seismicity_models):
        """
        Create and prepare an interactive forecast.

        An "interactive" forecast in this context means a forecast whose
        details will be filled in later by the user. Those details include
        defining additional scenarios and injections plans as well as
        configuring stages and models.

        .. note: We don't associate a well or a catalog yet at the time of
                 creation. This is supposed to be done later when the forecast
                 is executed.

        :param datetime start_time: Start time of the forecast period
        :param datetime end_time: End time of the forecast period
        :param seismicity_models: List of seismicity forecast models to use
            during forecast.
        :type seismicity_models: [ramsis.datamodel.seismicity.SeismicityModel]
        :return: Forecast with default scenario
        :rtype: Forecast
        """
        forecast = Forecast(starttime=start_time,
                            endtime=end_time)

        scenario = ForecastScenario(name='Default Scenario')
        scenario.injectionplan = InjectionPlan()

        # TODO LH: Depending on how the other stages will be implemented we
        #   might want to generalize this by providing the respective models
        #   to each stage on creation.
        scenario.stages = [Stage.create() for Stage in EStage]
        try:
            seismicity_forecast_stage = \
                next((s for s in scenario.stages
                      if isinstance(s, SeismicityForecastStage)), None)
        except StopIteration:
            pass
        else:
            seismicity_forecast_stage.prepare_runs(seismicity_models)

        forecast.scenarios = [scenario]
        return forecast

    def __iter__(self):
        for s in self.scenarios:
            yield s

    def reset(self):
        """
        Resets the forecast by deleting all results

        This keeps the configuration and scenarios but deletes anything that
        is a result of running the forecast, including the catalog snapshot.
        After reset a forecast can be re-run.

        """
        self.seismiccatalog = None
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

    reservoirgeom = Column(Geometry(geometry_type='GEOMETRYZ',
                                    dimension=3,
                                    management=True),
                           nullable=False)

    # relation: Forecast
    forecast_id = Column(Integer, ForeignKey('forecast.id'))
    forecast = relationship('Forecast', back_populates='scenarios')
    # relation: InjectionWell
    well = relationship('InjectionWell',
                        uselist=False,
                        back_populates='scenario')
    # XXX(damb): How to perform the cascade?
    # cascade='all, delete-orphan')
    stages = relationship('ForecastStage', back_populates='scenario',
                          cascade='all, delete-orphan')


class EStage(Enum):

    SEISMICITY = 0
    SEISMICITY_SKILL = 1
    HAZARD = 2
    RISK = 3

    def create(self, *args, **kwargs):
        """
        Create and return a corresponding stage instance

        The *args and **kwargs are directly passed on to the stage initializer.

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
        return stage_map[self](*args, **kwargs)


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
    _type = Column(sqlalchemy.Enum(EStage))

    scenario_id = Column(Integer, ForeignKey('forecastscenario.id'))
    scenario = relationship('ForecastScenario', back_populates='stages')

    # TODO(damb): Calculation status needs to be introduced for forecast
    # stages.

    __mapper_args__ = {
        'polymorphic_identity': 'stage',
        'polymorphic_on': _type,
    }


class SeismicityForecastStage(ForecastStage):
    """
    Concrete :py:class:`ForecastStage` container for
    :py:class:`SeismicityModelRun` implementations.
    """
    __tablename__ = 'seismicityforecaststage'
    id = Column(Integer, ForeignKey('forecaststage.id'), primary_key=True)

    runs = relationship('SeismicityModelRun',
                        back_populates='forecaststage',
                        cascade='all, delete-orphan')

    __mapper_args__ = {
        'polymorphic_identity': EStage.SEISMICITY,
    }

    def prepare_runs(self, models):
        """
        Prepare runs for seismicity models

        :param models: Global seismicity model configs to prepare runs for.

        """
        for model in models:
            run = SeismicityModelRun()
            run.model = model
            self.runs.append(run)

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


class HazardStage(ForecastStage):
    """
    Concrete :py:class:`ForecastStage` container for hazard computations

    """
    # TODO LH: Implement
    __tablename__ = 'hazardstage'
    id = Column(Integer, ForeignKey('forecaststage.id'), primary_key=True)

    __mapper_args__ = {
        'polymorphic_identity': EStage.HAZARD,
    }


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
