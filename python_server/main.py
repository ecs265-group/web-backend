import uvicorn
from fastapi import FastAPI, HTTPException, Depends, Request, status, UploadFile, File
from pymongo import MongoClient
from auth import get_current_user, create_access_token, Hash, User
from fastapi.security import OAuth2PasswordRequestForm
from boto3 import client
import os
from dotenv import load_dotenv
load_dotenv()

app = FastAPI()
from fastapi.middleware.cors import CORSMiddleware
origins = [
    "*",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

mongo_client = MongoClient("mongodb://mongodb:27017/")
db = mongo_client["user_auth"]

s3 = client('s3',
            aws_access_key_id = os.getenv('ACCESS_KEY'),
            aws_secret_access_key = os.getenv('SECRET_KEY'),
            )

bucketName = "shyamv-dds-project"


@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.post('/register')
def create_user(request:User):
   hashed_pass = Hash.bcrypt(request.password)
   user_object = dict(request)
   user_object["password"] = hashed_pass
   db["users"].insert_one(user_object)
   return {"res":"created"}


@app.post('/login')
def login(request:OAuth2PasswordRequestForm = Depends()):
    user = db["users"].find_one({"username":request.username})
    if not user:
       raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    if not Hash.verify(user["password"],request.password):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    access_token = create_access_token(data={"sub": user["username"] })
    return {"access_token": access_token, "token_type": "bearer"}


@app.post("/upload_pdf")
def upload_pdf(file: UploadFile = File(...)):
    try:
        pdf = file.file.read()
        file.file.seek(0)
        s3.upload_fileobj(file.file, bucketName, file.filename)
        message = f"{file.filename} uploaded to {bucketName} successfully!"
    except Exception as e:
        message = e.args
    finally:
        file.file.close()
    return {"message": message}



if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)