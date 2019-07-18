# Copyright 2019, ETH Zurich - Swiss Seismological Service SED
"""
Injection well ORM facilities.
"""

import inspect

from sqlalchemy import Column, Integer, Boolean, String, ForeignKey
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import relationship

from ramsis.datamodel.base import (ORMBase, CreationInfoMixin, PublicIDMixin,
                                   UniqueOpenEpochMixin, RealQuantityMixin,
                                   DeleteMultiParentOrphanMixin)
from ramsis.datamodel.utils import clone


_ci_attrs = inspect.getmembers(CreationInfoMixin,
                               lambda a: not(inspect.isroutine(a)))
_ci_attrs = [a[0] for a in _ci_attrs if not(a[0].startswith('__') and
                                            a[0].endswith('__'))]


class InjectionWell(DeleteMultiParentOrphanMixin(['project',
                                                  'forecast',
                                                  'forecastscenario']),
                    PublicIDMixin,
                    CreationInfoMixin,
                    RealQuantityMixin('bedrockdepth', optional=True),
                    ORMBase):
    """
    ORM injection well representation.

    .. note::

        *Point quantities* are implemented as `QuakeML
        <https://quake.ethz.ch/quakeml>`_ real quantities.
    """
    # relation: Project
    project_id = Column(Integer, ForeignKey('project.id'))
    project = relationship('Project', back_populates='wells')
    # relation: Forecast
    forecast_id = Column(Integer, ForeignKey('forecast.id'))
    forecast = relationship('Forecast', back_populates='well')
    # relation: ForecastScenario
    scenario_id = Column(Integer, ForeignKey('forecastscenario.id'))
    scenario = relationship('ForecastScenario', back_populates='well')

    # relation: WellSection
    sections = relationship('WellSection',
                            back_populates='well',
                            cascade='all, delete-orphan')

    @hybrid_property
    def longitude(self):
        # min topdepth defines top-section
        return min([s for s in self.sections],
                   key=lambda x: x.topdepth_value).toplongitude_value

    @hybrid_property
    def latitude(self):
        # min topdepth defines top-section
        return min([s for s in self.sections],
                   key=lambda x: x.topdepth_value).toplatitude_value

    @hybrid_property
    def depth(self):
        # max bottomdepth defines bottom-section
        return max([s.bottomdepth_value for s in self.sections])

    @hybrid_property
    def injectionpoint(self):
        """
        Injection point of the borehole. It is defined by the uppermost
        section's bottom with casing and an open bottom.

        .. note::

            The implementation requires boreholes to be linear.
        """
        isection = min([s for s in self.sections
                       if s.casingdiameter_value and not s.bottomclosed],
                       key=lambda x: x.bottomdepth_value, default=None)

        if not isection:
            raise ValueError('Cased borehole has a closed bottom.')

        return (isection.bottomlongitude_value,
                isection.bottomlatitude_value,
                isection.bottomdepth_value)

    def snapshot(self, section_filter_cond=None, sample_filter_cond=None):
        """
        Create a snapshot of the injection well.

        :param section_filter_cond: Callable applied on well sections when
            creating the snapshot
        :type section_filter_cond: callable or None
        :param sample_filter_cond: Callable applied on hydraulic samples when
            creating the snapshot
        :type sample_filter_cond: callable or None

        :returns: Snapshot of the injection well
        :rtype: :py:class:`InjectionWell`
        """
        snap = type(self)()
        snap.publicid = self.publicid
        snap.sections = [s.snapshot(filter_cond=sample_filter_cond)
                         for s in list(filter(section_filter_cond,
                                              self.sections))]
        return snap

    def merge(self, other):
        """
        Merge this injection well with another injection well.

        :param other: Injection well to be merged
        :type other: :py:class:`InjectionWell`
        """
        assert isinstance(other, type(self)), \
            "other is not of type InjectionWell."

        def section_lookup_by_publicid(publicid):
            for k, v in enumerate(self.sections):
                if v.publicid == publicid:
                    return self[k]
            return None

        if self.publicid == other.publicid:

            MUTABLE_ATTRS = _ci_attrs
            for attr in MUTABLE_ATTRS:
                value = getattr(other, attr)
                setattr(self, attr, value)

            for sec in other.sections:
                _sec = section_lookup_by_publicid(sec.publicid)
                if _sec is None:
                    self.sections.append(sec)
                else:
                    _sec.merge(sec)

    def __iter__(self):
        for s in self.sections:
            yield s

    def __getitem__(self, item):
        return self.sections[item] if self.sections else None

    def __repr__(self):
        return ("<{}(publicid={!r}, longitude={}, latitude={}, "
                "depth={})>").format(type(self).__name__, self.publicid,
                                     self.longitude, self.latitude, self.depth)


class WellSection(PublicIDMixin,
                  CreationInfoMixin,
                  UniqueOpenEpochMixin,
                  RealQuantityMixin('toplongitude'),
                  RealQuantityMixin('toplatitude'),
                  RealQuantityMixin('topdepth'),
                  RealQuantityMixin('bottomlongitude'),
                  RealQuantityMixin('bottomlatitude'),
                  RealQuantityMixin('bottomdepth'),
                  RealQuantityMixin('holediameter', optional=True),
                  RealQuantityMixin('casingdiameter', optional=True),
                  ORMBase):
    """
    ORM implementation of a well section.
    """
    topclosed = Column(Boolean, default=False)
    bottomclosed = Column(Boolean, default=False)
    sectiontype = Column(String)
    casingtype = Column(String)
    description = Column(String)

    # relation: InjectionWell
    well_id = Column(Integer, ForeignKey('injectionwell.id'))
    well = relationship('InjectionWell', back_populates='sections')

    # relation: Hydraulics
    hydraulics = relationship('Hydraulics',
                              back_populates='wellsection',
                              uselist=False,
                              cascade='all, delete-orphan')
    # relation: InjectionPlan
    injectionplan = relationship('InjectionPlan',
                                 back_populates='wellsection',
                                 uselist=False,
                                 cascade='all, delete-orphan')

    def snapshot(self, filter_cond=None):
        """
        Create a snapshot of the well section.

        :param filter_cond: Callable applied on hydraulic samples when creating
            the snapshot
        :type filter_cond: callable or None

        :returns: Snapshot of the well section
        :rtype: :py:class:`WellSection`
        """
        snap = clone(self)
        snap.hydraulics = self.hydraulics.snapshot(filter_cond=filter_cond)

        return snap

    def merge(self, other):
        """
        Merge this well section with another well section.

        :param other: Well section to be merged
        :type other: :py:class:`WellSection`
        """
        assert isinstance(other, type(self)) or other is None, \
            "other is not of type WellSection."

        if other and self.publicid == other.publicid:

            MUTABLE_ATTRS = _ci_attrs
            MUTABLE_ATTRS.append('endtime')

            # update mutable attributes
            for attr in MUTABLE_ATTRS:
                value = getattr(other, attr)
                setattr(self, attr, value)

            if self.hydraulics:
                self.hydraulics.merge(other.hydraulics)
            elif other.hydraulics:
                self.hydraulics = other.hydraulics.snapshot()
