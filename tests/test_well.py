# Copyright (C) 2019, ETH Zurich - Swiss Seismological Service SED
"""
Well related test facilities.
"""

import unittest

from ramsis.datamodel.status import Status  # noqa
from ramsis.datamodel.seismicity import SeismicityModel  # noqa
from ramsis.datamodel.forecast import Forecast  # noqa
from ramsis.datamodel.seismics import SeismicCatalog, SeismicEvent  # noqa
from ramsis.datamodel.well import InjectionWell, WellSection  # noqa
from ramsis.datamodel.hydraulics import Hydraulics, InjectionPlan  # noqa
from ramsis.datamodel.settings import ProjectSettings  # noqa
from ramsis.datamodel.project import Project  # noqa


class InjectionWellTestCase(unittest.TestCase):

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


def suite():
    return unittest.makeSuite(InjectionWellTestCase, 'test')


if __name__ == '__main__':
    unittest.main(defaultTest='suite')
