from django.conf import settings
from enum import StrEnum

MEMBERSHIP_TYPE_2_PLAN_ID_STRIPE = {
    "MEMBERSHIP_TYPE_BASIC_MONTHLY": settings.MEMBERSHIP_TYPE_BASIC_MONTHLY,
    "MEMBERSHIP_TYPE_PRO_MONTHLY": settings.MEMBERSHIP_TYPE_PRO_MONTHLY,
}


class PLAN_ID(StrEnum):
    MEMBERSHIP_TYPE_BASIC_MONTHLY = settings.MEMBERSHIP_TYPE_BASIC_MONTHLY
    MEMBERSHIP_TYPE_PRO_MONTHLY = settings.MEMBERSHIP_TYPE_PRO_MONTHLY

    @classmethod
    def get_name_from_price_Id(cls, price_id: str) -> str:
        for name, member in cls.__members__.items():
            if member.value == price_id:
                return name
        return ""

PLAN_ID_2_CREDITS = {
    PLAN_ID.MEMBERSHIP_TYPE_BASIC_MONTHLY: 100,
    PLAN_ID.MEMBERSHIP_TYPE_PRO_MONTHLY: 1000,
}
