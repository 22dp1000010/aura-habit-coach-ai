# Entry point for Vercel Serverless Functions
import sys
import os

# Add root and backend directories to sys.path so Vercel can resolve relative imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.main import app
