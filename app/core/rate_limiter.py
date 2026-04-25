from fastapi import Request

async def user_identifier(request: Request):
    auth = request.headers.get("authorization")

    if auth:
        return auth

    return request.client.host