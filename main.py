from fastapi import FastAPI, HTTPException, Depends, Form, UploadFile
from fastapi.responses import HTMLResponse
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from passlib.hash import bcrypt
from datetime import datetime, timedelta  # Import timedelta
import minio
import os
from fastapi.templating import Jinja2Templates
from fastapi.requests import Request
from fastapi.staticfiles import StaticFiles

# Database setup
DATABASE_URL = "mysql+pymysql://smv:password@localhost/instafake"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# MinIO setup
MINIO_CLIENT = minio.Minio(
    "192.168.118.209:9000",
    access_key="minioadmin",
    secret_key="minioadmin",
    secure=False
)

# Models
class User(Base):
    __tablename__ = "user"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(255), unique=True, nullable=False)
    password = Column(String(255), nullable=False)

class Post(Base):
    __tablename__ = "post"
    post_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    post_datetime = Column(DateTime, default=datetime.utcnow)
    post_caption = Column(Text)

Base.metadata.create_all(bind=engine)

# FastAPI app
app = FastAPI()

# Template setup
templates = Jinja2Templates(directory="templates")

# Mount the static directory
app.mount("/static", StaticFiles(directory="static"), name="static")

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Routes
@app.get("/", response_class=HTMLResponse)
def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/register")
def register(username: str = Form(...), password: str = Form(...), db: SessionLocal = Depends(get_db)):
    hashed_password = bcrypt.hash(password)
    user = User(username=username, password=hashed_password)
    db.add(user)
    db.commit()
    db.refresh(user)
    # Create MinIO bucket for the user using the username
    bucket_name = username.lower()  # Ensure bucket name is lowercase
    if not MINIO_CLIENT.bucket_exists(bucket_name):
        MINIO_CLIENT.make_bucket(bucket_name)
    return {"message": "User registered successfully"}

@app.post("/login")
def login(username: str = Form(...), password: str = Form(...), db: SessionLocal = Depends(get_db)):
    user = db.query(User).filter(User.username == username).first()
    if not user or not bcrypt.verify(password, user.password):
        raise HTTPException(status_code=400, detail="Invalid credentials")
    return {"message": "Login successful", "user_id": user.id}

@app.get("/feed")
def get_feed(user_id: str, db: SessionLocal = Depends(get_db)):
    posts = db.query(Post).order_by(Post.post_datetime.desc()).limit(5).all()

    array = []

    for post in posts:
        name = db.query(User).filter(User.id == post.user_id).first().username.lower()
        array.append({
            "post_id": post.post_id,
            "user_id": post.user_id,
            "username": name,
            "caption": post.post_caption,
            "datetime": post.post_datetime,
            "image_url": MINIO_CLIENT.presigned_get_object(
                bucket_name=name,
                object_name=f"{post.post_id}.jpg",
                expires=timedelta(seconds=3600)  # Use timedelta for expiration
            ),
        })

    return array

@app.post("/upload")
def upload_post(user_id: str = Form(...), caption: str = Form(...), file: UploadFile = None, db: SessionLocal = Depends(get_db)):
    if not file or file.content_type != "image/jpeg":
        raise HTTPException(status_code=400, detail="Only JPG files are allowed")
    
    # Query user by username (user_id is actually the username)
    user = db.query(User).filter(User.username == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Ensure the bucket exists
    bucket_name = user_id.lower()  # Use username as bucket name
    if not MINIO_CLIENT.bucket_exists(bucket_name):
        MINIO_CLIENT.make_bucket(bucket_name)
    
    # Save post in database
    post = Post(user_id=user.id, post_caption=caption)
    db.add(post)
    db.commit()
    db.refresh(post)
    
    # Save file in MinIO
    file_name = f"{post.post_id}.jpg"
    MINIO_CLIENT.put_object(bucket_name, file_name, file.file, length=-1, part_size=10*1024*1024)
    return {"message": "Post uploaded successfully"}
