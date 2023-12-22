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
sns_topic_arn = 'arn:aws:sns:us-east-2:318036681689:microservice-login-notifications'  

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key="secret-key")

class RegisterRequest(BaseModel):
    email: str

class VerificationRequest(BaseModel):
    email: str
    code: str

class UserBase(BaseModel):
    email: str

@app.on_event("startup")
async def startup():
    await database.connect()

@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()

async def publish_event_to_sns(event_type, email, code=None):
    message = {
        'EventType': event_type, 
        'Email': email, 
        'RecipientEmail': email  
    }
    if code:
        message['Code'] = code
    response = sns_client.publish(
        TopicArn=sns_topic_arn,
        Message=str(message),
    )
    return response

@app.post("/register/")
async def register_user(request: RegisterRequest):
    query = customers.select().where(customers.c.email == request.email)
    result = await database.fetch_one(query)
    if result and result.verified:
        return {"status": "exist"}
    elif result:
        verification_code = result.verification_code
        await publish_event_to_sns('Verification', request.email, verification_code)
        return {"status": "verification code sent"}
    else:
        verification_code = str(uuid.uuid4())
        await publish_event_to_sns('Register', request.email, verification_code)
        query = customers.insert().values(email=request.email, verified=False, verification_code=verification_code)
        await database.execute(query)
        return {"status": "subscription email sent"}

@app.post("/login/")
async def login_user(request: RegisterRequest):
    query = customers.select().where(customers.c.email == request.email)
    result = await database.fetch_one(query)
    if result:
        if result.verified:
            verification_code = str(uuid.uuid4())
            await publish_event_to_sns('Login', request.email, verification_code)
            update_query = customers.update().where(customers.c.email == request.email).values(verification_code=verification_code)
            await database.execute(update_query)
            return {"status": "verification email sent"}
        else:
            return {"status": "user not verified"}
    else:
        return {"status": "user does not exist"}

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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=1024)
