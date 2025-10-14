from fastapi import FastAPI

app = FastAPI()

@app.get('/bar')
def hello():
    return {"msg": "Hello from the bar microservice"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=8000)