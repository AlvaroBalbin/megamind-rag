# simple image for the FastAPI service, slim is fast and small
FROM python:3.11-slim 

WORKDIR / app

# image build 
RUN apt-get update && apt-get install -y --no-install-recommends build-essential \
    build-essential \
    # clear cache, its only useful to build new packages later but image doesnt need it extra space
    # can be rebuilt using apt-get update
    && rm -rf /var/lib/lists/*

    # put the source into destination ie working directory /app
    # do requirements.txt before megamind-rag so any change there doesnt make us rerun download everytime
    COPY requirements.txt . 
    # --no-cache-dir keeps file small cause it doesnt keep pip caches
    RUN pip install --no-cache-dir -r requirements.txt

    # store in app/example -> example can be megamind-rag
    COPY megamind-rag ./megamind-rag 
    COPY api ./api
    COPY data ./data

    # add /app to the python path so python can find it
    ENV PYTHONPATH = /app

    # network that this container will listen to
    EXPOSE 8000

    # tempted to use uv cause its so fast but its outside the scope of my expertise atm
    CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]



