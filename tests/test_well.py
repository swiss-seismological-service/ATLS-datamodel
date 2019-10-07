# Copyright (C) 2019, ETH Zurich - Swiss Seismological Service SED
"""
Well related test facilities.
"""

import datetime
import unittest
import uuid

import ramsis.datamodel as dm


class InjectionWellTestCase(unittest.TestCase):
    """
    Test cases for :py:class:`ramsis.datamodel.well.InjectionWell`.
    """

    def test_longitude(self):
        reference_result = 8.925293642
        bh = dm.InjectionWell()
        s0 = dm.WellSection(toplongitude_value=reference_result,
                            toplatitude_value=46.90669014,
                            topdepth_value=0,
                            bottomlongitude_value=9,
                            bottomlatitude_value=47,
                            bottomdepth_value=500,
                            holediameter_value=0.3,
                            casingdiameter_value=0.25)
        s1 = dm.WellSection(toplongitude_value=9,
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
        bh = dm.InjectionWell()
        s0 = dm.WellSection(toplongitude_value=8.925293642,
                            toplatitude_value=reference_result,
                            topdepth_value=0,
                            bottomlongitude_value=9,
                            bottomlatitude_value=47,
                            bottomdepth_value=500,
                            holediameter_value=0.3,
                            casingdiameter_value=0.25)
        s1 = dm.WellSection(toplongitude_value=9,
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
        bh = dm.InjectionWell()
        s0 = dm.WellSection(toplongitude_value=8.925293642,
                            toplatitude_value=46.90669014,
                            topdepth_value=0,
                            bottomlongitude_value=9,
                            bottomlatitude_value=47,
                            bottomdepth_value=500,
                            holediameter_value=0.3,
                            casingdiameter_value=0.25)
        s1 = dm.WellSection(toplongitude_value=9,
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
        bh = dm.InjectionWell()
        s0 = dm.WellSection(toplongitude_value=8.925293642,
                            toplatitude_value=46.90669014,
                            topdepth_value=0,
                            bottomlongitude_value=9,
                            bottomlatitude_value=47,
                            bottomdepth_value=500,
                            holediameter_value=0.3,
                            casingdiameter_value=0.25)
        s1 = dm.WellSection(toplongitude_value=9,
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
            dm.HydraulicSample(datetime_value=dt + i * interval,
                               topflow_value=i,
                               bottomflow_value=i - delta_flow)
            for i in range(num_samples)]
        s0 = dm.WellSection(toplongitude_value=8.925293642,
                            toplatitude_value=46.90669014,
                            topdepth_value=0,
                            bottomlongitude_value=9,
                            bottomlatitude_value=47,
                            bottomdepth_value=500,
                            holediameter_value=0.3,
                            casingdiameter_value=0.25,
                            hydraulics=dm.Hydraulics(samples=samples))
        bh = dm.InjectionWell(
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
            dm.HydraulicSample(datetime_value=dt + i * interval,
                               topflow_value=i,
                               bottomflow_value=i - delta_flow)
            for i in range(num_samples)]
        s0 = dm.WellSection(toplongitude_value=8.925293642,
                            toplatitude_value=46.90669014,
                            topdepth_value=0,
                            bottomlongitude_value=9,
                            bottomlatitude_value=47,
                            bottomdepth_value=500,
                            holediameter_value=0.3,
                            casingdiameter_value=0.25,
                            hydraulics=dm.Hydraulics(samples=samples))
        bh = dm.InjectionWell(
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
            dm.HydraulicSample(datetime_value=dt + i * interval,
                               topflow_value=i,
                               bottomflow_value=i - delta_flow)
            for i in range(num_samples)]
        s0 = dm.WellSection(toplongitude_value=8.925293642,
                            toplatitude_value=46.90669014,
                            topdepth_value=0,
                            bottomlongitude_value=9,
                            bottomlatitude_value=47,
                            bottomdepth_value=500,
                            holediameter_value=0.3,
                            casingdiameter_value=0.25,
                            hydraulics=dm.Hydraulics(samples=samples))
        s1 = dm.WellSection(toplongitude_value=9,
                            toplatitude_value=47,
                            topdepth_value=500,
                            bottomlongitude_value=9.01,
                            bottomlatitude_value=47.01,
                            bottomdepth_value=1500,
                            holediameter_value=0.25,
                            casingdiameter_value=0)

        bh = dm.InjectionWell(
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

    def test_merge_update_mutable(self):
        bh_id = str(uuid.uuid4())
        dt = datetime.datetime(2020, 1, 1)
        delta = datetime.timedelta(days=365)

        bh0 = dm.InjectionWell(
            publicid=bh_id,
            creationinfo_creationtime=dt)

        bh1 = dm.InjectionWell(
            publicid=bh_id,
            creationinfo_creationtime=dt + delta)

        bh0.merge(bh1)

        self.assertEqual(bh0.creationinfo_creationtime, dt + delta)

    def test_merge_update_section(self):
        bh_id = str(uuid.uuid4())
        dt = datetime.datetime(2020, 1, 1)
        delta = datetime.timedelta(days=365)

        sec_id = str(uuid.uuid4())
        s0 = dm.WellSection(publicid=sec_id,
                            starttime=dt,
                            endtime=None)
        s1 = dm.WellSection(publicid=sec_id,
                            starttime=dt,
                            endtime=dt + delta)

        bh0 = dm.InjectionWell(
            publicid=bh_id,
            sections=[s0, ])

        bh1 = dm.InjectionWell(
            publicid=bh_id,
            sections=[s1, ])

        bh0.merge(bh1)

        self.assertEqual(bh0.sections[0].endtime, dt + delta)

    def test_merge_append_section(self):
        bh_id = str(uuid.uuid4())
        dt = datetime.datetime(2020, 1, 1)
        delta = datetime.timedelta(days=365)

        sec_id0 = str(uuid.uuid4())
        s0 = dm.WellSection(publicid=sec_id0,
                            starttime=dt,
                            endtime=None)
        sec_id1 = str(uuid.uuid4())
        s1 = dm.WellSection(publicid=sec_id1,
                            starttime=dt + delta,
                            endtime=None)

        bh0 = dm.InjectionWell(
            publicid=bh_id,
            sections=[s0, ])

        bh1 = dm.InjectionWell(
            publicid=bh_id,
            sections=[s1, ])

        bh0.merge(bh1)

        self.assertEqual(len(bh0.sections), 2)

    def test_merge_to_empty(self):
        bh0 = dm.InjectionWell()

        bh_id = str(uuid.uuid4())
        sec_id = str(uuid.uuid4())
        dt = datetime.datetime(2020, 1, 1)
        s0 = dm.WellSection(publicid=sec_id,
                            starttime=dt,
                            endtime=None,
                            toplongitude_value=8.925293642,
                            toplatitude_value=46.90669014,
                            topdepth_value=0,
                            bottomlongitude_value=9,
                            bottomlatitude_value=47,
                            bottomdepth_value=500,
                            holediameter_value=0.3,
                            casingdiameter_value=0.25)
        bh1 = dm.InjectionWell(
            publicid=bh_id,
            sections=[s0, ])

        bh0.merge(bh1, merge_undefined=True)

        self.assertEqual(bh0.publicid, bh1.publicid)
        self.assertEqual(len(bh0.sections), 1)
        self.assertEqual(len(bh1.sections), 0)


class WellSectionTestCase(unittest.TestCase):
    """
    Test cases for :py:class:`ramsis.datamodel.well.WellSection`.
    """

    def test_merge_update_mutable(self):
        dt = datetime.datetime(2020, 1, 1)
        interval = datetime.timedelta(seconds=3600)
        num_samples = 7
        delta_flow = 0.1
        samples = [
            dm.HydraulicSample(datetime_value=dt + i * interval,
                               topflow_value=i,
                               bottomflow_value=i - delta_flow)
            for i in range(num_samples)]
        sec_id = str(uuid.uuid4())
        s0 = dm.WellSection(publicid=sec_id,
                            starttime=dt,
                            endtime=None,
                            toplongitude_value=8.925293642,
                            toplatitude_value=46.90669014,
                            topdepth_value=0,
                            bottomlongitude_value=9,
                            bottomlatitude_value=47,
                            bottomdepth_value=500,
                            holediameter_value=0.3,
                            casingdiameter_value=0.25,
                            hydraulics=dm.Hydraulics(samples=samples))
        s1 = dm.WellSection(publicid=sec_id,
                            starttime=dt,
                            endtime=dt + (num_samples - 1) * interval,
                            toplongitude_value=8.925293642,
                            toplatitude_value=46.90669014,
                            topdepth_value=0,
                            bottomlongitude_value=9,
                            bottomlatitude_value=47,
                            bottomdepth_value=500,
                            holediameter_value=0.3,
                            casingdiameter_value=0.25)

        s0.merge(s1)

        self.assertEqual(s0.endtime, dt + (num_samples - 1) * interval)
        self.assertEqual(len(samples), len(s0.hydraulics.samples))

    def test_merge_append_samples(self):
        dt0 = datetime.datetime(2020, 1, 1)
        interval = datetime.timedelta(seconds=3600)
        num_samples = 7
        delta_flow = 0.1
        samples0 = [
            dm.HydraulicSample(datetime_value=dt0 + i * interval,
                               topflow_value=i,
                               bottomflow_value=i - delta_flow)
            for i in range(num_samples)]

        dt1 = datetime.datetime(2021, 1, 1)
        samples1 = [
            dm.HydraulicSample(datetime_value=dt1 + i * interval,
                               topflow_value=i,
                               bottomflow_value=i - delta_flow)
            for i in range(num_samples)]

        sec_id = str(uuid.uuid4())
        s0 = dm.WellSection(publicid=sec_id,
                            starttime=dt0,
                            endtime=None,
                            toplongitude_value=8.925293642,
                            toplatitude_value=46.90669014,
                            topdepth_value=0,
                            bottomlongitude_value=9,
                            bottomlatitude_value=47,
                            bottomdepth_value=500,
                            holediameter_value=0.3,
                            casingdiameter_value=0.25,
                            hydraulics=dm.Hydraulics(samples=samples0))
        s1 = dm.WellSection(publicid=sec_id,
                            starttime=dt1,
                            endtime=None,
                            toplongitude_value=8.925293642,
                            toplatitude_value=46.90669014,
                            topdepth_value=0,
                            bottomlongitude_value=9,
                            bottomlatitude_value=47,
                            bottomdepth_value=500,
                            holediameter_value=0.3,
                            casingdiameter_value=0.25,
                            hydraulics=dm.Hydraulics(samples=samples1))

        s0.merge(s1)

        self.assertEqual(s0.starttime, dt0)
        self.assertEqual(len(s0.hydraulics.samples),
                         len(samples0) + len(samples1))
        self.assertEqual(s0.hydraulics[0].datetime_value, dt0)
        self.assertEqual(s0.hydraulics[-1].datetime_value,
                         dt1 + (num_samples - 1) * interval)


def suite():
    suite = unittest.makeSuite(InjectionWellTestCase, 'test')
    suite.addTest(
        unittest.makeSuite(WellSectionTestCase, 'test'))
    return suite


if __name__ == '__main__':
    unittest.main(defaultTest='suite')
