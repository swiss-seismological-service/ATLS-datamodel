# This is <model.py>
# ----------------------------------------------------------------------------
#
# Copyright (c) 2018 by Daniel Armbruster (SED, ETHZ)
#
# REVISIONS and CHANGES
#    2018/01/24   V1.0   Daniel Armbruster (damb)
#
# ============================================================================

import enum

from sqlalchemy import Column, Boolean, Enum
from sqlalchemy.ext.mutable import MutableDict

from ramsis.datamodel.base import ORMBase, NameMixin
from ramsis.datamodel.type import JSONEncodedDict


class EModel(enum.Enum):
    SEISMICITY = 0
    SEISMICITY_SKILL = 1
    HAZARD = 2
    RISK = 3

# class EModel


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

# class Model


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

    __mapper_args__ = {
        'polymorphic_identity': 'model_run',
        'polymorphic_on': _type,
    }

# class ModelRun


# ----- END OF model.py -----
