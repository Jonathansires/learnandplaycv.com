from fastapi import FastAPI, Form, Request, UploadFile, File, BackgroundTasks, HTTPException, status, Depends
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from Email_manager import Email_manager
import os
import logging
import httpx
from typing import Dict, Any, Optional

# Configure logging
logging.basicConfig(
    filename="learnandplaycv.log",  # Change path if necessary
    level=logging.INFO,  # Changed from DEBUG to INFO to reduce verbosity
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

# Suppress verbose SMTP logs
logging.getLogger('smtplib').setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

app = FastAPI()
templates = Jinja2Templates(directory="templates")
emails = ["sires_mary@yahoo.com","jonnysires@yahoo.com"]

# Initialize email manager
email_manager = Email_manager()

# reCAPTCHA Configuration
RECAPTCHA_VERIFY_URL = "https://www.google.com/recaptcha/api/siteverify"
PRODUCTION_SITE_KEY = "6Ldwt_QrAAAAAJe16NGYB5W5RLqeMibHLQu2or1r"
PRODUCTION_SECRET_KEY = "6Ldwt_QrAAAAAGUlbPlLHvG7ZUalEbA1bInb1vzD"
PRODUCTION_MIN_SCORE = 0.5

TEST_SITE_KEY = "6LeIxAcTAAAAAJcZVRqyHh71UMIEGNQ_MXjiZKhI"
TEST_SECRET_KEY = "6LeIxAcTAAAAAGG-vFI1TnRWxMZNFuojJ4WifJWe"
TEST_MIN_SCORE = 0.0

PRODUCTION_HOSTS = {"learnandplaycv.com", "www.learnandplaycv.com", "jcsires.com", "www.jcsires.com"}


def get_recaptcha_config(hostname: Optional[str]) -> Dict[str, Any]:
    """Return site key, secret key, and min score based on the incoming host."""
    normalized_host = (hostname or "").split(":")[0].lower()
    if normalized_host in PRODUCTION_HOSTS:
        return {
            "site_key": PRODUCTION_SITE_KEY,
            "secret_key": PRODUCTION_SECRET_KEY,
            "min_score": PRODUCTION_MIN_SCORE,
            "environment": "production",
        }
    return {
        "site_key": TEST_SITE_KEY,
        "secret_key": TEST_SECRET_KEY,
        "min_score": TEST_MIN_SCORE,
        "environment": "development",
    }


def get_request_context(request: Request) -> Dict[str, str]:
    """Return normalized host and client IP with proxy headers honored."""
    forwarded_host = request.headers.get("x-forwarded-host")
    host = forwarded_host or request.headers.get("host") or request.url.hostname or ""

    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        client_ip = forwarded_for.split(",")[0].strip()
    else:
        client_ip = request.client.host if request.client else ""

    return {"host": host, "client_ip": client_ip}

async def verify_recaptcha(token: str, remote_ip: str, secret_key: str, min_score: float):
    """Verify reCAPTCHA v3 token with Google."""
    if not token:
        logger.warning("No reCAPTCHA token provided")
        return False, 0.0
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                RECAPTCHA_VERIFY_URL,
                data={
                    'secret': secret_key,
                    'response': token,
                    'remoteip': remote_ip
                },
                timeout=10.0
            )
            result = response.json()
            
            success = result.get('success', False)
            score = result.get('score', 0.0)
            
            logger.info(f"reCAPTCHA verification: success={success}, score={score}")
            
            if not success or score < min_score:
                return False, score
            
            return True, score
            
    except Exception as e:
        logger.error(f"reCAPTCHA verification error: {e}", exc_info=True)
        # In case of error, allow submission (graceful degradation)
        return True, 0.0

# Directory setup
current_dir = os.path.dirname(__file__)
static_dir = os.path.join(current_dir, "static")
templates_dir = os.path.join(current_dir, "templates")
app.mount("/static", StaticFiles(directory=static_dir), name="static")
templates = Jinja2Templates(directory=templates_dir)


@app.get("/", response_class=HTMLResponse)
async def one_get(request: Request):
    """Serve the main page for GET requests."""
    context = get_request_context(request)
    recaptcha_config = get_recaptcha_config(context["host"])
    logger.info(
        f"GET request received for the main page from host {context['host']} using {recaptcha_config['environment']} keys."
    )
    return templates.TemplateResponse(
        "onepage-1.html",
        {
            "request": request,
            "recaptcha_site_key": recaptcha_config["site_key"],
        },
    )


