# Copyright 2019, ETH Zurich - Swiss Seismological Service SED
"""
Hazard related ORM facilities.
"""
from sqlalchemy import Column, String, Integer, ForeignKey, DateTime, enum, \
    Float
import functools
from sqlalchemy.orm import relationship, backref

from ramsis.datamodel.base import ORMBase
from ramsis.datamodel.model import Model, ModelRun, EModel
from ramsis.datamodel.seismicity import hazard_seismicity_association


class HazardModel(Model):
    """
    ORM representation of a Hazard model configuration.
    :py:class:`HazardModel` instances are inteded to provide templates for
    :py:class:HazardModelRun` implementations.
    """
    __tablename__ = 'hazardmodel'
    id = Column(Integer, ForeignKey('model.id'), primary_key=True)

    url = Column(String)
    logictreetemplate = Column(String)
    jobconfigfile = Column(String)
    gmpefile = Column(String)
    runs = relationship('HazardModelRun',
                        cascade='all, delete-orphan')

    __mapper_args__ = {
        'polymorphic_identity': EModel.HAZARD,
    }

    def __repr__(self):
        return '<%s(name=%s, url=%s)>' % (type(self).__name__, self.name,
                                          self.url)


class HazardModelRun(ModelRun):
    """
    ORM representation of a hazard forecast model run.
    """
    __tablename__ = 'hazardmodelrun'
    id = Column(Integer, ForeignKey('modelrun.id'), primary_key=True)

    describedinterval_start = Column(DateTime)
    describedinterval_end = Column(DateTime)
    logictreefile = Column(String)
    # relation: HazardModel
    model_id = Column(Integer, ForeignKey('hazardmodel.id'))
    model = relationship('HazardModel',
                         back_populates='runs', lazy="joined")

    seismicitymodelruns = relationship(
        'SeismicityModelRun', secondary=hazard_seismicity_association,
        back_populates='hazardruns', lazy="joined")
    # relation: HazardForecastStage
    forecaststage_id = Column(Integer,
                              ForeignKey('hazardstage.id'))
    forecaststage = relationship('HazardStage',
                                 back_populates='runs',
                                 lazy="joined")
    oqinputdir = Column(String)

    result = relationship('HazardResult',
                          back_populates='modelrun',
                          cascade='all, delete-orphan')

    __mapper_args__ = {
        'polymorphic_identity': EModel.HAZARD,
        'inherit_condition': id == ModelRun.id,
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


class OQSeismicityModelFile(ModelRun):
    """
    ORM representation of the file associated with each seismicity model
    that is used in a hazard run.
    """
    __tablename__ = 'oqseismicitymodelfile'
    id = Column(Integer, ForeignKey('modelrun.id'), primary_key=True)
    seismicitymodel_id = Column(Integer,
                                ForeignKey('seismicitymodel.id'))
    seismicitymodelfilename = Column(String)


class IntensityMeasurementType(enum.Enum):
    """
    ORM representation for a :py:class:`HazardModelRun` result type.
    """
    PGA = 0


@functools.total_ordering
class HazardResult(ORMBase):
    """
    ORM representation for a :py:class:`HazardModelRun` result.
    """
    id = Column(Integer, primary_key=True)
    hazardtype = Column(enum.Enum(IntensityMeasurementType))
    samples = relationship('SeismicityPredictionBin',
                           back_populates='result')
    modelrun_id = Column(Integer, ForeignKey('hazardmodelrun.id'))
    modelrun = relationship('HazardModelRun',
                            back_populates='results')
    children = relationship(
        'HazardPointValue',
        backref=backref('parent', remote_side=[id]),
        cascade="all, delete-orphan", lazy="joined")


@functools.total_ordering
class HazardPointValue(ORMBase):
    """
    ORM representation of a seismicity prediction sample.
    """
    id = Column(Integer, primary_key=True)
    result_id = Column(Integer, ForeignKey('reservoirseismicityprediction.id'))
    result = relationship('ReservoirSeismicityPrediction',
                          back_populates='samples')
    groundmotion = Column(Float)
    poe = Column(Float)
    geopoint_id = Column(Integer, ForeignKey('geopoint.id'))
    geopoint = relationship('GeoPoint',
                            back_populates='hazardpointvalues',
                            use_list=False,
                            lazy='joined')

class GeoPoint(ORMBase):
    id = Column(Integer, primary_key=True)
    x = Column(Float)
    y = Column(Float)
    z = Column(Float)
    hazardpointvalues = relationship('HazardPointValue',
                                     back_populates='geopoint',
                                     use_list=True)
