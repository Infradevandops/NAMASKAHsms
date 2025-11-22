#!/usr/bin/env python3
"""Minimal test server for frontend testing"""

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import uvicorn

app = FastAPI(title="Namaskah Test Server")

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", response_class=HTMLResponse)
async def home():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Namaskah SMS - Test Server</title>
        <link rel="stylesheet" href="/static/css/style.css">
    </head>
    <body>
        <h1>🚀 Namaskah SMS Platform</h1>
        <p>✅ Test server running</p>
        <nav>
            <a href="/auth/login">Login</a> |
            <a href="/dashboard">Dashboard</a> |
            <a href="/verify">Verify</a>
        </nav>
    </body>
    </html>
    """

@app.get("/auth/login", response_class=HTMLResponse)
async def login():
    return """
    <!DOCTYPE html>
    <html>
    <head><title>Login - Namaskah</title></head>
    <body>
        <h2>Login</h2>
        <form>
            <input type="email" placeholder="Email" required>
            <input type="password" placeholder="Password" required>
            <button type="submit">Login</button>
        </form>
    </body>
    </html>
    """

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard():
    return """
    <!DOCTYPE html>
    <html>
    <head><title>Dashboard - Namaskah</title></head>
    <body>
        <h2>Dashboard</h2>
        <p>Balance: $10.00</p>
        <p>Verifications: 5</p>
    </body>
    </html>
    """

@app.get("/verify", response_class=HTMLResponse)
async def verify():
    return """
    <!DOCTYPE html>
    <html>
    <head><title>Verify - Namaskah</title></head>
    <body>
        <h2>SMS Verification</h2>
        <select><option>Select Country</option></select>
        <select><option>Select Service</option></select>
        <button>Get Number</button>
    </body>
    </html>
    """

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)