from fastapi import FastAPI, Request
from authlib.integrations.starlette_client import OAuth
from fastapi.responses import RedirectResponse

app = FastAPI()

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
    redirect_uri = request.url_for('callback')
    return await oauth.google.authorize_redirect(request, redirect_uri)

@app.get('/callback/')
async def callback(request: Request):
    token = await oauth.google.authorize_access_token(request)
    user = await oauth.google.parse_id_token(request, token)
    return {"status": "successful", "email": user.get("email")}




if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=1024)