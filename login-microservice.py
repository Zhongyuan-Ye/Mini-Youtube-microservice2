from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
import databases
import sqlalchemy
import boto3
import uuid
from starlette.middleware.sessions import SessionMiddleware





# Database configuration
DATABASE_URL = "sqlite:///./test.db"
database = databases.Database(DATABASE_URL)
metadata = sqlalchemy.MetaData()
customers = sqlalchemy.Table(
    "customers",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True),
    sqlalchemy.Column("email", sqlalchemy.String, unique=True),
    sqlalchemy.Column("verified", sqlalchemy.Boolean),
    sqlalchemy.Column("verification_code", sqlalchemy.String),
)

engine = sqlalchemy.create_engine(DATABASE_URL)
metadata.create_all(engine)

# AWS SNS client
sns_client = boto3.client('sns', region_name='us-east-2')

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key="secret-key")
class RegisterRequest(BaseModel):
    email: str

class LoginRequest(BaseModel):
    email: str

class VerificationRequest(BaseModel):
    email: str
    code: str
class UserBase(BaseModel):
    email: str

async def startup_event():
    await database.connect()
app.add_event_handler("startup", startup_event)

async def shutdown_event():
    await database.disconnect()
app.add_event_handler("shutdown", shutdown_event)





async def subscribe_email_to_sns(email):
    sns_client.subscribe(
        TopicArn='arn:aws:sns:us-east-2:318036681689:microservice-login',
        Protocol='email',
        Endpoint=email
    )



async def send_verification_email(email, code):
    message = f"Your verification code is: {code}"
    response = sns_client.publish(
        TargetArn='arn:aws:sns:us-east-2:318036681689:microservice-login',
        Message=message,
        Subject='Email Verification',
    )
    return response

@app.on_event("startup")
async def startup():
    await database.connect()

@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()

@app.post("/register/")
async def register_user(request: RegisterRequest):
    query = customers.select().where(customers.c.email == request.email)
    result = await database.fetch_one(query)
    if result and result.verified:
        return {"status": "exist"}
    elif result:
        verification_code = result.verification_code
        await send_verification_email(request.email, verification_code)
        return {"status": "verification code sent"}
    else:
        await subscribe_email_to_sns(request.email)
        verification_code = str(uuid.uuid4())
        await send_verification_email(request.email, verification_code)
        query = customers.insert().values(email=request.email, verified=False, verification_code=verification_code)
        await database.execute(query)
        return {"status": "subscribtion email sent"}

@app.post("/verify/")
async def verify_user(request: VerificationRequest):
    query = customers.select().where(customers.c.email == request.email)
    user = await database.fetch_one(query)
    if user and user.verification_code == request.code:
        update_query = customers.update().where(customers.c.email == request.email).values(verified=True, verification_code=None)
        await database.execute(update_query)
        return {"status": "verified"}
    else:
        return {"status": "verification failed"}

@app.post("/login/")
async def login_user(request: LoginRequest):
    query = customers.select().where(customers.c.email == request.email)
    user = await database.fetch_one(query)
    if user:
        if user.verified:
            verification_code = str(uuid.uuid4())
            await send_verification_email(request.email, verification_code)
            update_query = customers.update().where(customers.c.email == request.email).values(verification_code=verification_code)
            await database.execute(update_query)
            return {"status": "verification email sent"}
        else:
            return {"status": "user not verified"}
    else:
        return {"status": "user not exist"}

@app.post("/verify-login/")
async def verify_login(request: VerificationRequest):
    query = customers.select().where(customers.c.email == request.email)
    user = await database.fetch_one(query)
    if user and user.verification_code == request.code:
        update_query = customers.update().where(customers.c.email == request.email).values(verification_code=None)
        await database.execute(update_query)
        return {"status": "login successful"}
    else:
        return {"status": "login failed"}


from authlib.integrations.starlette_client import OAuth

oauth = OAuth()
oauth.register(
    name='google',
    client_id="???????????????????",
    client_secret="???????????????????????",
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
    email = user.get("email")

    # Check if user exists in database
    query = customers.select().where(customers.c.email == email)
    result = await database.fetch_one(query)

    if not result:
        # Insert new user into database
        query = customers.insert().values(email=email, verified=True)
        await database.execute(query)
    
    # Handle user login or registration logic here
    return {"email": email}




if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=1024)
