# This is <seismicity.py>
# ----------------------------------------------------------------------------
#
# Copyright (c) 2018 by Daniel Armbruster (SED, ETHZ)
#
# REVISIONS and CHANGES
#    2018/01/24   V1.0   Daniel Armbruster (damb)
#
# ============================================================================
"""
Seismicity prediction related ORM facilities.
"""

from geoalchemy import Geometry

from sqlalchemy import Column, String, Integer, ForeignKey
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.orm import relationship, backref

from ramsis.datamodel.base import ORMBase, QuantityMixin
from ramsis.datamodel.model import Model, ModelRun, EModel
from ramsis.datamodel.type import JSONEncodedDict


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

# class SeismicityModel


class SeismicityModelRun(ModelRun):
    """
    ORM representation of a seismicity forecast model run.
    """
    __tablename__ = 'seismicitymodelrun'
    id = Column(Integer, ForeignKey('modelrun.id'), primary_key=True)

    # XXX(damb): seismicity model run specific configuration parameters
    config = Column(MutableDict.as_mutable(JSONEncodedDict))

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

    # TODO(damb): calculationstate to be added
    # TODO TODO TODO

    __mapper_args__ = {
        'polymorphic_identity': EModel.SEISMICITY,
    }

    # TODO(damb): calculationstate to be added
    def __repr__(self):
        return '<%s(name=%s, url=%s)>' % (type(self).__name__, self.model.name,
                                          self.model.url)
# SeismicityModelRun


class ReservoirSeismicityPrediction(QuantityMixin('rate'),
                                    QuantityMixin('b_value'), ORMBase):
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
    # XXX(damb): The attribute rate_uncertainty is used to express the concept
    # of a rate_propability.
    geom = Column(Geometry(geometry_type='GEOMETRYZ', dimension=3),
                  nullable=False)

    # relation: SeismicityModelRun
    modelrun_id = Column(Integer, ForeignKey('seismicitymodelrun.id'))
    modelrun = relationship('SeismicityModelRun',
                            back_populates='result',
                            cascade='all, delete-orphan')
    # reference: self (Adjacency List Relationships)
    parent_id = Column(Integer,
                       ForeignKey('reservoirseismicityprediction.id'))
    children = relationship(
        'ReservoirSeismicityPrediction',
        backref=backref('parent', remote_side=[id]),
        cascade="all, delete-orphan")

    def __iter__(self):
        for c in self.children:
            yield c

    # __iter__ ()

# class ReservoirSeismicityPrediction


# ----- END OF seismicity.py -----
