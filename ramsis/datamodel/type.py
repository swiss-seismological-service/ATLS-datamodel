# This is <type.py>
# ----------------------------------------------------------------------------
#
# Copyright (c) 2018 by Swiss Seismological Service (SED, ETHZ)
#
# REVISIONS and CHANGES
#    2018/01/24   V1.0   Daniel Armbruster (damb)
#
# ============================================================================
"""
`SQLAlchemy <https://www.sqlalchemy.org/>`_ custom type facilities.
"""

from sqlalchemy.types import TypeDecorator, VARCHAR
import json


class JSONEncodedDict(TypeDecorator):
    """
    Representation of a :code:`dict` as a JSON encoded string.
    """

    impl = VARCHAR

    def process_bind_param(self, value, dialect):
        if value is not None:
            value = json.dumps(value)
        return value

    def process_result_value(self, value, dialect):
        if value is not None:
            value = json.loads(value)
        return value

# class JSONEncodedDict


# ----- END OF type.py -----
