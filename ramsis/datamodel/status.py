# Copyright 2019, ETH Zurich - Swiss Seismological Service SED
"""
Processing status related ORM facilities.
"""

import datetime
import enum
import json

from sqlalchemy import Column, Integer, Enum, PickleType, ForeignKey
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import relationship

from ramsis.datamodel.base import ORMBase, UniqueEpochMixin
from ramsis.datamodel.type import GUID


class EStatus(enum.Enum):
    PENDING = 0
    RUNNING = 1
    ERROR = 2
    COMPLETE = 3


class Status(UniqueEpochMixin, ORMBase):
    """
    General purpose calculation status ORM representation for bookkeeping
    purposes.

    The info `dict` contains zero or more of the following fields by
    convention:

    info = {
        'last_response': Last http response for remote workers
    }
    """
    # TODO(damb): Check if UUID is better located at ModelRun
    uuid = Column(GUID, unique=True, index=True, nullable=False)
    state = Column(Enum(EStatus), default=EStatus.PENDING)
    info = Column(PickleType(pickler=json))

    # relation: ModelRun
    run_id = Column(Integer, ForeignKey('modelrun.id'))
    run = relationship('ModelRun', back_populates='status')

    def __init__(self, uuid, state=EStatus.PENDING, info=None):
        self.uuid = uuid
        self.state = state
        self.info = info
        self.starttime = datetime.datetime.utcnow()

    @hybrid_property
    def finished(self):
        return self.state in (EStatus.ERROR, EStatus.COMPLETE)
