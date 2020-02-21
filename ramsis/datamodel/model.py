# Copyright 2019, ETH Zurich - Swiss Seismological Service SED
"""
Model related ORM facilities,
"""

import enum

from sqlalchemy import Column, Boolean, Enum
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.orm import relationship

from ramsis.datamodel.base import ORMBase, NameMixin
from ramsis.datamodel.status import Status
from ramsis.datamodel.type import JSONEncodedDict
from ramsis.datamodel.utils import clone


class EModel(enum.Enum):
    SEISMICITY = 0
    SEISMICITY_SKILL = 1
    HAZARD = 2
    RISK = 3


class Model(NameMixin, ORMBase):
    """
    Abstract ORM base class for models.

    .. note::

        Inheritance is implemented following the `SQLAlchemy Joined Table
        Inheritance
        <https://docs.sqlalchemy.org/en/latest/orm/inheritance.html#joined-table-inheritance>`_
        paradigm.
    """
    # XXX(damb): default model configuration parameters
    config = Column(MutableDict.as_mutable(JSONEncodedDict))
    enabled = Column(Boolean, default=True)
    _type = Column(Enum(EModel))

    __mapper_args__ = {
        'polymorphic_identity': 'model',
        'polymorphic_on': _type,
    }


class ModelRun(ORMBase):
    """
    Abstract base class for model runs.

    .. note::

        Inheritance is implemented following the `SQLAlchemy Joined Table
        Inheritance
        <https://docs.sqlalchemy.org/en/latest/orm/inheritance.html#joined-table-inheritance>`_
        paradigm.
    """
    # XXX(damb): seismicity model run specific configuration parameters
    config = Column(MutableDict.as_mutable(JSONEncodedDict))
    enabled = Column(Boolean, default=True)
    _type = Column(Enum(EModel))
    #seismicity_model_run = relationship('SeismicityModelRun', uselist=False, back_populates='modelrun')
    #hazard_model_run = relationship('HazardModelRun', uselist=False, back_populates='modelrun')

    status = relationship('Status',
                          back_populates='run',
                          uselist=False,
                          cascade='all, delete-orphan')

    __mapper_args__ = {
        'polymorphic_identity': 'model_run',
        'polymorphic_on': _type,
    }

    def clone(self, with_results=False):
        """
        Clone a model run.

        :param bool with_results: If :code:`True`, append results and related
            data while cloning, otherwise results are excluded.
        """
        new = clone(self, with_foreignkeys=False)
        new.status = self.status.clone() if with_results else Status()
        return new
