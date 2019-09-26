# Copyright (C) 2019, ETH Zurich - Swiss Seismological Service SED
"""
Event related test facilities.
"""

import datetime
import unittest

from sqlalchemy import event, create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import select, func

from ramsis.datamodel.base import ORMBase  # noqa
from ramsis.datamodel.event import (
    create_scalar_attribute_events, create_collection_attribute_events,
    create_instance_events, SeismicCatalogAttributeEvents)
from ramsis.datamodel.forecast import (  # noqa
    Forecast, ForecastScenario, ForecastStage, SeismicityForecastStage,
    SeismicitySkillStage, HazardStage, RiskStage)
from ramsis.datamodel.hydraulics import (  # noqa
    Hydraulics, InjectionPlan, HydraulicSample)
from ramsis.datamodel.model import Model, ModelRun  # noqa
from ramsis.datamodel.project import Project  # noqa
from ramsis.datamodel.seismicity import (  # noqa
    SeismicityModel, SeismicityModelRun, ReservoirSeismicityPrediction,
    SeismicityPredictionBin)
from ramsis.datamodel.seismics import SeismicCatalog, SeismicEvent  # noqa
from ramsis.datamodel.settings import ProjectSettings  # noqa
from ramsis.datamodel.status import Status  # noqa
from ramsis.datamodel.well import InjectionWell, WellSection  # noqa


def load_spatialite(dbapi_conn, connection_record):
    """
    Load spatialite extention.
    """
    # XXX(damb): sudo apt-get install libsqlite3-mod-spatialite
    dbapi_conn.enable_load_extension(True)
    dbapi_conn.load_extension('/usr/lib/x86_64-linux-gnu/mod_spatialite.so')


