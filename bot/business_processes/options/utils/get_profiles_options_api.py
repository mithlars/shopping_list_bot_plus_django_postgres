from typing import Dict, Any

from bot.api.django_auth import update_last_request_time, django_auth
from bot.constants import django_address


@update_last_request_time(django_auth)
async def get_profiles_options_api(telegram_user_id: int) -> Dict[str, Any]:
    url = f"{django_address}/profiles/options/"
    data = {"telegram_user_id": telegram_user_id}
    response = django_auth.session.get(url=url, data=data)
    return response.json()
