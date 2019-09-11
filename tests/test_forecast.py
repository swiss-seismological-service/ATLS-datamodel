# Copyright (C) 2019, ETH Zurich - Swiss Seismological Service SED
"""
Seismics related test facilities.
"""

import datetime
import unittest

from ramsis.datamodel.status import EStatus, Status  # noqa
from ramsis.datamodel.seismicity import (
    SeismicityModel, SeismicityModelRun, ReservoirSeismicityPrediction)  # noqa
from ramsis.datamodel.forecast import (
    Forecast, ForecastScenario, SeismicityForecastStage) # noqa
from ramsis.datamodel.seismics import SeismicCatalog, SeismicEvent  # noqa
from ramsis.datamodel.well import InjectionWell, WellSection  # noqa
from ramsis.datamodel.hydraulics import Hydraulics, InjectionPlan  # noqa
from ramsis.datamodel.settings import ProjectSettings  # noqa
from ramsis.datamodel.project import Project  # noqa


class ForecastTestCase(unittest.TestCase):
    """
    Test cases for :py:class:`ramsis.datamodel.forecast.Forecast`.
    """

    def test_clone_without_results(self):
        model = SeismicityModel(
            name='EM1.1',
            enabled=True,
            sfmwid='EM1',
            url='http://localhost:5000',
            config={'foo': 42})

        model_run = SeismicityModelRun(
            model=model,
            status=Status(state=EStatus.COMPLETE),
            result=ReservoirSeismicityPrediction(
                geom=('POLYHEDRALSURFACE Z '
                      '(((0 0 0, 0 2 0, 2 2 0, 2 0 0, 0 0 0)),'
                      '((0 0 0, 0 2 0, 0 2 2, 0 0 2, 0 0 0)),'
                      '((0 0 0, 2 0 0, 2 0 2, 0 0 2, 0 0 0)),'
                      '((2 2 2, 2 0 2, 0 0 2, 0 2 2, 2 2 2)),'
                      '((2 2 2, 2 0 2, 2 0 0, 2 2 0, 2 2 2)),'
                      '((2 2 2, 2 2 0, 0 2 0, 0 2 2, 2 2 2)))')))

        fc_stage = SeismicityForecastStage(
            config={},
            enabled=True,
            runs=[model_run, ])

        fc_scenario = ForecastScenario(stages=[fc_stage, ],
                                       well=InjectionWell())

        fc = Forecast(name='Forecast',
                      config={},
                      scenarios=[fc_scenario, ],
                      starttime=datetime.datetime.utcnow(),
                      endtime=datetime.datetime.utcnow(),
                      seismiccatalog=SeismicCatalog(),
                      well=InjectionWell())

        cloned = fc.clone(with_results=False)

        # FIXME(damb): Instead implement Forecast.__eq__ and make use of it
        # Currently, just the sensible attributes are checked.
        self.assertEqual(cloned.seismiccatalog, None)
        self.assertEqual(cloned.well, None)
        self.assertEqual(cloned.scenarios[0].well, fc.scenarios[0].well)
        self.assertEqual(cloned.scenarios[0].stages[0].runs[0].status.state,
                         EStatus.PENDING)
        self.assertEqual(cloned.scenarios[0].stages[0].runs[0].result, None)
