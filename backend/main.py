from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
import jwt
import requests
from jwt.algorithms import RSAAlgorithm
from decouple import config

# Keycloak config
KEYCLOAK_CLIENT_ID = config("KEYCLOAK_CLIENT_ID")
KEYCLOAK_URL = str(config("KEYCLOAK_URL"))
ISSUER_URL = str(config("ISSUER_URL"))
JWKS_URL = f"{KEYCLOAK_URL}/protocol/openid-connect/certs"
ALGORITHMS = ["RS256"]

origins = [
    str(config("ORIGINS")),
]

app = FastAPI()
security = HTTPBearer()

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,              # или ["*"] — разрешить всё (не рекомендуется на проде)
    allow_credentials=True,
    allow_methods=["*"],                # разрешить GET, POST, PUT, DELETE, OPTIONS, * и т.д.
    allow_headers=["*"],                # разрешить все заголовки, включая Authorization
)

# Получаем JWKS
_jwks_cache = None

def get_jwks():
    global _jwks_cache
    if _jwks_cache is None:
        response = requests.get(JWKS_URL)
        response.raise_for_status()
        _jwks_cache = response.json()["keys"]
    return _jwks_cache


def get_public_key(token: str):
    unverified_header = jwt.get_unverified_header(token)
    kid = unverified_header.get("kid")
    if not kid:
        raise HTTPException(status_code=401, detail="Missing 'kid' in token header")

    key = next((k for k in get_jwks() if k["kid"] == kid), None)
    if not key:
        raise HTTPException(status_code=401, detail="Public key not found")

    return RSAAlgorithm.from_jwk(key)

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    try:
        public_key = get_public_key(token)
        payload = jwt.decode(
            token,
            public_key,
            algorithms=ALGORITHMS,
            # audience=KEYCLOAK_CLIENT_ID,
            issuer=ISSUER_URL,
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired.")
    except jwt.InvalidTokenError as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")

@app.get("/reports")
def report(user=Depends(verify_token)):
    return {
        "message": f"Hello, {user.get('preferred_username', 'unknown user')}!",
        "report": "Here is your report"
        }

