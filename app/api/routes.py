from fastapi import APIRouter, Request, Form, HTTPException, Depends
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
import string, random
from urllib.parse import urlparse
from app.database import get_db
from app.models.models import URL

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

def generate_code(length=6):
    code = ''.join(random.choices(string.ascii_letters + string.digits, k=length))
    print(f"📝 Generated short code: {code}")
    return code

@router.get("/", response_class=HTMLResponse)
def homepage(request: Request):
    print("🏠 Serving homepage")
    return templates.TemplateResponse("index.html", {"request": request, "short_url": None})

@router.post("/shorten", response_class=HTMLResponse)
def shorten_url(
    request: Request, 
    long_url: str = Form(...), 
    db: Session = Depends(get_db)
):
    print(f"📨 Received URL to shorten: {long_url}")
    
    # Validate URL
    try:
        print("🔍 Validating URL format")
        result = urlparse(long_url)
        if not all([result.scheme, result.netloc]):
            print("❌ Invalid URL format detected")
            raise ValueError("Invalid URL")
    except ValueError:
        print("❌ URL validation failed")
        raise HTTPException(status_code=400, detail="Invalid URL format")

    print("✅ URL validation successful")
    short_code = generate_code()
    
    # Check if short_code already exists
    print("🔄 Checking for duplicate short code")
    while db.query(URL).filter(URL.short_code == short_code).first():
        print(f"⚠️ Duplicate short code found: {short_code}")
        short_code = generate_code()
    
    # Create new URL entry in database
    print("💾 Creating new URL entry in database")
    db_url = URL(
        original_url=long_url,
        short_code=short_code
    )
    try:
        db.add(db_url)
        db.commit()
        db.refresh(db_url)
        print(f"✅ Successfully saved URL with short code: {short_code}")
    except Exception as e:
        print(f"❌ Database error: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Database error")
    
    short_url = f"http://localhost:8000/{short_code}"
    print(f"🔗 Generated short URL: {short_url}")
    return templates.TemplateResponse("index.html", {"request": request, "short_url": short_url})

@router.get("/{short_code}")
def redirect_to_original(short_code: str, db: Session = Depends(get_db)):
    print(f"🔍 Looking up short code: {short_code}")
    
    # Query the database for the URL
    url = db.query(URL).filter(URL.short_code == short_code).first()
    if url is None:
        print(f"❌ Short code not found: {short_code}")
        raise HTTPException(status_code=404, detail="URL not found")
    
    print(f"✅ Found original URL: {url.original_url}")
    # Add status_code 307 for temporary redirect
    # This preserves the HTTP method and body of the request
    return RedirectResponse(
        url=url.original_url, 
        status_code=307
    )
