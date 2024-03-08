

        # --Add new purchase:
        # data = {
        #     "telegram_user_id": user.id,
        #     "telegram_id": 129727111,
        #     "name": "Сыр222",
        #     "description": "",
        #     "list": 1
        # }
        # csrf_token = django_auth.session.cookies["csrftoken"]
        # response = django_auth.session.post(url=f"{django_address}/purchases/add/?list_id=1",
        #                                     data=data, headers={'X-CSRFToken': csrf_token})
        # print(response.json()["id"])

        # --Delete added purchase:
        # csrf_token = django_auth.session.cookies["csrftoken"]
        # url = f"{django_address}/purchases/{response.json()['id']}/?list_id=1"
        # headers = {'X-CSRFToken': csrf_token}
        # response = django_auth.session.delete(url=url, data=data, headers=headers)
