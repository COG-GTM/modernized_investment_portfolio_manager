"""
Online Inquiry Communication Area data model.

Translated from COBOL copybook: src/copybook/online/INQCOM.cpy

COBOL structure: INQCOM-AREA (01 level)
  - INQCOM-FUNCTION: inquiry function code
  - INQCOM-ACCOUNT-NO: account number
  - INQCOM-RESPONSE-CODE: response code
  - INQCOM-ERROR-MSG: error message
"""

from typing import Literal, Optional

from pydantic import BaseModel, Field


class InquiryCommon(BaseModel):
    """Online inquiry request/response communication area.

    Translated from COBOL copybook INQCOM.cpy.
    Maps to INQCOM-AREA (01 level).

    Functions (88-level values):
      MENU = Main menu, INQP = Portfolio inquiry,
      INQH = History inquiry, EXIT = Exit
    """

    inqcom_function: Literal["MENU", "INQP", "INQH", "EXIT"] = Field(
        default="MENU",
        description="INQCOM-FUNCTION: MENU/INQP/INQH/EXIT - PIC X(4)"
    )
    inqcom_account_no: str = Field(
        default="", max_length=10,
        description="INQCOM-ACCOUNT-NO: Account number - PIC X(10)"
    )
    inqcom_response_code: int = Field(
        default=0,
        description="INQCOM-RESPONSE-CODE: Response code - PIC S9(8) COMP"
    )
    inqcom_error_msg: str = Field(
        default="", max_length=80,
        description="INQCOM-ERROR-MSG: Error message - PIC X(80)"
    )
