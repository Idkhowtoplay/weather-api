from flask import Flask, jsonify
from dotenv import load_dotenv
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import requests
import json
import os
import redis

app = Flask(__name__)

load_dotenv() #load env file
API_KEY = os.getenv("API_KEY") # get api key from env

try:
    r = redis.Redis(
        host=os.getenv("host"),
        port=os.getenv("port"),
        decode_responses=os.getenv("decode_response")
    )
    r.ping()
    print("Connected to Redis successfully")
except redis.ConnectionError as e:
    print(f"Could not connect to Redis: {e}")

limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["200 per day", "50 per hour"],
)

@app.route('/weather/<locate>')
@limiter.limit("10 per hour")
def get_weather(locate):
    cache_key = f"{locate.lower()}"
    cached_weather = r.get(cache_key)
    
    if cached_weather:
        status = "Using cached data from Redis"
        print(status)
        response = json.loads(cached_weather)
        return jsonify(response)
    else:
        response = requests.get(f"https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline/{locate}/?key={API_KEY}")
        if response.status_code == 200:
            data = json.loads(response.text)
            r.setex(cache_key, 3600, json.dumps(data)) # store response to redis
            return jsonify(data)
        else:
            return jsonify({"Error": response.status_code})

if __name__ == '__main__':
    app.run(debug=True)
