# Copyright (C) 2019, ETH Zurich - Swiss Seismological Service SED
"""
Hydraulics related test facilities.
"""

import datetime
import unittest

from ramsis.datamodel.status import Status  # noqa
from ramsis.datamodel.seismicity import SeismicityModel  # noqa
from ramsis.datamodel.forecast import Forecast  # noqa
from ramsis.datamodel.seismics import SeismicCatalog, SeismicEvent  # noqa
from ramsis.datamodel.well import InjectionWell, WellSection  # noqa
from ramsis.datamodel.hydraulics import (  # noqa
    Hydraulics, InjectionPlan, HydraulicSample)  # noqa
from ramsis.datamodel.settings import ProjectSettings  # noqa
from ramsis.datamodel.project import Project  # noqa


class HydraulicsTestCase(unittest.TestCase):
    """
    Test cases for :py:class:`ramsis.datamodel.hydraulics.Hydraulics`.
    """

    def test_merge_overlap_by_time(self):
        h1_first_sample = datetime.datetime(2020, 1, 1)
        h1_interval = datetime.timedelta(seconds=3600)
        h1_num_samples = 7

        h1 = Hydraulics(
            samples=[HydraulicSample(
                datetime_value=h1_first_sample + i * h1_interval)
                for i in range(h1_num_samples)])

        h2_first_sample = datetime.datetime(2020, 1, 1, 3)
        h2_interval = datetime.timedelta(seconds=1800)
        h2_num_samples = 4

        h2 = Hydraulics(
            samples=[HydraulicSample(
                datetime_value=h2_first_sample + i * h2_interval)
                for i in range(h2_num_samples)])

        h1.merge(h2)
        self.assertEqual(
            HydraulicSample(datetime_value=datetime.datetime(2020, 1, 1)),
            h1.samples[0])
        self.assertEqual(
            HydraulicSample(datetime_value=datetime.datetime(2020, 1, 1, 1)),
            h1.samples[1])
        self.assertEqual(
            HydraulicSample(datetime_value=datetime.datetime(2020, 1, 1, 2)),
            h1.samples[2])
        self.assertEqual(
            HydraulicSample(datetime_value=datetime.datetime(2020, 1, 1, 5)),
            h1.samples[3])
        self.assertEqual(
            HydraulicSample(datetime_value=datetime.datetime(2020, 1, 1, 6)),
            h1.samples[4])
        self.assertEqual(
            HydraulicSample(datetime_value=datetime.datetime(2020, 1, 1, 3)),
            h1.samples[5])
        self.assertEqual(
            HydraulicSample(
                datetime_value=datetime.datetime(2020, 1, 1, 3, 30)),
            h1.samples[6])
        self.assertEqual(
            HydraulicSample(datetime_value=datetime.datetime(2020, 1, 1, 4)),
            h1.samples[7])
        self.assertEqual(
            HydraulicSample(
                datetime_value=datetime.datetime(2020, 1, 1, 4, 30)),
            h1.samples[8])

    def test_merge_empty(self):
        h1_first_sample = datetime.datetime(2020, 1, 1)
        h1_interval = datetime.timedelta(seconds=3600)
        h1_num_samples = 7

        h1 = Hydraulics(
            samples=[HydraulicSample(
                datetime_value=h1_first_sample + i * h1_interval)
                for i in range(h1_num_samples)])

        h2 = Hydraulics()

        h1.merge(h2)
        self.assertEqual(
            HydraulicSample(datetime_value=datetime.datetime(2020, 1, 1)),
            h1.samples[0])
        self.assertEqual(
            HydraulicSample(datetime_value=datetime.datetime(2020, 1, 1, 1)),
            h1.samples[1])
        self.assertEqual(
            HydraulicSample(datetime_value=datetime.datetime(2020, 1, 1, 2)),
            h1.samples[2])
        self.assertEqual(
            HydraulicSample(datetime_value=datetime.datetime(2020, 1, 1, 3)),
            h1.samples[3])
        self.assertEqual(
            HydraulicSample(datetime_value=datetime.datetime(2020, 1, 1, 4)),
            h1.samples[4])
        self.assertEqual(
            HydraulicSample(datetime_value=datetime.datetime(2020, 1, 1, 5)),
            h1.samples[5])
        self.assertEqual(
            HydraulicSample(datetime_value=datetime.datetime(2020, 1, 1, 6)),
            h1.samples[6])

    def test_merge_single(self):
        h1_first_sample = datetime.datetime(2020, 1, 1)
        h1_interval = datetime.timedelta(seconds=3600)
        h1_num_samples = 7

        h1 = Hydraulics(
            samples=[HydraulicSample(
                datetime_value=h1_first_sample + i * h1_interval)
                for i in range(h1_num_samples)])

        h2 = Hydraulics(
            samples=[HydraulicSample(
                datetime_value=datetime.datetime(2020, 1, 1, 3))])

        h1.merge(h2)
        self.assertEqual(
            HydraulicSample(datetime_value=datetime.datetime(2020, 1, 1)),
            h1.samples[0])
        self.assertEqual(
            HydraulicSample(datetime_value=datetime.datetime(2020, 1, 1, 1)),
            h1.samples[1])
        self.assertEqual(
            HydraulicSample(datetime_value=datetime.datetime(2020, 1, 1, 2)),
            h1.samples[2])
        self.assertEqual(
            HydraulicSample(datetime_value=datetime.datetime(2020, 1, 1, 4)),
            h1.samples[3])
        self.assertEqual(
            HydraulicSample(datetime_value=datetime.datetime(2020, 1, 1, 5)),
            h1.samples[4])
        self.assertEqual(
            HydraulicSample(datetime_value=datetime.datetime(2020, 1, 1, 6)),
            h1.samples[5])
        self.assertEqual(
            HydraulicSample(datetime_value=datetime.datetime(2020, 1, 1, 3)),
            h1.samples[6])


def suite():
    return unittest.makeSuite(HydraulicsTestCase, 'test')


if __name__ == '__main__':
    unittest.main(defaultTest='suite')
