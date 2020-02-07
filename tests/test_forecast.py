# Copyright (C) 2019, ETH Zurich - Swiss Seismological Service SED
"""
Seismics related test facilities.
"""

import datetime
import unittest

import ramsis.datamodel as dm

from ramsis.datamodel.status import EStatus, Status  # noqa


class ForecastTestCase(unittest.TestCase):
    """
    Test cases for :py:class:`ramsis.datamodel.forecast.Forecast`.
    """

    def test_clone_without_results(self):
        model = dm.SeismicityModel(
            name='EM1.1',
            enabled=True,
            sfmwid='EM1',
            url='http://localhost:5000',
            config={'foo': 42})

        model_run = dm.SeismicityModelRun(
            model=model,
            status=dm.Status(state=EStatus.COMPLETE),
            result=dm.ReservoirSeismicityPrediction(
                x_min=-1000,
                x_max=1000,
                y_min=-1000,
                y_max=1000,
                z_min=-2000,
                z_max=0
                ))

        fc_stage = dm.SeismicityForecastStage(
            config={},
            enabled=True,
            runs=[model_run, ])

        fc_scenario = dm.ForecastScenario(stages=[fc_stage, ],
                                          well=dm.InjectionWell())

        fc = dm.Forecast(name='Forecast',
                         config={},
                         scenarios=[fc_scenario, ],
                         starttime=datetime.datetime.utcnow(),
                         endtime=datetime.datetime.utcnow(),
                         seismiccatalog=[dm.SeismicCatalog()],
                         well=[dm.InjectionWell()])

        cloned = fc.clone(with_results=False)

        # FIXME(damb): Instead implement Forecast.__eq__ and make use of it
        # Currently, just the sensible attributes are checked.
        self.assertEqual(cloned.seismiccatalog, [])
        self.assertEqual(cloned.well, [])
        self.assertEqual(cloned.scenarios[0].well, fc.scenarios[0].well)
        self.assertEqual(cloned.scenarios[0].stages[0].runs[0].status.state,
                         dm.EStatus.PENDING)
        self.assertEqual(cloned.scenarios[0].stages[0].runs[0].result, None)
