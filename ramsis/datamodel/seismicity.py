# Copyright 2019, ETH Zurich - Swiss Seismological Service SED
"""
Seismicity prediction related ORM facilities.
"""
import functools

from sqlalchemy import Column, String, Integer, Float, ForeignKey
from sqlalchemy.orm import relationship, backref, class_mapper
from sqlalchemy.orm.exc import DetachedInstanceError

from ramsis.datamodel.base import (ORMBase, RealQuantityMixin,
                                   UniqueFiniteEpochMixin)
from ramsis.datamodel.model import Model, ModelRun, EModel
from ramsis.datamodel.type import GUID


# XXX(damb): Maintaining both a SeismicityModel, a SeismicityModelRun and on
# top a ForecastStage seems somehow cumbersome. In particular, when every
# single class ships its own config.
# Proposed strategy:
# * SeismicityModel.config provides the default configuration of a concrete
#   implementation of a seismicity model
# * SeismicityModelRun.config is the concrete configuration of the model when
#   executed
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
    sfmwid = Column(String)

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
    runid = Column(GUID, unique=True, index=True)

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

    def clone(self, with_results=False):
        """
        Clone a seismicity model run.

        :param bool with_results: If :code:`True`, append results and related
            data while cloning, otherwise results are excluded.
        """
        new = super().clone(with_results=with_results)
        # models are top-level objects; copy by reference
        new.model = self.model

        if not with_results:
            new.runid = None
            return new

        # TODO(damb): Copy results
        raise NotImplementedError
        return new

    def __repr__(self):
        return '<%s(name=%s, url=%s)>' % (type(self).__name__, self.model.name,
                                          self.model.url)

    def snapshot(self):
        """
        Create a snapshot of the catalog.

        :param filter_cond: Callable applied on catalog events when creating
            the snapshot
        :type filter_cond: callable or None

        :returns: Snapshot of the catalog
        :rtype: :py:class:`SeismicCatalog`
        """
        def try_detached(attr_name, snap):
            try:
                setattr(snap, attr_name, getattr(self, attr_name))
            except DetachedInstanceError:
                pass
            return snap

        snap = type(self)()
        for attr_name in ["model",
                          "model_id",
                          "forecaststage_id",
                          "forecaststage",
                          "runid",
                          "config",
                          "enabled",
                          "_type"]:
            snap = try_detached(attr_name, snap)
        return snap


@functools.total_ordering
class ReservoirSeismicityPrediction(ORMBase):
    """
    ORM representation for a :py:class:`SeismicityModelRun` result.
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

    x_min = Column(Float)
    x_max = Column(Float)
    y_min = Column(Float)
    y_max = Column(Float)
    z_min = Column(Float)
    z_max = Column(Float)

    # relation: SeismicityPredictionSample
    samples = relationship('SeismicityPredictionBin',
                           back_populates='result')
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

    def __lt__(self, other):
        # (sarsonl) have removed comparison of geometry,
        # what is this function used for? Update as required.
        if isinstance(other, ReservoirSeismicityPrediction):
            return ((self.samples) <
                    (self.samples))

        raise ValueError

    def __eq__(self, other):
        if isinstance(other, ReservoirSeismicityPrediction):
            mapper = class_mapper(type(self))

            pk_keys = set([c.key for c in mapper.primary_key])
            rel_keys = set([c.key for c in mapper.relationships])
            fk_keys = set([c.key for c in mapper.columns if c.foreign_keys])

            omit = pk_keys | rel_keys | fk_keys

            return all(getattr(self, attr) == getattr(other, attr)
                       for attr in [p.key for p in mapper.iterate_properties
                                    if p.key not in omit])

    def __hash__(self):
        return id(self)


@functools.total_ordering
class SeismicityPredictionBin(UniqueFiniteEpochMixin,
                              RealQuantityMixin('numberevents'),
                              RealQuantityMixin('b'),
                              RealQuantityMixin('a'),
                              RealQuantityMixin('mc'),
                              RealQuantityMixin('hydraulicvol'),
                              ORMBase):
    """
    ORM representation of a seismicity prediction sample.
    """
    result_id = Column(Integer, ForeignKey('reservoirseismicityprediction.id'))
    result = relationship('ReservoirSeismicityPrediction',
                          back_populates='samples')

    def __lt__(self, other):
        if isinstance(other, SeismicityPredictionBin):
            return ((self.numberevents_value, self.b_value, self.a_value,
                     self.mc_value, self.hydraulicvol_value) <
                    (other.numberevents_value, other.b_value, other.a_value,
                     other.mc_value, other.hydraulicvol_value))

        raise ValueError

    def __eq__(self, other):
        if isinstance(other, SeismicityPredictionBin):
            mapper = class_mapper(type(self))

            pk_keys = set([c.key for c in mapper.primary_key])
            rel_keys = set([c.key for c in mapper.relationships])
            fk_keys = set([c.key for c in mapper.columns if c.foreign_keys])

            omit = pk_keys | rel_keys | fk_keys

            return all(getattr(self, attr) == getattr(other, attr)
                       for attr in [p.key for p in mapper.iterate_properties
                                    if p.key not in omit])

        raise ValueError

    def __hash__(self):
        return id(self)
