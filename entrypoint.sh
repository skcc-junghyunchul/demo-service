run() {
    uvicorn app.api:app --host "0.0.0.0" --port=$PORT --workers=$WORKERS --log-level=$LOG_LEVEL
}


run
