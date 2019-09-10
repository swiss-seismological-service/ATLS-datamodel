# Copyright (C) 2019, ETH Zurich - Swiss Seismological Service SED
"""
General purpose utils.
"""

from sqlalchemy.orm import class_mapper


def clone(obj, with_foreignkeys=False):
    """
    Clone a `SQLAlchemy <https://www.sqlalchemy.org/>`_ mapping object omitting
    the object's primary key.

    :param obj: SQLAlchemy mapping object to be cloned.
    :param bool with_foreignkeys: Include foreign keys while copying

    :returns: Cloned SQLAlchemy mapping object.
    """
    mapper = class_mapper(type(obj))
    new = type(obj)()

    pk_keys = set([c.key for c in mapper.primary_key])
    rel_keys = set([c.key for c in mapper.relationships])
    omit = pk_keys | rel_keys

    if not with_foreignkeys:
        fk_keys = set([c.key for c in mapper.columns if c.foreign_keys])
        omit = omit | fk_keys

    for attr in [p.key for p in mapper.iterate_properties
                 if p.key not in omit]:
        try:
            value = getattr(obj, attr)
            setattr(new, attr, value)
        except AttributeError:
            pass

    return new
