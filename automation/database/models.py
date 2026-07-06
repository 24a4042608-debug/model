import os
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Numeric, DateTime, JSON, Float, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from dotenv import load_dotenv

load_dotenv()

Base = declarative_base()

class RawProduct(Base):
    __tablename__ = "shop_products"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(String(100), unique=True, nullable=False)
    title = Column(Text, nullable=False)
    description = Column(Text)
    price = Column(Numeric(12, 2))
    price_text = Column(String(255))  # Original price display (e.g. "₫69.000 - ₫125.000")
    brand = Column(String(100))
    category = Column(Text)  # Category breadcrumb (e.g. "Thời Trang Nữ > Áo > Áo hai dây và ba lỗ")
    details_json = Column(Text)  # Structured product details as JSON string
    images = Column(JSON) # JSON format for image lists
    video = Column(Text)
    url = Column(Text)
    rating_star = Column(Float, nullable=True)
    sold_count = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class SeoProduct(Base):
    __tablename__ = "seo_products"
    
    product_id = Column(String(100), primary_key=True, nullable=False)
    seo_title = Column(String(255))
    meta_description = Column(Text)
    slug = Column(String(255))
    main_keyword = Column(String(255))
    secondary_keywords = Column(JSON) # List of keywords
    usp = Column(JSON) # List of unique selling points
    target_customer = Column(Text)
    search_intent = Column(Text)
    seo_score = Column(Integer)
    analysis = Column(JSON) # Dictionary feedback
    created_at = Column(DateTime, default=datetime.utcnow)

class FacebookPost(Base):
    __tablename__ = "facebook_posts"
    
    product_id = Column(String(100), primary_key=True, nullable=False)
    caption = Column(Text)
    hashtags = Column(JSON) # List of hashtags
    status = Column(String(50), default="Pending") # Pending, Publishing, Posted, Failed
    retry = Column(Integer, default=0)
    posted_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class Product(Base):
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    keyword = Column(String(255), nullable=False)
    title = Column(Text, nullable=False)
    price_text = Column(String(100))
    price_val = Column(Numeric(15, 2))
    rating_star = Column(Float)
    sold_count = Column(Integer)
    image_url = Column(Text)
    local_image_path = Column(Text)
    seo_keywords = Column(Text)
    seo_description = Column(Text)
    product_url = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

# Configuration & Connection Setup
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "3306")
DB_USER = os.getenv("DB_USER", "root")
DB_PASS = os.getenv("DB_PASS", "")
DB_NAME = os.getenv("DB_NAME", "shopee_db")

DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Automatic Database Creator Helper
def init_db():
    try:
        # Connect to MySQL server without selecting database first
        sys_url = f"mysql+pymysql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/"
        sys_engine = create_engine(sys_url)
        from sqlalchemy import text
        with sys_engine.connect() as conn:
            conn.execute(text(f"CREATE DATABASE IF NOT EXISTS {DB_NAME} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"))
            conn.commit()
        sys_engine.dispose()
        
        # Now connect to selected DB and create tables
        engine = create_engine(DATABASE_URL)
        Base.metadata.create_all(engine)
        return engine
    except Exception as e:
        print(f"Error initializing MySQL database: {e}")
        # Fallback to sqlite if MySQL is offline during initial test
        fallback_url = "sqlite:///fallback_db.sqlite"
        print(f"Falling back to local SQLite: {fallback_url}")
        engine = create_engine(fallback_url)
        Base.metadata.create_all(engine)
        return engine

class TrainingDataset(Base):
    __tablename__ = "training_dataset"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(String(100), nullable=False)
    date = Column(String(50), nullable=False) # Format: YYYY-MM-DD
    ctr = Column(Numeric(12, 4), nullable=False)
    cvr = Column(Numeric(12, 4), nullable=False)
    cpc = Column(Numeric(12, 2), nullable=False)
    cpa = Column(Numeric(12, 2), nullable=False)
    roas = Column(Numeric(12, 4), nullable=False)
    refund = Column(Numeric(12, 4), nullable=False)
    gmv = Column(Numeric(12, 2), nullable=False)
    profit = Column(Numeric(12, 2), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class MLModel(Base):
    __tablename__ = "models"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(String(100), nullable=False)
    algorithm = Column(String(100), nullable=False)
    version = Column(String(50), nullable=False)
    accuracy = Column(Numeric(12, 4))
    dataset_size = Column(Integer)
    model_path = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

class MLPrediction(Base):
    __tablename__ = "predictions"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(String(100), nullable=False)
    input_json = Column(JSON)
    output_json = Column(JSON)
    confidence = Column(Numeric(12, 2))
    created_at = Column(DateTime, default=datetime.utcnow)

engine = init_db()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
