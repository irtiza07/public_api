from fastapi import FastAPI
from apps.debugger_app.routes import router as debug_router
from apps.flight_tracker.routes import router as flight_tracker_router
from apps.sql_query_builder.routes import router as sql_query_builder_router
from apps.langchain_stream.routes import router as langchain_stream_router
from apps.twilio_restaurants.routes import router as twilio_restaurants_router
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,  # if you need to send cookies or HTTP auth
    allow_methods=["*"],  # e.g. ["GET", "POST"] for specific methods
    allow_headers=["*"],  # e.g. ["Content-Type", "Authorization"] for specific headers
)

# Include the routers for each app
app.include_router(debug_router, prefix="/debugger_app", tags=["debugger_app"])
app.include_router(
    flight_tracker_router, prefix="/flight_tracker", tags=["flight_tracker"]
)
app.include_router(
    sql_query_builder_router, prefix="/sql_query_builder", tags=["sql_query_builder"]
)
app.include_router(
    sql_query_builder_router, prefix="/sql_query_builder", tags=["sql_query_builder"]
)
app.include_router(
    twilio_restaurants_router, prefix="/twilio_restaurants", tags=["twilio_restaurants"]
)
app.include_router(
    langchain_stream_router,
    prefix="/langchain_stream_router",
    tags=["langchain_stream_router"],
)
