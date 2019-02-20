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

from geoalchemy2 import Geometry
from sqlalchemy import Column, Boolean, Enum, Integer, ForeignKey
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import relationship

from ramsis.datamodel.base import (ORMBase, NameMixin, CreationInfoMixin,
                                   EpochMixin)
from ramsis.datamodel.model import EModel
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
    project_id = Column(Integer, ForeignKey('project.id'))
    project = relationship('Project', back_populates='forecasts')
    # XXX(damb): Catalogs used for a forecast are snapshots. Thus, a
    # delete-orphan is appropriate.
    seismiccatalog = relationship('SeismicCatalog',
                                  uselist=False,
                                  back_populates='forecast',
                                  cascade='all, delete-orphan')
    well = relationship('InjectionWell',
                        uselist=False,
                        back_populates='forecast')
    scenarios = relationship('ForecastScenario',
                             back_populates='forecast',
                             cascade='all, delete-orphan')

    @hybrid_property
    def duration(self):
        return self.endtime - self.starttime

    def __iter__(self):
        for s in self.scenarios:
            yield s

    # __iter__ ()

# class Forecast


class ForecastScenario(NameMixin, ORMBase):
    """
    A :py:class:`ForecastScenario` describes the forecast input data which
    is configurable by the end-user.

    In general, a :py:class:`ForecastScenario` provides a container for:
        * scenario specific end-user configuration,
        * an :py:class:`InjectionPlan`,
        * a set of :py:class:`ForecastStage` objects,
        * geometric description of a reservoir.

    .. note::

        Currently, a scenario does only cover a single injection plan including
        the reservoir geometry.

    """
    config = Column(MutableDict.as_mutable(JSONEncodedDict))

    reservoirgeom = Column(Geometry(geometry_type='GEOMETRYZ',
                                    dimension=3,
                                    management=True,
                                    use_st_prefix=False),
                           nullable=False)

    # relation: Forecast
    forecast_id = Column(Integer, ForeignKey('forecast.id'))
    forecast = relationship('Forecast', back_populates='scenarios')
    # relation: InjectionPlan
    injectionplan = relationship('InjectionPlan',
                                 uselist=False,
                                 back_populates='scenario',
                                 cascade='all, delete-orphan')

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
                        back_populates='forecaststage',
                        cascade='all, delete-orphan')

    __mapper_args__ = {
        'polymorphic_identity': EModel.SEISMICITY,
    }

# class SeismicityForecastStage


# ----- END OF forecast.py -----
