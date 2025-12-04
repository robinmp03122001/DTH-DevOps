# 1. Base Image
FROM python:3.9-slim

# 2. Set Working Directory
WORKDIR /app

# 3. Install Dependencies
RUN pip install flask prometheus-client

# 4. Copy Code
COPY dth_manager.py .

# 5. Expose Port
EXPOSE 5000

# 6. Run Command
CMD ["python", "dth_manager.py"]
