"""
DB2 Request Area data model.

Translated from COBOL copybook: src/copybook/online/DB2REQ.cpy

COBOL structure: DB2-REQUEST-AREA (01 level)
  - DB2-REQUEST-TYPE: connection operation type
  - DB2-RESPONSE-CODE: operation response code
  - DB2-CONNECTION-TOKEN: connection token
  - DB2-ERROR-INFO: SQL error details
"""

from typing import Literal, Optional

from pydantic import BaseModel, Field


class DB2Request(BaseModel):
    """DB2 connection request/response area.

    Translated from COBOL copybook DB2REQ.cpy.
    Maps to DB2-REQUEST-AREA (01 level).

    Request types (88-level values):
      C = Connect, D = Disconnect, S = Status
    """

    db2_request_type: Literal["C", "D", "S"] = Field(
        ...,
        description="DB2-REQUEST-TYPE: C=Connect, D=Disconnect, S=Status - PIC X"
    )
    db2_response_code: int = Field(
        default=0,
        description="DB2-RESPONSE-CODE: Response code - PIC S9(8) COMP"
    )
    db2_connection_token: str = Field(
        default="", max_length=16,
        description="DB2-CONNECTION-TOKEN: Connection identifier - PIC X(16)"
    )

    # DB2-ERROR-INFO sub-fields
    db2_sqlcode: int = Field(
        default=0,
        description="DB2-SQLCODE: SQL return code - PIC S9(9) COMP"
    )
    db2_error_msg: str = Field(
        default="", max_length=80,
        description="DB2-ERROR-MSG: SQL error message - PIC X(80)"
    )
