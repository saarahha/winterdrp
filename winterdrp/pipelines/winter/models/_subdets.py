"""
Models for the 'subdets' table
"""
from typing import ClassVar

from pydantic import Field
from sqlalchemy import Column, Integer, Select
from sqlalchemy.orm import Mapped, relationship

from winterdrp.pipelines.winter.models.basemodel import WinterBase
from winterdrp.processors.sqldatabase.basemodel import BaseDB, _exists
from winterdrp.utils.sql import get_engine

DEFAULT_FIELD = 999999999


class SubdetsTable(WinterBase):  # pylint: disable=too-few-public-methods
    """
    Field table in database
    """

    __tablename__ = "subdets"

    qid = Column(Integer, primary_key=True)  # serial counter
    detectorID = Column(Integer)  # WINTER detector ID
    # subdetid = Column(Integer)  # Sub-detector id (1-2)?
    nx = Column(Integer)
    nxtot = Column(Integer)
    ny = Column(Integer)
    nytot = Column(Integer)

    raw: Mapped["RawTable"] = relationship(back_populates="subdets")


class Subdets(BaseDB):
    """
    A pydantic model for a fields database entry
    """

    sql_model: ClassVar = SubdetsTable
    detectorID: int = Field(Integer, ge=0)
    # subdetid: int = Field(Integer, ge=0)
    nx: int = Field(Integer, ge=0)
    nxtot: int = Field(Integer, ge=0)
    ny: int = Field(Integer, ge=0)
    nytot: int = Field(Integer, ge=0)


def populate_subdets(ndetectors: int = 6, nxtot: int = 1, nytot: int = 2):
    """
    Creates entries in the database based on number of detectors and splits

    """

    engine = get_engine(db_name=SubdetsTable.db_name)
    if not _exists(Select(SubdetsTable), engine=engine):
        for ndetector in range(ndetectors):
            for nx in range(nxtot):
                for ny in range(nytot):
                    new = Subdets(
                        detectorID=ndetector,
                        nx=nx + 1,
                        ny=ny + 1,
                        nxtot=nxtot,
                        nytot=nytot,
                    )

                    if not new.sql_model().exists(
                        values=[nx, nxtot, ny, nytot],
                        keys=["nx", "nxtot", "ny", "nytot"],
                    ):
                        new.insert_entry()