class AttributeEventsTestCase(unittest.TestCase):
    """
    Test cases for :py:class:`ramsis.datamodel.events.AttributeEvents`
    """
    def setUp(self):
        self.emitted = False

    def tearDown(self):
        self.emitted = None

    def test_set_identifier_single_scalar_attr(self):

        def listener(**kwargs):
            self.emitted = True

        create_scalar_attribute_events(
            SeismicCatalog.creationinfo_creationtime,
            listener=listener, identifiers=['set'])

        cat = SeismicCatalog()
        cat.creationinfo_creationtime = datetime.datetime.utcnow()

        self.assertTrue(self.emitted)

        self.emitted = False
        cat.events = [SeismicEvent(
            datetime_value=datetime.datetime.utcnow(),
            x_value=0, y_value=0, z_value=5000, magnitude_value=4.0,
            quakeml=b'')]

        self.assertFalse(self.emitted)
        event.remove(SeismicCatalog.creationinfo_creationtime,
                     'set', listener)

    def test_set_modified_identifier_single_scalar_attr(self):

        def listener(**kwargs):
            self.emitted = True

        create_scalar_attribute_events(
            SeismicCatalog.creationinfo_creationtime,
            listener=listener, identifiers=['set', 'modified'])

        cat = SeismicCatalog()
        cat.creationinfo_creationtime = datetime.datetime.utcnow()

        self.assertTrue(self.emitted)

        self.emitted = False
        cat.creationinfo_creationtime = datetime.datetime.utcnow()

        self.assertTrue(self.emitted)

        self.emitted = False
        cat.events = [SeismicEvent(
            datetime_value=datetime.datetime.utcnow(),
            x_value=0, y_value=0, z_value=5000, magnitude_value=4.0,
            quakeml=b'')]

        self.assertFalse(self.emitted)
        event.remove(SeismicCatalog.creationinfo_creationtime,
                     'set', listener)
        event.remove(SeismicCatalog.creationinfo_creationtime,
                     'modified', listener)

    def test_init_collection_single_collection_attr(self):

        def listener(**kwargs):
            self.emitted = True

        create_collection_attribute_events(
            SeismicCatalog.events, listener=listener,
            identifiers=['init_collection'])

        cat = SeismicCatalog()
        cat.creationinfo_creationtime = datetime.datetime.utcnow()

        self.assertFalse(self.emitted)

        cat.events = [SeismicEvent(
            datetime_value=datetime.datetime.utcnow(),
            x_value=0, y_value=0, z_value=5000, magnitude_value=4.0,
            quakeml=b'')]

        self.assertTrue(self.emitted)
        event.remove(SeismicCatalog.events,
                     'init_collection', listener)

    def test_seismic_catalog_attr_events(self):

        def listener(**kwargs):
            self.emitted = True

        events = SeismicCatalogAttributeEvents(listener=listener)
        events.listen()

        cat = SeismicCatalog()

        # scalar set event
        cat.creationinfo_creationtime = datetime.datetime.utcnow()
        self.assertTrue(self.emitted)
        self.emitted = False

        # scalar modified event
        cat.creationinfo_creationtime = datetime.datetime.utcnow()
        self.assertTrue(self.emitted)
        self.emitted = False

        # collection init_collection event
        _ = cat.events
        self.assertTrue(self.emitted)
        self.emitted = False

        # collection init_collection event
        e = SeismicEvent(
            datetime_value=datetime.datetime.utcnow(),
            x_value=0, y_value=0, z_value=5000, magnitude_value=4.0,
            quakeml=b'')
        cat.events = [e, ]
        self.assertTrue(self.emitted)
        self.emitted = False

        # collection append event
        e = SeismicEvent(
            datetime_value=datetime.datetime.utcnow(),
            x_value=0, y_value=0, z_value=6000, magnitude_value=5.0,
            quakeml=b'')
        cat.events.append(e)
        self.assertTrue(self.emitted)
        self.emitted = False

        # collection remove event
        cat.events.remove(e)
        self.assertTrue(self.emitted)
        self.emitted = False

        # collection dispose_collection event
        cat.events = []
        self.assertTrue(self.emitted)
        self.emitted = False

    def test_seismic_catalog_remove_events(self):

        def listener(**kwargs):
            self.emitted = True

        events = SeismicCatalogAttributeEvents(
            listener=listener, scalar_identifiers=['set'],
            collection_identifiers=['init_collection'])
        events.listen()

        cat = SeismicCatalog()

        # test with exemplary attributes
        # ----
        # scalar set event
        cat.creationinfo_creationtime = datetime.datetime.utcnow()
        self.assertTrue(self.emitted)
        self.emitted = False

        # collection init_collection event
        e = SeismicEvent(
            datetime_value=datetime.datetime.utcnow(),
            x_value=0, y_value=0, z_value=5000, magnitude_value=4.0,
            quakeml=b'')
        cat.events = [e, ]
        self.assertTrue(self.emitted)
        self.emitted = False

        events.remove()

        # scalar set event
        cat.creationinfo_creationtime = datetime.datetime.utcnow()
        self.assertFalse(self.emitted)

        # collection init_collection event
        e = SeismicEvent(
            datetime_value=datetime.datetime.utcnow(),
            x_value=0, y_value=0, z_value=5000, magnitude_value=4.0,
            quakeml=b'')
        cat.events = [e, ]
        self.assertFalse(self.emitted)


class InstanceEventsTestCase(unittest.TestCase):

    def setUp(self):
        self.engine = create_engine('sqlite://')
        event.listen(self.engine, 'connect', load_spatialite)

        conn = self.engine.connect()
        conn.execute(select([func.InitSpatialMetaData()]))
        conn.close()

        # init DB
        ORMBase.metadata.create_all(self.engine)

        self.make_session = sessionmaker(bind=self.engine)

        self.emitted = False

    def tearDown(self):
        self.emitted = None

    def test_seismic_catalog_instance_load(self):

        def listener(**kwargs):
            self.emitted = True

        create_instance_events(
            SeismicCatalog, listener, ['load'], propagate=False)

        # create seismic catalog
        session = self.make_session()
        cat = SeismicCatalog(creationinfo_author='ed')
        session.add(cat)
        session.commit()
        session.close()

        # query it from the DB
        session = self.make_session()
        cat = session.query(SeismicCatalog).\
            filter_by(creationinfo_author='ed').first()
        session.close()

        self.assertTrue(self.emitted)
        session.close()
