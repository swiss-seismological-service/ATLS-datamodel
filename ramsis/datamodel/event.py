# Copyright 2019, ETH Zurich - Swiss Seismological Service SED
"""
ORM event and signal facilities.
"""
from itertools import product

from sqlalchemy import event
from sqlalchemy.orm import class_mapper
from sqlalchemy.exc import ArgumentError

from ramsis.datamodel.status import Status  # noqa
from ramsis.datamodel.model import Model, ModelRun  # noqa
from ramsis.datamodel.hydraulics import (  # noqa
    Hydraulics, InjectionPlan, HydraulicSample)
from ramsis.datamodel.seismicity import (  # noqa
    SeismicityModel, SeismicityModelRun, ReservoirSeismicityPrediction,
    SeismicityPredictionBin)
from ramsis.datamodel.forecast import (  # noqa
    Forecast, ForecastScenario, ForecastStage, SeismicityForecastStage,
    SeismicitySkillStage, HazardStage, RiskStage)
from ramsis.datamodel.seismics import SeismicCatalog, SeismicEvent  # noqa
from ramsis.datamodel.well import InjectionWell, WellSection  # noqa
from ramsis.datamodel.settings import ProjectSettings  # noqa
from ramsis.datamodel.project import Project  # noqa
from ramsis.datamodel.base import ORMBase  # noqa


_SCALAR_EVENT_IDENTIFIERS = ('set', 'modified', 'init_scalar')
_COLLECTION_EVENT_IDENTIFIERS = (
    'append', 'bulk_replace', 'dispose_collection', 'init_collection',
    'remove')


def create_scalar_attribute_events(
    targets, listener, identifiers=_SCALAR_EVENT_IDENTIFIERS,
        propagate=False):
    """
    Factory for scalar attribute events.

    :param targets: The object instances receiving the event. When passing the
        mapping all available scalar properties receive the event (bulk
        registration).
    :param str identifier: List of string identifiers which identify the event
        to be intercepted.
    :param callable listener: Callable executed when the signal is received.
    :param bool propagate: When True, the listener function will be established
        not just for the targets given, but for attributes of the same name on
        all current subclasses of that class, as well as all future subclasses
        of that class, using an additional listener that listens for
        instrumentation events.
    """

    for i in identifiers:
        if i not in _SCALAR_EVENT_IDENTIFIERS:
            raise ValueError(f'Invalid identifier: {i!r}')

    if not isinstance(targets, list):
        targets = [targets]

    # expand targets
    expanded_targets = set([])
    for t in targets:
        try:
            mapper = class_mapper(t)

            rel_keys = set([c.key for c in mapper.relationships])
            fk_keys = set([c.key for c in mapper.columns if c.foreign_keys])
            omit = rel_keys | fk_keys

            expanded_targets |= set([p for p in mapper.iterate_properties
                                     if p.key not in omit])
        except ArgumentError:
            expanded_targets.add(t)

    for t, i in product(expanded_targets, identifiers):
        event.listen(t, i, listener, propagate=propagate, named=True)

    return expanded_targets


def create_collection_attribute_events(
    targets, listener, identifiers=_COLLECTION_EVENT_IDENTIFIERS,
        propagate=False):
    """
    Factory for collection attribute events.

    :param targets: The object instances receiving the event. When passing the
        mapping all available scalar properties receive the event (bulk
        registration).
    :type targets: Mapping, collection attribute or list of a combination of
        both
    :param callable listener: Callable executed when the signal is received.
    :type identifiers: Collection attribute event identifiers
    :param bool propagate: Propagate event listening to subclasses
    """

    for i in identifiers:
        if i not in _COLLECTION_EVENT_IDENTIFIERS:
            raise ValueError(f'Invalid identifier: {i!r}')

    if not isinstance(targets, list):
        targets = [targets]

    # expand targets
    expanded_targets = set([])
    for t in targets:
        try:
            mapper = class_mapper(t)

            rel_keys = set([c.key for c in mapper.relationships])

            expanded_targets |= set([p for p in mapper.iterate_properties
                                     if p.key in rel_keys])
        except ArgumentError:
            expanded_targets.add(t)

    for t, i in product(expanded_targets, identifiers):
        event.listen(t, i, listener, propagate=propagate, named=True)

    return expanded_targets


