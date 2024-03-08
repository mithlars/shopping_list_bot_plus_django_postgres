from bot.api.django_auth import django_auth, update_last_request_time
from bot.constants import django_address


@update_last_request_time(django_auth)
async def get_lists_detail_api(telegram_user_id: int, list_id: str = None) -> str:
    """ requests from Django details of users current list for the message """
    url = f"{django_address}/lists/detail/"
    data = {
        "telegram_user_id": telegram_user_id,
        "list_id": list_id
    }
    response = django_auth.session.get(url=url, data=data)
    list_text = response.json()['name']
    list_description = response.json().get('description', "")
    if list_description != "" and list_description is not None:
        list_text += f" ({list_description})"
    return list_text
