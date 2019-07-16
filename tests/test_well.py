# Copyright (C) 2019, ETH Zurich - Swiss Seismological Service SED
"""
Well related test facilities.
"""

import datetime
import unittest
import uuid

from ramsis.datamodel.status import Status  # noqa
from ramsis.datamodel.seismicity import SeismicityModel  # noqa
from ramsis.datamodel.forecast import Forecast  # noqa
from ramsis.datamodel.seismics import SeismicCatalog, SeismicEvent  # noqa
from ramsis.datamodel.well import InjectionWell, WellSection  # noqa
from ramsis.datamodel.hydraulics import (  # noqa
    Hydraulics, InjectionPlan, HydraulicSample)  # noqa
from ramsis.datamodel.settings import ProjectSettings  # noqa
from ramsis.datamodel.project import Project  # noqa


class InjectionWellTestCase(unittest.TestCase):
    """
    Test cases for :py:class:`ramsis.datamodel.well.InjectionWell`.
    """

    def test_longitude(self):
        reference_result = 8.925293642
        bh = InjectionWell()
        s0 = WellSection(toplongitude_value=reference_result,
                         toplatitude_value=46.90669014,
                         topdepth_value=0,
                         bottomlongitude_value=9,
                         bottomlatitude_value=47,
                         bottomdepth_value=500,
                         holediameter_value=0.3,
                         casingdiameter_value=0.25)
        s1 = WellSection(toplongitude_value=9,
                         toplatitude_value=47,
                         topdepth_value=500,
                         bottomlongitude_value=9.01,
                         bottomlatitude_value=47.01,
                         bottomdepth_value=1500,
                         holediameter_value=0.25,
                         casingdiameter_value=0)

        bh.sections = [s0, s1]

        self.assertEqual(bh.longitude, reference_result)

    def test_latitude(self):
        reference_result = 46.90669014
        bh = InjectionWell()
        s0 = WellSection(toplongitude_value=8.925293642,
                         toplatitude_value=reference_result,
                         topdepth_value=0,
                         bottomlongitude_value=9,
                         bottomlatitude_value=47,
                         bottomdepth_value=500,
                         holediameter_value=0.3,
                         casingdiameter_value=0.25)
        s1 = WellSection(toplongitude_value=9,
                         toplatitude_value=47,
                         topdepth_value=500,
                         bottomlongitude_value=9.01,
                         bottomlatitude_value=47.01,
                         bottomdepth_value=1500,
                         holediameter_value=0.25,
                         casingdiameter_value=0)

        bh.sections = [s0, s1]

        self.assertEqual(bh.latitude, reference_result)

    def test_depth(self):
        reference_result = 1500
        bh = InjectionWell()
        s0 = WellSection(toplongitude_value=8.925293642,
                         toplatitude_value=46.90669014,
                         topdepth_value=0,
                         bottomlongitude_value=9,
                         bottomlatitude_value=47,
                         bottomdepth_value=500,
                         holediameter_value=0.3,
                         casingdiameter_value=0.25)
        s1 = WellSection(toplongitude_value=9,
                         toplatitude_value=47,
                         topdepth_value=500,
                         bottomlongitude_value=9.01,
                         bottomlatitude_value=47.01,
                         bottomdepth_value=reference_result,
                         holediameter_value=0.25,
                         casingdiameter_value=0)

        bh.sections = [s0, s1]

        self.assertEqual(bh.depth, reference_result)

    def test_injectionpoint(self):
        reference_result = (9, 47, 500)
        bh = InjectionWell()
        s0 = WellSection(toplongitude_value=8.925293642,
                         toplatitude_value=46.90669014,
                         topdepth_value=0,
                         bottomlongitude_value=9,
                         bottomlatitude_value=47,
                         bottomdepth_value=500,
                         holediameter_value=0.3,
                         casingdiameter_value=0.25)
        s1 = WellSection(toplongitude_value=9,
                         toplatitude_value=47,
                         topdepth_value=500,
                         bottomlongitude_value=9.01,
                         bottomlatitude_value=47.01,
                         bottomdepth_value=1500,
                         holediameter_value=0.25,
                         casingdiameter_value=0)

        bh.sections = [s0, s1]

        self.assertEqual(bh.injectionpoint, reference_result)

    def test_snapshot_no_filter(self):
        dt = datetime.datetime(2020, 1, 1)
        interval = datetime.timedelta(seconds=3600)
        num_samples = 7
        delta_flow = 0.1
        samples = [
            HydraulicSample(datetime_value=dt + i * interval,
                            topflow_value=i,
                            bottomflow_value=i - delta_flow)
            for i in range(num_samples)]
        s0 = WellSection(toplongitude_value=8.925293642,
                         toplatitude_value=46.90669014,
                         topdepth_value=0,
                         bottomlongitude_value=9,
                         bottomlatitude_value=47,
                         bottomdepth_value=500,
                         holediameter_value=0.3,
                         casingdiameter_value=0.25,
                         hydraulics=Hydraulics(samples=samples))
        bh = InjectionWell(
            publicid=str(uuid.uuid4()),
            sections=[s0, ])

        snap = bh.snapshot()

        self.assertNotEqual(id(bh), id(snap))
        self.assertEqual(bh.publicid, snap.publicid)
        self.assertNotEqual(id(bh.sections[0]), id(snap.sections[0]))

        bh_hydraulics = bh.sections[0].hydraulics
        snap_hydraulics = snap.sections[0].hydraulics
        self.assertNotEqual(id(bh_hydraulics), id(snap_hydraulics))
        self.assertEqual(bh_hydraulics, snap_hydraulics)

    def test_snapshot_sample_filter(self):
        dt = datetime.datetime(2020, 1, 1)
        interval = datetime.timedelta(seconds=3600)
        num_samples = 7
        delta_flow = 0.1
        samples = [
            HydraulicSample(datetime_value=dt + i * interval,
                            topflow_value=i,
                            bottomflow_value=i - delta_flow)
            for i in range(num_samples)]
        s0 = WellSection(toplongitude_value=8.925293642,
                         toplatitude_value=46.90669014,
                         topdepth_value=0,
                         bottomlongitude_value=9,
                         bottomlatitude_value=47,
                         bottomdepth_value=500,
                         holediameter_value=0.3,
                         casingdiameter_value=0.25,
                         hydraulics=Hydraulics(samples=samples))
        bh = InjectionWell(
            publicid=str(uuid.uuid4()),
            sections=[s0, ])

        def remove_last(s):
            return s.topflow_value != 6

        snap = bh.snapshot(sample_filter_cond=remove_last)

        self.assertNotEqual(id(bh), id(snap))
        self.assertEqual(bh.publicid, snap.publicid)
        self.assertNotEqual(id(bh.sections[0]), id(snap.sections[0]))

        bh_hydraulics = bh.sections[0].hydraulics
        snap_hydraulics = snap.sections[0].hydraulics
        self.assertNotEqual(id(bh_hydraulics), id(snap_hydraulics))
        self.assertNotEqual(bh_hydraulics, snap_hydraulics)
        self.assertEqual(7, len(bh_hydraulics))
        self.assertEqual(6, len(snap_hydraulics))

    def test_snapshot_section_filter(self):
        dt = datetime.datetime(2020, 1, 1)
        interval = datetime.timedelta(seconds=3600)
        num_samples = 7
        delta_flow = 0.1
        samples = [
            HydraulicSample(datetime_value=dt + i * interval,
                            topflow_value=i,
                            bottomflow_value=i - delta_flow)
            for i in range(num_samples)]
        s0 = WellSection(toplongitude_value=8.925293642,
                         toplatitude_value=46.90669014,
                         topdepth_value=0,
                         bottomlongitude_value=9,
                         bottomlatitude_value=47,
                         bottomdepth_value=500,
                         holediameter_value=0.3,
                         casingdiameter_value=0.25,
                         hydraulics=Hydraulics(samples=samples))
        s1 = WellSection(toplongitude_value=9,
                         toplatitude_value=47,
                         topdepth_value=500,
                         bottomlongitude_value=9.01,
                         bottomlatitude_value=47.01,
                         bottomdepth_value=1500,
                         holediameter_value=0.25,
                         casingdiameter_value=0)

        bh = InjectionWell(
            publicid=str(uuid.uuid4()),
            sections=[s0, s1, ])

        def remove_lower_section(s):
            return (s.topdepth_value == 0 and
                    s.bottomdepth_value == 500)

        snap = bh.snapshot(section_filter_cond=remove_lower_section)

        self.assertNotEqual(id(bh), id(snap))
        self.assertEqual(bh.publicid, snap.publicid)
        self.assertEqual(2, len(bh.sections))
        self.assertEqual(1, len(snap.sections))
        self.assertNotEqual(id(bh.sections[0]), id(snap.sections[0]))

        bh_hydraulics = bh.sections[0].hydraulics
        snap_hydraulics = snap.sections[0].hydraulics
        self.assertNotEqual(id(bh_hydraulics), id(snap_hydraulics))
        self.assertEqual(bh_hydraulics, snap_hydraulics)


def suite():
    return unittest.makeSuite(InjectionWellTestCase, 'test')


if __name__ == '__main__':
    unittest.main(defaultTest='suite')
