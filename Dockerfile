FROM tiangolo/uvicorn-gunicorn-fastapi:latest
COPY ./app /app
RUN pip install fastapi
RUN pip install pymongo
# RUN pip install bson
# RUN pip install pydantic
# RUN pip install passlib
# RUN pip install python-jose[cryptography]
