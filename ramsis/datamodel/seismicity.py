# Copyright 2019, ETH Zurich - Swiss Seismological Service SED
"""
Seismicity prediction related ORM facilities.
"""

from geoalchemy2 import Geometry

from sqlalchemy import Column, String, Integer, ForeignKey
from sqlalchemy.orm import relationship, backref

from ramsis.datamodel.base import ORMBase, RealQuantityMixin
from ramsis.datamodel.model import Model, ModelRun, EModel


# FIXME(damb): Maintaining both a SeismicityModel, a SeismicityModelRun and on
# top a ForecastStage seems somehow cumbersome. In particular, when every
# single class ships its own config.
# Proposed strategy:
# * SeismicityModel.config provides the default configuration of a concrete
#   implementation of a seismicity model
# * SeismicityModelRun.config is the concrete configuration of the model at
#   when executed
# * Concrete implementations of a ForecastStage (e.g. SeismicityForecastStage)
#   sets default parameters using the *config* property for a group of models
#   from a certain type (e.g. seismicity).
#
# Configuration parameters MUST be propagated accordingly.


class SeismicityModel(Model):
    """
    ORM representation of a seismicity forecast model.
    :py:class:`SeismicityModel` instances are inteded to provide templates for
    :py:class:SeismicityModelRun` implementations.
    """
    __tablename__ = 'seismicitymodel'
    id = Column(Integer, ForeignKey('model.id'), primary_key=True)

    url = Column(String)

    runs = relationship('SeismicityModelRun',
                        cascade='all, delete-orphan')

    __mapper_args__ = {
        'polymorphic_identity': EModel.SEISMICITY,
    }

    def __repr__(self):
        return '<%s(name=%s, url=%s)>' % (type(self).__name__, self.name,
                                          self.url)


class SeismicityModelRun(ModelRun):
    """
    ORM representation of a seismicity forecast model run.
    """
    __tablename__ = 'seismicitymodelrun'
    id = Column(Integer, ForeignKey('modelrun.id'), primary_key=True)

    # relation: SeismicityModel
    model_id = Column(Integer, ForeignKey('seismicitymodel.id'))
    model = relationship('SeismicityModel',
                         back_populates='runs')
    # relation: SeismicityForecastStage
    forecaststage_id = Column(Integer,
                              ForeignKey('seismicityforecaststage.id'))
    forecaststage = relationship('SeismicityForecastStage',
                                 back_populates='runs')

    result = relationship('ReservoirSeismicityPrediction',
                          back_populates='modelrun',
                          uselist=False,
                          cascade='all, delete-orphan')

    __mapper_args__ = {
        'polymorphic_identity': EModel.SEISMICITY,
    }

    def __repr__(self):
        return '<%s(name=%s, url=%s)>' % (type(self).__name__, self.model.name,
                                          self.model.url)


class ReservoirSeismicityPrediction(RealQuantityMixin('rate'),
                                    RealQuantityMixin('bvalue'), ORMBase):
    """
    ORM represenation for a :py:class:`SeismicityModelRun` result.
    """
    # XXX(damb): Currently this entity is implemented self referencial i.e.
    # using an adjacency list relationship. However, in future *parent*
    # ReservoirSeismicityRatePrediction entities may ship additional
    # attributes. A reusable approach would be the usage of a mapping class
    # inheritance hierarchy e.g.:
    #
    #                   ReservoirSeismicityPrediction
    #                                   ^
    #                                   |
    #               IntegratedReservoirSeismicityPrediction
    #
    # XXX(damb): The attribute rate_uncertainty should be used to express the
    # concept of a rate_propability.
    id = Column(Integer, primary_key=True)
    geom = Column(Geometry(geometry_type='GEOMETRYZ',
                           dimension=3,
                           management=True,
                           use_st_prefix=False),
                  nullable=False)

    # relation: SeismicityModelRun
    modelrun_id = Column(Integer, ForeignKey('seismicitymodelrun.id'))
    modelrun = relationship('SeismicityModelRun',
                            back_populates='result')
    # reference: self (Adjacency List Relationships)
    parent_id = Column(Integer,
                       ForeignKey('reservoirseismicityprediction.id'))
    children = relationship(
        'ReservoirSeismicityPrediction',
        backref=backref('parent', remote_side=[id]),
        cascade="all, delete-orphan")

    def __iter__(self):
        # TODO(damb): Implement recursively
        for c in self.children:
            yield c
