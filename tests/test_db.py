# Copyright (C) 2019, ETH Zurich - Swiss Seismological Service SED
"""
General purpose DB test facilities.
"""

import os
import unittest
import tempfile

from sqlalchemy import create_engine
from sqlalchemy.event import listen
from sqlalchemy.sql import select, func

from ramsis.datamodel.status import Status # noqa
from ramsis.datamodel.seismicity import SeismicityModel # noqa
from ramsis.datamodel.forecast import Forecast # noqa
from ramsis.datamodel.seismics import SeismicCatalog # noqa
from ramsis.datamodel.well import InjectionWell # noqa
from ramsis.datamodel.settings import ProjectSettings # noqa
from ramsis.datamodel.project import Project # noqa
from ramsis.datamodel.base import ORMBase


def load_spatialite(dbapi_conn, connection_record):
    """
    Load spatialite extension.
    """
    # XXX(damb): sudo apt-get install libsqlite3-mod-spatialite
    dbapi_conn.enable_load_extension(True)
    dbapi_conn.load_extension('/usr/lib/x86_64-linux-gnu/mod_spatialite.so')

# load_spatialite ()


# XXX(damb): Enable GISDB test cases with:
# $ export RAMSIS_TEST_GISDB="True"; python setup.py test --addopts="-r s"
@unittest.skipUnless(
    os.getenv('RAMSIS_TEST_GISDB', 'False') == 'True',
    "'RAMSIS_TEST_GISDB' envvar not 'True'")
class GISDBTestCase(unittest.TestCase):

    def setUp(self):
        _, self.path_db = tempfile.mkstemp(dir=tempfile.gettempdir())
        # XXX(damb): see:
        # https://geoalchemy-2.readthedocs.io/en/latest/spatialite_tutorial.html
        self.engine = create_engine('sqlite:///{}'.format(self.path_db))
        listen(self.engine, 'connect', load_spatialite)

        conn = self.engine.connect()
        conn.execute(select([func.InitSpatialMetaData()]))
        conn.close()

    # setUp ()

    def tearDown(self):
        os.remove(self.path_db)

    def test_create_tables(self):
        self.assertIsNone(ORMBase.metadata.create_all(self.engine))

# class GISDBTestCase


# ----- END OF test_db.py -----
