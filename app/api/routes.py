from fastapi import APIRouter, Request, Form, HTTPException, Depends
from fastapi.responses import RedirectResponse, HTMLResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
import string, random
from urllib.parse import urlparse
from datetime import datetime, timedelta
from app.database import get_db
from app.models.models import URL

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

def generate_code(length=6):
    code = ''.join(random.choices(string.ascii_letters + string.digits, k=length))
    print(f"📝 Generated short code: {code}")
    return code

# 1. Home route
@router.get("/", response_class=HTMLResponse)
def homepage(request: Request):
    print("🏠 Serving homepage")
    return templates.TemplateResponse("index.html", {"request": request, "short_url": None})

# 2. Admin route - MOVE THIS BEFORE the {short_code} route
@router.get("/admin", response_class=HTMLResponse)
def admin_dashboard(request: Request, db: Session = Depends(get_db)):
    print("👑 Accessing admin dashboard")
    urls = db.query(URL).all()
    return templates.TemplateResponse(
        "admin.html", 
        {"request": request, "urls": urls}
    )

# 3. QR code route - MOVE THIS BEFORE the {short_code} route
@router.get("/qr/{short_code}")
async def generate_qr(short_code: str):
    """Generate QR code for a short URL"""
    print(f"🔳 Generating QR code for: {short_code}")
    
    try:
        import qrcode
        from io import BytesIO
        
        # Create the QR code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        
        # Add the full URL data
        base_url = "http://localhost:8000"
        short_url = f"{base_url}/{short_code}"
        
        # Fix: Complete the add_data method call
        qr.add_data(short_url)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="white", back_color="#1e293b")
        
        # Save the image to a bytes buffer
        buf = BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)
        
        print(f"✅ QR code generated successfully for: {short_code}")
        
        # Return the image as a streaming response
        return StreamingResponse(buf, media_type="image/png")
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"❌ QR generation error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"QR Code generation failed: {str(e)}")

# 4. Shorten URL route
@router.post("/shorten", response_class=HTMLResponse)
def shorten_url(
    request: Request, 
    long_url: str = Form(...), 
    custom_code: str = Form(""),
    expiration: int = Form(0),
    one_time_use: bool = Form(False),
    db: Session = Depends(get_db)
):
    print(f"📨 Received URL to shorten: {long_url}")
    print(f"🔑 Custom code provided: '{custom_code}'")
    print(f"⏱️ Expiration hours: {expiration}")
    print(f"🔥 One-time use: {one_time_use}")
    
    # Validate URL
    try:
        print("🔍 Validating URL format")
        result = urlparse(long_url)
        if not all([result.scheme, result.netloc]):
            print("❌ Invalid URL format detected")
            raise ValueError("Invalid URL")
    except ValueError:
        print("❌ URL validation failed")
        return templates.TemplateResponse(
            "index.html", 
            {"request": request, "error": "Invalid URL format", "short_url": None}
        )

    print("✅ URL validation successful")
    
    # Handle custom code if provided
    if custom_code:
        print(f"🔑 Using custom code: {custom_code}")
        # Check if custom code already exists
        existing = db.query(URL).filter(URL.short_code == custom_code).first()
        if existing:
            print(f"❌ Custom code already exists: {custom_code}")
            return templates.TemplateResponse(
                "index.html", 
                {
                    "request": request, 
                    "error": "Custom code already in use. Please try another.", 
                    "short_url": None
                }
            )
        short_code = custom_code
        print(f"✅ Custom code available: {short_code}")
    else:
        # Generate random code
        print("🎲 Generating random code")
        short_code = generate_code()
        # Check if short_code already exists
        print("🔄 Checking for duplicate short code")
        while db.query(URL).filter(URL.short_code == short_code).first():
            print(f"⚠️ Duplicate short code found: {short_code}")
            short_code = generate_code()
    
    # Calculate expiration time if set
    expires_at = None
    if expiration > 0:
        expires_at = datetime.now() + timedelta(hours=expiration)
        print(f"⏱️ Link will expire at: {expires_at}")
    
    # Create new URL entry in database
    print("💾 Creating new URL entry in database")
    try:
        db_url = URL(
            original_url=long_url,
            short_code=short_code,
            expires_at=expires_at,
            one_time_use=one_time_use
        )
        db.add(db_url)
        db.commit()
        db.refresh(db_url)
        print(f"✅ Successfully saved URL with short code: {short_code}")
    except Exception as e:
        print(f"❌ Database error: {str(e)}")
        db.rollback()
        return templates.TemplateResponse(
            "index.html", 
            {"request": request, "error": f"Database error: {str(e)}", "short_url": None}
        )
    
    short_url = f"http://localhost:8000/{short_code}"
    print(f"🔗 Generated short URL: {short_url}")
    return templates.TemplateResponse(
        "index.html", 
        {"request": request, "short_url": short_url, "short_code": short_code}
    )

# 5. Generic short code route - THIS SHOULD BE LAST
@router.get("/{short_code}")
def redirect_to_original(request: Request, short_code: str, db: Session = Depends(get_db)):
    print(f"🔍 Looking up short code: {short_code}")
    
    # Query the database for the URL
    url = db.query(URL).filter(URL.short_code == short_code).first()
    if url is None:
        print(f"❌ Short code not found: {short_code}")
        raise HTTPException(status_code=404, detail="URL not found")
    
    # Check if URL has expired
    if url.expires_at and datetime.now() > url.expires_at:
        print(f"⏱️ Link has expired: {short_code}")
        return templates.TemplateResponse(
            "expired.html",
            {"request": request, "message": "This link has expired."}
        )
    
    # Increment click counter
    url.clicks += 1
    db.commit()
    print(f"📊 Incrementing clicks counter: {url.clicks}")
    
    # Check if one-time use
    if url.one_time_use:
        print(f"🔥 One-time use link accessed: {short_code}")
        db.delete(url)
        db.commit()
    
    print(f"✅ Found original URL: {url.original_url}")
    return RedirectResponse(
        url=url.original_url, 
        status_code=307
    )
