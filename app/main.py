import json
import os
import time

import sentry_sdk
from sentry_sdk.integrations.asgi import SentryAsgiMiddleware

from async_spotify import SpotifyApiClient
from async_spotify.authentification import SpotifyAuthorisationToken
from async_spotify.authentification.authorization_flows import \
    AuthorizationCodeFlow
from async_spotify.spotify_errors import TokenExpired

from authlib.integrations.base_client.errors import MismatchingStateError
from authlib.integrations.starlette_client import OAuth

from fastapi import FastAPI, HTTPException, Request, Response, status, Depends
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

from app.models import *

os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

# from .routers import trump, jokes

# load config
with open("config.json", "r") as f:
    config = json.load(f)

app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)
app.base_url = config.get("base_url")

app.add_middleware(SessionMiddleware, secret_key=config["secret_key"])
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

oauth = OAuth()
oauth.register(
    name="spotify",
    client_id=config["spotify_client_id"],
    client_secret=config["spotify_client_secret"],
    access_token_url="https://accounts.spotify.com/api/token",
    access_token_params=None,
    authorize_url="https://accounts.spotify.com/authorize",
    authorize_params=None,
    api_base_url="https://api.spotify.com/v1/",
    client_kwargs={"scope": "user-read-private user-read-recently-played user-top-read user-library-read"}
)

auth_flow = AuthorizationCodeFlow(
    application_id=config["spotify_client_id"],
    application_secret=config["spotify_client_secret"],
    scopes=["user-read-private", "user-read-recently-played", "user-top-read", "user-library-read"],
    redirect_url="placeholder",
)

spotify = SpotifyApiClient(auth_flow)

# for router_module in (trump, jokes):
#     app.include_router(router_module.router)

if sentry_dsn := config.get("sentry_dsn"):
    sentry_sdk.init(
        dsn=sentry_dsn,
        traces_sample_rate=1.0,
        send_default_pii=True
    )
    app.add_middleware(SentryAsgiMiddleware)

async def get_auth_token(request: Request):
    try:
        return SpotifyAuthorisationToken(*request.session["SPOTIFY_AUTH_TOKEN"])
    except KeyError:
        raise SpotifyNotAuthorizedError

@app.on_event("startup")
async def startup():
    await spotify.create_new_client()

@app.on_event("shutdown")
async def shutdown():
    await spotify.close_client()

@app.exception_handler(TokenExpired)
async def token_expired(request: Request, exc: TokenExpired):
    try:
        auth_token = await spotify.refresh_token(auth_token=SpotifyAuthorisationToken(*request.session["SPOTIFY_AUTH_TOKEN"]))
        request.session["SPOTIFY_AUTH_TOKEN"] = tuple(auth_token)
    except:
        url = app.url_path_for("login_via_spotify")
    else:
        url = request.url
    return RedirectResponse(url=url)

@app.exception_handler(SpotifyNotAuthorizedError)
async def spotify_not_authorized(request: Request, exc: SpotifyNotAuthorizedError):
    return RedirectResponse(url=app.url_path_for("login_via_spotify"))

@app.get("/")
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/login")
async def login_via_spotify(request: Request) -> RedirectResponse:
    if app.base_url:
        redirect_uri = app.base_url + "/callback"
    else:
        redirect_uri = request.url_for("auth_via_spotify")
    return await oauth.spotify.authorize_redirect(request, redirect_uri)

@app.get("/callback")
async def auth_via_spotify(request: Request) -> RedirectResponse:
    """Uses newly-received token to finalize OAuth2 cred flow"""
    try:
        request.session["SPOTIFY_OAUTH2"] = state = await oauth.spotify.authorize_access_token(request)
        request.session["SPOTIFY_AUTH_TOKEN"] = [state["refresh_token"], int(time.time()), state["access_token"]]
    except MismatchingStateError:
        return RedirectResponse(url=app.url_path_for("login_via_spotify"))
    else:
        return RedirectResponse(url=app.url_path_for("index"))

@app.get("/top/tracks")
async def top_tracks(request: Request, count: int = 50, auth_token: SpotifyAuthorisationToken = Depends(get_auth_token)):
    """Returns the user's top tracks"""
    tracks = await spotify.personalization.get_top(content_type="tracks", auth_token=auth_token, limit=count)
    return templates.TemplateResponse("top-tracks.html", {"request": request, "tracks": enumerate(tracks["items"], start=1)})

@app.get("/top/artists")
async def top_artists(request: Request, count: int = 50, auth_token: SpotifyAuthorisationToken = Depends(get_auth_token)):
    """Returns the user's top artists"""
    artists = await spotify.personalization.get_top(content_type="artists", auth_token=auth_token, limit=count)
    return templates.TemplateResponse("top-artists.html", {"request": request, "artists": enumerate(artists["items"], start=1)})

@app.get("/recommendations")
async def recommendations(request: Request, count: int = 50, auth_token: SpotifyAuthorisationToken = Depends(get_auth_token)):
    """Gets recommendations for the user based on top songs and artists"""
    seed_tracks = ",".join(x["id"] for x in (await spotify.personalization.get_top(content_type="tracks", auth_token=auth_token, limit=5))["items"])
    if seed_tracks:
        recommendations = await spotify.browse.get_recommendation_by_seed(auth_token=auth_token, seed_tracks=seed_tracks, limit=count)
    else:
        recommendations = {"tracks": []}
    return templates.TemplateResponse("recommendations.html", {"request": request, "recommendations": recommendations["tracks"]})