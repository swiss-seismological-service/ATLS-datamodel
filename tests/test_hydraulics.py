# Copyright (C) 2019, ETH Zurich - Swiss Seismological Service SED
"""
Hydraulics related test facilities.
"""

import datetime
import unittest

import ramsis.datamodel as dm


class HydraulicsTestCase(unittest.TestCase):
    """
    Test cases for :py:class:`ramsis.datamodel.hydraulics.Hydraulics`.
    """

    def test_merge_overlap_by_time(self):
        h1_first_sample = datetime.datetime(2020, 1, 1)
        h1_interval = datetime.timedelta(seconds=3600)
        h1_num_samples = 7

        h1 = dm.Hydraulics(
            samples=[dm.HydraulicSample(
                datetime_value=h1_first_sample + i * h1_interval)
                for i in range(h1_num_samples)])

        h2_first_sample = datetime.datetime(2020, 1, 1, 3)
        h2_interval = datetime.timedelta(seconds=1800)
        h2_num_samples = 4

        h2 = dm.Hydraulics(
            samples=[dm.HydraulicSample(
                datetime_value=h2_first_sample + i * h2_interval)
                for i in range(h2_num_samples)])

        h1.merge(h2)
        self.assertEqual(
            dm.HydraulicSample(datetime_value=datetime.datetime(2020, 1, 1)),
            h1.samples[0])
        self.assertEqual(
            dm.HydraulicSample(
                datetime_value=datetime.datetime(2020, 1, 1, 1)),
            h1.samples[1])
        self.assertEqual(
            dm.HydraulicSample(
                datetime_value=datetime.datetime(2020, 1, 1, 2)),
            h1.samples[2])
        self.assertEqual(
            dm.HydraulicSample(
                datetime_value=datetime.datetime(2020, 1, 1, 5)),
            h1.samples[3])
        self.assertEqual(
            dm.HydraulicSample(
                datetime_value=datetime.datetime(2020, 1, 1, 6)),
            h1.samples[4])
        self.assertEqual(
            dm.HydraulicSample(
                datetime_value=datetime.datetime(2020, 1, 1, 3)),
            h1.samples[5])
        self.assertEqual(
            dm.HydraulicSample(
                datetime_value=datetime.datetime(2020, 1, 1, 3, 30)),
            h1.samples[6])
        self.assertEqual(
            dm.HydraulicSample(
                datetime_value=datetime.datetime(2020, 1, 1, 4)),
            h1.samples[7])
        self.assertEqual(
            dm.HydraulicSample(
                datetime_value=datetime.datetime(2020, 1, 1, 4, 30)),
            h1.samples[8])

    def test_merge_empty(self):
        h1_first_sample = datetime.datetime(2020, 1, 1)
        h1_interval = datetime.timedelta(seconds=3600)
        h1_num_samples = 7

        h1 = dm.Hydraulics(
            samples=[dm.HydraulicSample(
                datetime_value=h1_first_sample + i * h1_interval)
                for i in range(h1_num_samples)])

        h2 = dm.Hydraulics()

        h1.merge(h2)
        self.assertEqual(
            dm.HydraulicSample(datetime_value=datetime.datetime(2020, 1, 1)),
            h1.samples[0])
        self.assertEqual(
            dm.HydraulicSample(
                datetime_value=datetime.datetime(2020, 1, 1, 1)),
            h1.samples[1])
        self.assertEqual(
            dm.HydraulicSample(
                datetime_value=datetime.datetime(2020, 1, 1, 2)),
            h1.samples[2])
        self.assertEqual(
            dm.HydraulicSample(
                datetime_value=datetime.datetime(2020, 1, 1, 3)),
            h1.samples[3])
        self.assertEqual(
            dm.HydraulicSample(
                datetime_value=datetime.datetime(2020, 1, 1, 4)),
            h1.samples[4])
        self.assertEqual(
            dm.HydraulicSample(
                datetime_value=datetime.datetime(2020, 1, 1, 5)),
            h1.samples[5])
        self.assertEqual(
            dm.HydraulicSample(
                datetime_value=datetime.datetime(2020, 1, 1, 6)),
            h1.samples[6])

    def test_merge_single(self):
        h1_first_sample = datetime.datetime(2020, 1, 1)
        h1_interval = datetime.timedelta(seconds=3600)
        h1_num_samples = 7

        h1 = dm.Hydraulics(
            samples=[dm.HydraulicSample(
                datetime_value=h1_first_sample + i * h1_interval)
                for i in range(h1_num_samples)])

        h2 = dm.Hydraulics(
            samples=[dm.HydraulicSample(
                datetime_value=datetime.datetime(2020, 1, 1, 3))])

        h1.merge(h2)
        self.assertEqual(
            dm.HydraulicSample(datetime_value=datetime.datetime(2020, 1, 1)),
            h1.samples[0])
        self.assertEqual(
            dm.HydraulicSample(
                datetime_value=datetime.datetime(2020, 1, 1, 1)),
            h1.samples[1])
        self.assertEqual(
            dm.HydraulicSample(
                datetime_value=datetime.datetime(2020, 1, 1, 2)),
            h1.samples[2])
        self.assertEqual(
            dm.HydraulicSample(
                datetime_value=datetime.datetime(2020, 1, 1, 4)),
            h1.samples[3])
        self.assertEqual(
            dm.HydraulicSample(
                datetime_value=datetime.datetime(2020, 1, 1, 5)),
            h1.samples[4])
        self.assertEqual(
            dm.HydraulicSample(
                datetime_value=datetime.datetime(2020, 1, 1, 6)),
            h1.samples[5])
        self.assertEqual(
            dm.HydraulicSample(
                datetime_value=datetime.datetime(2020, 1, 1, 3)),
            h1.samples[6])


def suite():
    return unittest.makeSuite(HydraulicsTestCase, 'test')


if __name__ == '__main__':
    unittest.main(defaultTest='suite')
