from jwt import decode

from . import config


def decode_authorization_header(request):
    token = request.headers.get("Authorization")

    if token is None:
        return None

    if not token.startswith("Bearer "):
        return None

    # Chop off the 'Bearer ' bit
    token = token[7:]

    return decode(token,
                  config.JWT_SECRET_KEY,
                  algorithms=["HS256"],
                  issuer=config.JWT_ISSUER,
                  audience=config.JWT_AUDIENCE,
                  options={
                      "require_exp": True,
                      "verify_iss": True,
                      "verify_aud": True,
                      "verify_exp": True,
                  })
