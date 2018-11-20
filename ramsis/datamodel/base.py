# This is <base.py>
# ----------------------------------------------------------------------------
#
# Copyright (c) 2018 by Swiss Seismological Service (SED, ETHZ)
#
# REVISIONS and CHANGES
#    2018/01/24   V1.0   Daniel Armbruster (damb)
#
# ============================================================================
"""
General purpose datamodel facilities.
"""

from sqlalchemy import Column, Integer
from sqlalchemy.ext.declarative import declared_attr, declarative_base


# Base class for objects that are to be persisted by sqlalchemy
class Base(object):

    @declared_attr
    def __tablename__(cls):
        return cls.__name__.lower()

    id = Column(Integer, primary_key=True)

# class Base


OrmBase = declarative_base(cls=Base)


# ----- END OF base.py -----
