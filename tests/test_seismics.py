# Copyright (C) 2019, ETH Zurich - Swiss Seismological Service SED
"""
Seismics related test facilities.
"""

import datetime
import unittest

from ramsis.datamodel.status import Status  # noqa
from ramsis.datamodel.seismicity import SeismicityModel  # noqa
from ramsis.datamodel.forecast import Forecast  # noqa
from ramsis.datamodel.seismics import SeismicCatalog, SeismicEvent  # noqa
from ramsis.datamodel.well import InjectionWell, WellSection  # noqa
from ramsis.datamodel.hydraulics import Hydraulics, InjectionPlan  # noqa
from ramsis.datamodel.settings import ProjectSettings  # noqa
from ramsis.datamodel.project import Project  # noqa


class SeismicCatalogTestCase(unittest.TestCase):
    """
    Test cases for :py:class:`ramsis.datamodel.seimics.SeismicCatalog`.
    """

    def test_merge_overlap_by_time(self):
        c1_first_event = datetime.datetime(2020, 1, 1)
        c1_interval = datetime.timedelta(seconds=3600)
        c1_num_events = 7

        c1 = SeismicCatalog(
            events=[SeismicEvent(
                datetime_value=c1_first_event + i * c1_interval)
                for i in range(c1_num_events)])

        c2_first_event = datetime.datetime(2020, 1, 1, 3)
        c2_interval = datetime.timedelta(seconds=1800)
        c2_num_events = 4

        c2 = SeismicCatalog(
            events=[SeismicEvent(
                datetime_value=c2_first_event + i * c2_interval)
                for i in range(c2_num_events)])

        c1.merge(c2)

        self.assertEqual(
            SeismicEvent(datetime_value=datetime.datetime(2020, 1, 1)),
            c1.events[0])
        self.assertEqual(
            SeismicEvent(datetime_value=datetime.datetime(2020, 1, 1, 1)),
            c1.events[1])
        self.assertEqual(
            SeismicEvent(datetime_value=datetime.datetime(2020, 1, 1, 2)),
            c1.events[2])
        self.assertEqual(
            SeismicEvent(datetime_value=datetime.datetime(2020, 1, 1, 5)),
            c1.events[3])
        self.assertEqual(
            SeismicEvent(datetime_value=datetime.datetime(2020, 1, 1, 6)),
            c1.events[4])
        self.assertEqual(
            SeismicEvent(datetime_value=datetime.datetime(2020, 1, 1, 3)),
            c1.events[5])
        self.assertEqual(
            SeismicEvent(datetime_value=datetime.datetime(2020, 1, 1, 3, 30)),
            c1.events[6])
        self.assertEqual(
            SeismicEvent(datetime_value=datetime.datetime(2020, 1, 1, 4)),
            c1.events[7])
        self.assertEqual(
            SeismicEvent(datetime_value=datetime.datetime(2020, 1, 1, 4, 30)),
            c1.events[8])

    def test_merge_empty(self):
        c1_first_event = datetime.datetime(2020, 1, 1)
        c1_interval = datetime.timedelta(seconds=3600)
        c1_num_events = 7

        c1 = SeismicCatalog(
            events=[SeismicEvent(
                datetime_value=c1_first_event + i * c1_interval)
                for i in range(c1_num_events)])

        c2 = SeismicCatalog()

        c1.merge(c2)

        self.assertEqual(
            SeismicEvent(datetime_value=datetime.datetime(2020, 1, 1)),
            c1.events[0])
        self.assertEqual(
            SeismicEvent(datetime_value=datetime.datetime(2020, 1, 1, 1)),
            c1.events[1])
        self.assertEqual(
            SeismicEvent(datetime_value=datetime.datetime(2020, 1, 1, 2)),
            c1.events[2])
        self.assertEqual(
            SeismicEvent(datetime_value=datetime.datetime(2020, 1, 1, 3)),
            c1.events[3])
        self.assertEqual(
            SeismicEvent(datetime_value=datetime.datetime(2020, 1, 1, 4)),
            c1.events[4])
        self.assertEqual(
            SeismicEvent(datetime_value=datetime.datetime(2020, 1, 1, 5)),
            c1.events[5])
        self.assertEqual(
            SeismicEvent(datetime_value=datetime.datetime(2020, 1, 1, 6)),
            c1.events[6])

    def test_merge_single(self):
        c1_first_event = datetime.datetime(2020, 1, 1)
        c1_interval = datetime.timedelta(seconds=3600)
        c1_num_events = 7

        c1 = SeismicCatalog(
            events=[SeismicEvent(
                datetime_value=c1_first_event + i * c1_interval)
                for i in range(c1_num_events)])

        c2 = SeismicCatalog(
            events=[SeismicEvent(
                datetime_value=datetime.datetime(2020, 1, 1, 3))])

        c1.merge(c2)

        self.assertEqual(
            SeismicEvent(datetime_value=datetime.datetime(2020, 1, 1)),
            c1.events[0])
        self.assertEqual(
            SeismicEvent(datetime_value=datetime.datetime(2020, 1, 1, 1)),
            c1.events[1])
        self.assertEqual(
            SeismicEvent(datetime_value=datetime.datetime(2020, 1, 1, 2)),
            c1.events[2])
        self.assertEqual(
            SeismicEvent(datetime_value=datetime.datetime(2020, 1, 1, 4)),
            c1.events[3])
        self.assertEqual(
            SeismicEvent(datetime_value=datetime.datetime(2020, 1, 1, 5)),
            c1.events[4])
        self.assertEqual(
            SeismicEvent(datetime_value=datetime.datetime(2020, 1, 1, 6)),
            c1.events[5])
        self.assertEqual(
            SeismicEvent(datetime_value=datetime.datetime(2020, 1, 1, 3)),
            c1.events[6])

    def test_merge_into_empty(self):

        c1 = SeismicCatalog()

        c2_first_event = datetime.datetime(2020, 1, 1)
        c2_interval = datetime.timedelta(seconds=3600)
        c2_num_events = 7

        c2 = SeismicCatalog(
            events=[SeismicEvent(
                datetime_value=c2_first_event + i * c2_interval,
                magnitude_value=i)
                for i in range(c2_num_events)])

        c1.merge(c2)

        self.assertEqual(len(c1), len(c2))
        for e_c1, e_c2 in zip(c1, c2):
            self.assertEqual(e_c1, e_c2)

    def test_merge_with_starttime(self):
        c1_first_event = datetime.datetime(2020, 1, 1)
        c1_interval = datetime.timedelta(seconds=3600)
        c1_num_events = 7

        c1 = SeismicCatalog(
            events=[SeismicEvent(
                datetime_value=c1_first_event + i * c1_interval)
                for i in range(c1_num_events)])

        c2_first_event = datetime.datetime(2020, 1, 1, 3)
        c2_interval = datetime.timedelta(seconds=1800)
        c2_num_events = 4

        c2 = SeismicCatalog(
            events=[SeismicEvent(
                datetime_value=c2_first_event + i * c2_interval)
                for i in range(c2_num_events)])

        c1.merge(c2, starttime=datetime.datetime(2020, 1, 1, 2))

        self.assertEqual(
            SeismicEvent(datetime_value=datetime.datetime(2020, 1, 1)),
            c1.events[0])
        self.assertEqual(
            SeismicEvent(datetime_value=datetime.datetime(2020, 1, 1, 1)),
            c1.events[1])
        self.assertEqual(
            SeismicEvent(datetime_value=datetime.datetime(2020, 1, 1, 5)),
            c1.events[2])
        self.assertEqual(
            SeismicEvent(datetime_value=datetime.datetime(2020, 1, 1, 6)),
            c1.events[3])
        self.assertEqual(
            SeismicEvent(datetime_value=datetime.datetime(2020, 1, 1, 3)),
            c1.events[4])
        self.assertEqual(
            SeismicEvent(datetime_value=datetime.datetime(2020, 1, 1, 3, 30)),
            c1.events[5])
        self.assertEqual(
            SeismicEvent(datetime_value=datetime.datetime(2020, 1, 1, 4)),
            c1.events[6])
        self.assertEqual(
            SeismicEvent(datetime_value=datetime.datetime(2020, 1, 1, 4, 30)),
            c1.events[7])

    def test_merge_with_endtime(self):
        c1_first_event = datetime.datetime(2020, 1, 1)
        c1_interval = datetime.timedelta(seconds=3600)
        c1_num_events = 7

        c1 = SeismicCatalog(
            events=[SeismicEvent(
                datetime_value=c1_first_event + i * c1_interval)
                for i in range(c1_num_events)])

        c2_first_event = datetime.datetime(2020, 1, 1, 3)
        c2_interval = datetime.timedelta(seconds=1800)
        c2_num_events = 4

        c2 = SeismicCatalog(
            events=[SeismicEvent(
                datetime_value=c2_first_event + i * c2_interval)
                for i in range(c2_num_events)])

        c1.merge(c2, endtime=datetime.datetime(2020, 1, 1, 4))

        self.assertEqual(
            SeismicEvent(datetime_value=datetime.datetime(2020, 1, 1)),
            c1.events[0])
        self.assertEqual(
            SeismicEvent(datetime_value=datetime.datetime(2020, 1, 1, 1)),
            c1.events[1])
        self.assertEqual(
            SeismicEvent(datetime_value=datetime.datetime(2020, 1, 1, 2)),
            c1.events[2])
        self.assertEqual(
            SeismicEvent(datetime_value=datetime.datetime(2020, 1, 1, 5)),
            c1.events[3])
        self.assertEqual(
            SeismicEvent(datetime_value=datetime.datetime(2020, 1, 1, 6)),
            c1.events[4])
        self.assertEqual(
            SeismicEvent(datetime_value=datetime.datetime(2020, 1, 1, 3)),
            c1.events[5])
        self.assertEqual(
            SeismicEvent(datetime_value=datetime.datetime(2020, 1, 1, 3, 30)),
            c1.events[6])
        self.assertEqual(
            SeismicEvent(datetime_value=datetime.datetime(2020, 1, 1, 4)),
            c1.events[7])

    def test_merge_with_timewindow_no_events(self):
        c1_first_event = datetime.datetime(2020, 1, 1)
        c1_interval = datetime.timedelta(seconds=3600)
        c1_num_events = 7

        c1 = SeismicCatalog(
            events=[SeismicEvent(
                datetime_value=c1_first_event + i * c1_interval)
                for i in range(c1_num_events)])

        c2_first_event = datetime.datetime(2020, 1, 1, 3)
        c2_interval = datetime.timedelta(seconds=1800)
        c2_num_events = 4

        c2 = SeismicCatalog(
            events=[SeismicEvent(
                datetime_value=c2_first_event + i * c2_interval)
                for i in range(c2_num_events)])

        # no events in c2 available from starttime until endtime - though, c1
        # is reduced
        c1.merge(c2, starttime=datetime.datetime(2020, 1, 1, 1),
                 endtime=datetime.datetime(2020, 1, 1, 2))

        self.assertEqual(
            SeismicEvent(datetime_value=datetime.datetime(2020, 1, 1)),
            c1.events[0])
        self.assertEqual(
            SeismicEvent(datetime_value=datetime.datetime(2020, 1, 1, 3)),
            c1.events[1])
        self.assertEqual(
            SeismicEvent(datetime_value=datetime.datetime(2020, 1, 1, 4)),
            c1.events[2])
        self.assertEqual(
            SeismicEvent(datetime_value=datetime.datetime(2020, 1, 1, 5)),
            c1.events[3])
        self.assertEqual(
            SeismicEvent(datetime_value=datetime.datetime(2020, 1, 1, 6)),
            c1.events[4])


def suite():
    return unittest.makeSuite(SeismicCatalogTestCase, 'test')


if __name__ == '__main__':
    unittest.main(defaultTest='suite')
