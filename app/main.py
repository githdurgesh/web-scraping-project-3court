from fastapi import FastAPI

from app.routes.case_routes import router as case_router


app = FastAPI(
    title="Gujarat High Court Case Scraper API",
    description="Gujarat High Court Case Status and Litigant Scraper with Captcha Solving",
    version="1.0.0",
)


app.include_router(case_router)