@app.post("/", response_class=JSONResponse)
async def one_post(
    request: Request,
    background_tasks: BackgroundTasks,
    name: str = Form(...),
    email: str = Form(...),
    age: str = Form(...),
    message: str = Form(...),
    phone: str = Form(None),  # Honeypot field
    recaptcha_token: str = Form(None),  # reCAPTCHA token
):
    context = get_request_context(request)
    recaptcha_config = get_recaptcha_config(context["host"])
    logger.info(
        f"Contact form submission started from IP: {context['client_ip']} using {recaptcha_config['environment']} keys."
    )
    
    # Get client IP
    client_ip = context["client_ip"]
    
    # Verify reCAPTCHA
    if recaptcha_token:
        logger.info(f"reCAPTCHA token received: {recaptcha_token[:20]}...")
        recaptcha_valid, score = await verify_recaptcha(
            recaptcha_token,
            client_ip,
            recaptcha_config["secret_key"],
            recaptcha_config["min_score"],
        )
        if not recaptcha_valid:
            logger.warning(f"reCAPTCHA failed for IP {client_ip}, score: {score}")
            return JSONResponse(
                {"status": "error", "message": "Please verify you are human and try again."},
                status_code=status.HTTP_400_BAD_REQUEST
            )
        logger.info(f"reCAPTCHA passed for IP {client_ip} with score {score}")
    else:
        logger.warning(f"⚠️  NO reCAPTCHA token provided from IP {client_ip} - form submitted without bot protection!")
    
    # Honeypot check
    if phone:  # Honeypot field to catch bots
        logger.warning(f"Honeypot triggered by request from {client_ip}")
        return JSONResponse({"status": "error", "message": "Spam detected!"})

    try:
        email_content = email_manager.email_form(name, email, age, message)
        logger.debug("Email content created for contact form.")

        # Send to site owner(s)
        for recipient in emails:
            logger.info(f"Scheduling contact form email to {recipient}.")
            background_tasks.add_task(
                email_manager.send_email,
                recipient,
                email_content,
                "Contact Form",
                reply_to_email=email
            )

        # Auto-reply to user
        logger.info(f"Scheduling auto-reply to form submitter: {email}")
        background_tasks.add_task(
            email_manager.auto_reply_to_form_submitter,
            email,
            name
        )

        return JSONResponse({"status": "success", "message": "Form has been successfully submitted"})
    
    except Exception as e:
        logger.error(f"Error in contact form submission: {e}", exc_info=True)
        return JSONResponse({"status": "error", "message": f"An error occurred: {e}"})

@app.get("/careers", response_class=HTMLResponse)
async def careers_get(request: Request):
    """Serve the careers page for GET requests."""
    context = get_request_context(request)
    recaptcha_config = get_recaptcha_config(context["host"])
    logger.info(
        f"GET request received for the careers page from host {context['host']} using {recaptcha_config['environment']} keys."
    )
    return templates.TemplateResponse(
        "careers.html",
        {
            "request": request,
            "recaptcha_site_key": recaptcha_config["site_key"],
        },
    )

@app.post("/careers", response_class=JSONResponse)
async def careers_post(
    request: Request,
    background_tasks: BackgroundTasks,
    first_name: str = Form(...),
    last_name: str = Form(...),
    phone: str = Form(...),
    email2: str = Form(...),
    location: str = Form(...),
    experience: str = Form(...),
    position: str = Form(...),
    resume: UploadFile = File(...),
    additional_info: str = Form(None),
    recaptcha_token: str = Form(None),  # reCAPTCHA token
):
    context = get_request_context(request)
    recaptcha_config = get_recaptcha_config(context["host"])
    logger.info(
        f"Careers form submission started from IP: {context['client_ip']} using {recaptcha_config['environment']} keys."
    )
    
    # Get client IP
    client_ip = context["client_ip"]
    
    # Verify reCAPTCHA
    if recaptcha_token:
        logger.info(f"reCAPTCHA token received: {recaptcha_token[:20]}...")
        recaptcha_valid, score = await verify_recaptcha(
            recaptcha_token,
            client_ip,
            recaptcha_config["secret_key"],
            recaptcha_config["min_score"],
        )
        if not recaptcha_valid:
            logger.warning(f"reCAPTCHA failed for IP {client_ip}, score: {score}")
            return JSONResponse(
                {"status": "error", "message": "Please verify you are human and try again."},
                status_code=status.HTTP_400_BAD_REQUEST
            )
        logger.info(f"reCAPTCHA passed for IP {client_ip} with score {score}")
    else:
        logger.warning(f"⚠️  NO reCAPTCHA token provided from IP {client_ip} - careers form submitted without bot protection!")
    
    # Honeypot check
    form_data = await request.form()
    honeypot = form_data.get("email")
    if honeypot:
        logger.warning(f"Honeypot triggered by request from {client_ip}")
        return JSONResponse(
            {"status": "error", "message": "Spam detected!"},
            status_code=status.HTTP_400_BAD_REQUEST
        )

    try:
        file_data = await resume.read()
        file_name = resume.filename
        logger.info(f"Received file {file_name}.")

        email_content = email_manager.email_resume(
            first_name, last_name, email2, phone, location,
            experience, position, additional_info
        )
        logger.debug("Email content created for careers form.")

        for recipient in emails:
            logger.info(f"Scheduling email to {recipient} with attachment {file_name}.")
            background_tasks.add_task(
                email_manager.send_email,
                recipient,
                email_content,
                "Careers",
                reply_to_email=email2,  # Candidate's email for reply header
                file_data=file_data,
                file_name=file_name
            )


        logger.info(f"Scheduling auto-reply to resume submitter: {email2}")
        background_tasks.add_task(
            email_manager.auto_reply_to_resume_submitter,
            email2,
            first_name
        )

        return JSONResponse({"status": "success", "message": "Form has been successfully submitted"})
    except Exception as e:
        logger.error(f"Error in careers_post: {e}", exc_info=True)
        return JSONResponse(
            {"status": "error", "message": f"Form submission server error: {e}"}
        )


@app.get("/team", response_class=HTMLResponse)
async def team(request: Request):
    """Serve the team page."""
    logger.info("GET request received for the team page.")
    return templates.TemplateResponse("team.html", {"request": request})


@app.exception_handler(404)
async def custom_404_handler(request: Request, exc):
    """Custom 404 error handler."""
    logger.warning(f"404 error: {request.url}")
    return templates.TemplateResponse("404.html", {"request": request}, status_code=404)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)