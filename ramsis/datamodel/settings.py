# Copyright 2019, ETH Zurich - Swiss Seismological Service SED
"""
Settings access and storage

These classes represent project related settings, i.e. settings
that will be stored in the project database.
"""

import abc
import collections
import datetime
import json

from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.ext.declarative.api import DeclarativeMeta
from sqlalchemy.orm import reconstructor, relationship

from ramsis.datamodel.base import ORMBase, NameMixin


# TODO(damb): Better make use of a ISO8601 conform date format. With
# https://docs.obspy.org/packages/autogen/obspy.core.utcdatetime.UTCDateTime.html
# e.g. obspy implements already the according infrastructure.
DATE_FORMAT = '%Y-%m-%d %H:%M:%S'


def datetime_encoder(x):
    if isinstance(x, datetime.datetime):
        return x.strftime(DATE_FORMAT)
    raise TypeError('Don''t know how to encode {}'.format(x))


def datetime_decoder(dct):
    for k, v in dct.items():
        if isinstance(v, str):
            try:
                dct[k] = datetime.datetime.strptime(v, DATE_FORMAT)
            except ValueError:
                pass
    return dct


class SettingsMeta(DeclarativeMeta, abc.ABCMeta):
    pass


class Settings(collections.UserDict, NameMixin, ORMBase,
               metaclass=SettingsMeta):
    """
    Collection of settings

    Each Settings object manages a arbitrary number of settings and their
    default values. Internally everything is stored in a nested dict and
    persisted as a json string. This makes it easy to add new and remove
    obsolete settings.

    .. note::

        Settings make use of SQLAlchemy's `Single Table Inheritance
        <https://docs.sqlalchemy.org/en/latest/orm/inheritance.html#single-table-inheritance>`_.

    """
    datetime = Column(DateTime, default=datetime.datetime.utcnow(),
                      onupdate=datetime.datetime.utcnow())
    # TODO(damb): Check if sqlalchemy.type.JSON would be an option.
    config = Column(String)
    _type = Column(String, nullable=False)

    __mapper_args__ = {
        'polymorphic_on': _type,
        'polymorphic_identity': 'settings'
    }

    @reconstructor
    def init_on_load(self):
        self.data = (json.loads(self.config,
                                object_hook=datetime_decoder)
                     if self.config else {})

    def commit(self):
        """
        Commit the settings

        This updates the internal json string and the date property if we keep
        a history of this Settings object. You still need to commit the object
        to the database afterwards.
        Emits the settings_changed signal

        """
        self.config = json.dumps(self.data, indent=4, default=datetime_encoder)


class ProjectSettings(Settings):
    __tablename__ = 'settings'

    # relation: Project
    project_id = Column(ForeignKey('project.id'))
    project = relationship('Project', back_populates='settings')

    __mapper_args__ = {'polymorphic_identity': 'project'}
    __table_args__ = {'extend_existing': True}

    DEFAULTS = {
        'fdsnws_enable': False,
        'fdsnws_url': None,
        'fdsnws_interval': 5.0,  # minutes
        'hydws_enable': False,
        'hydws_url': None,
        'hydws_interval': 5.0,  # minutes
        'rate_interval': 1.0,  # minutes
        'auto_schedule_enable': True,
        'forecast_interval': 6.0,  # hours
        'forecast_length': 6.0,  # hours
        'forecast_start': datetime.datetime(1970, 1, 1, 0, 0, 0),
        'seismic_rate_interval': 1.0,  # minutes
        'write_fc_results_to_disk': False,
    }

    def __init__(self):
        super().__init__()

        for key, default_value in self.DEFAULTS.items():
            self.setdefault(key, default=default_value)
        self.commit()
