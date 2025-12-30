# Use official Python image
FROM python:3.13-slim

# Set working directory
WORKDIR /app

# Copy files
COPY . .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Set environment variable for token (يمكن وضعه في Railway مباشرة)
# ENV BOT_TOKEN=your_token_here

# Run bot
CMD ["python", "bot.py"]
