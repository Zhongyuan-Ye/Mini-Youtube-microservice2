
from fastapi import FastAPI, Request
from authlib.integrations.starlette_client import OAuth
from fastapi.responses import RedirectResponse
from starlette.middleware.sessions import SessionMiddleware
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Add SessionMiddleware with a secret key
app.add_middleware(SessionMiddleware, secret_key="your-very-strong-secret-key")

# Enable CORS (optional, depending on your frontend requirements)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Configure OAuth
oauth = OAuth()
oauth.register(
    name='google',
    client_id="177640167439-89pg7khuonjha41ccg4ngir2ph3nakqn.apps.googleusercontent.com",
    client_secret="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",
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={
        'scope': 'openid email profile'
    }
)

@app.get('/authenticate/')
async def authenticate(request: Request):
    # Ensure the redirect_uri is consistent and correctly configured
    redirect_uri = request.url_for('callback', _external=True)
    return await oauth.google.authorize_redirect(request, redirect_uri)

@app.get('/callback/')
async def callback(request: Request):
    # Handling the response from Google
    token = await oauth.google.authorize_access_token(request)
    user = await oauth.google.parse_id_token(request, token)
    return {"status": "successful", "email": user.get("email")}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=1024)
