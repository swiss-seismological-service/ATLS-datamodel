# Copyright (C) 2019, ETH Zurich - Swiss Seismological Service SED
"""
General purpose DB test facilities.
"""

import os
import unittest

from sqlalchemy import create_engine
from sqlalchemy.event import listen
from sqlalchemy.sql import select, func

import ramsis.datamodel as dm


def load_spatialite(dbapi_conn, connection_record):
    """
    Load spatialite extension.
    """
    # XXX(damb): sudo apt-get install libsqlite3-mod-spatialite
    dbapi_conn.enable_load_extension(True)
    dbapi_conn.load_extension('/usr/lib/x86_64-linux-gnu/mod_spatialite.so')


# XXX(damb): Enable SPATIALITE test cases with:
# $ export RAMSIS_TEST_SPATIALITE="True"; python setup.py test --addopts="-r s"
@unittest.skipUnless(
    os.getenv('RAMSIS_TEST_SPATIALITE', 'False') == 'True',
    "'RAMSIS_TEST_SPATIALITE' envvar not 'True'")
class GISDBTestCase(unittest.TestCase):

    def setUp(self):
        # XXX(damb): see:
        # https://geoalchemy-2.readthedocs.io/en/latest/spatialite_tutorial.html
        self.engine = create_engine('sqlite://')
        listen(self.engine, 'connect', load_spatialite)

        conn = self.engine.connect()
        conn.execute(select([func.InitSpatialMetaData()]))
        conn.close()

    def test_create_tables(self):
        self.assertIsNone(dm.ORMBase.metadata.create_all(self.engine))


def suite():
    return unittest.makeSuite(GISDBTestCase, 'test')


if __name__ == '__main__':
    unittest.main(defaultTest='suite')