class AttributeEvents:
    """
    Base class for attribute events.
    """

    TARGET = None

    def __init__(
        self, target=None, listener=None,
        scalar_identifiers=_SCALAR_EVENT_IDENTIFIERS,
        collection_identifiers=_COLLECTION_EVENT_IDENTIFIERS,
            propagate=False):
        """
        :param target: The object instance receiving the event. When passing
            the mapping all available attributes receive the event (bulk
            registration).
        :param target: Targets events should be registered for
        :param callable listener: Callback executed when the event is fired
        :param scalar_identifiers: List of scalar attribute event identifiers
        :param collection_identifiers: List of collection attribute event
            identifiers
        :param bool propagate: Propagate event listening to subclasses
        """

        self._target = target or self.TARGET
        assert self._target, "Missing target."

        self._listener = listener
        self._scalar_identifiers = scalar_identifiers
        self._scalar_targets = None
        self._collection_identifiers = collection_identifiers
        self._collection_targets = None
        self._propagate = propagate

    def listen(self, listener=None):
        """
        Register and listen to attribute events.

        :param callable listener: Callback executed when the event is fired
        """

        if not listener:
            listener = self._listener

        if not listener:
            raise ValueError(f'Invalid value: {listener}')

        if self._scalar_identifiers:
            self._scalar_targets = create_scalar_attribute_events(
                self._target, listener, self._scalar_identifiers,
                self._propagate)

        if self._collection_identifiers:
            self._collection_targets = create_collection_attribute_events(
                self._target, listener, self._collection_identifiers,
                self._propagate)

    def remove(self, target=None):
        """
        Remove attribute events

        :param target: Target mapping attribute event listening should be
            removed for
        """

        if self._scalar_targets and target in self._scalar_targets:
            for identifier in self._scalar_identifiers:
                event.remove(target, identifier, self._listener)
                self._scalar_targets.remove(target)

        elif self._collection_targets and target in self._collection_targets:
            for identifier in self._collection_identifiers:
                event.remove(target, identifier, self._listener)
                self._collection_targets.remove(target)
        else:
            if self._scalar_targets:
                for t, i in product(self._scalar_targets,
                                    self._scalar_identifiers):
                    event.remove(t, i, self._listener)

                self._scalar_targets = None

            if self._collection_targets:
                for t, i in product(self._collection_targets,
                                    self._collection_identifiers):
                    event.remove(t, i, self._listener)

                self._collection_targets = None

    def contains(self, target, identifier):
        """
        Return :code:`True` if attribute event listening is set up for the
        combination of :code:`target` and :code:`identifier`.
        """

        if ((self._scalar_targets and
            target in self._scalar_targets and
            self._scalar_identifiers and
            identifier in self._scalar_identifiers) or
            (self._collection_targets and
            target in self._collection_targets and
            self._collection_identifiers and
                identifier in self._collection_identifiers)):
            return True

        return False


class EntityAttributeEventMixin(AttributeEvents):

    def __init__(self, listener, scalar_identifiers=['set', 'modified'],
                 collection_identifiers=['append', 'dispose_collection',
                                         'bulk_replace', 'init_collection',
                                         'remove'],
                 propagate=False):
        super().__init__(
            listener=listener, scalar_identifiers=scalar_identifiers,
            collection_identifiers=collection_identifiers, propagate=propagate)


class ProjectAttributeEvents(EntityAttributeEventMixin, AttributeEvents):
    """
    Attribute events for :py:class:`ramsis.datamodel.project.Project`.
    """

    TARGET = Project


class ProjectSettingsAttributeEvents(EntityAttributeEventMixin,
                                     AttributeEvents):
    """
    Attribute events for :py:class:`ramsis.datamodel.settings.ProjectSettings`.
    """

    TARGET = ProjectSettings


class ForecastAttributeEvents(EntityAttributeEventMixin, AttributeEvents):
    """
    Attribute events for :py:class:`ramsis.datamodel.forecast.Forecast`.
    """

    TARGET = Forecast


class SeismicCatalogAttributeEvents(EntityAttributeEventMixin,
                                    AttributeEvents):
    """
    Attribute events for :py:class:`ramsis.datamodel.seismics.SeismicCatalog`.
    
    An exemplary usage example adapting SQLAlchemy events to PyQt5 signals:

    .. code-block:: python

        import datetime

        from PyQt5 import QtCore

        from ramsis.datamodel.base import ORMBase  # noqa
        from ramsis.datamodel.event import (
            SeismicCatalogAttributeEvents)
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


        class Example(QtCore.QObject):

            cat_modified = QtCore.pyqtSignal(object)

            def __init__(self):
                super().__init__()
                self.cat = SeismicCatalog()

                # configure event listening for attribute events of a catalog
                def cat_listener(**kwargs):
                    self.cat_modified.emit(kwargs['target'])

                # configure scalar events only
                self._orm_events = SeismicCatalogAttributeEvents(
                    listener=cat_listener,
                    scalar_identifiers=['set', 'modified'],
                    collection_identifiers=[])

                self._orm_events.listen()
                self.cat_modified.connect(self._on_catalog_modified)

            def _on_catalog_modified(self, value):
                print(f'Catalog modified: {value}')
    """

    TARGET = SeismicCatalog


class InjectionWellAttributeEvents(EntityAttributeEventMixin, AttributeEvents):
    """
    Attribute events for :py:class:`ramsis.datamodel.well.InjectionWell`.
    """

    TARGET = InjectionWell
