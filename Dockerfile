# Use the official lightweight Python image.
# https://hub.docker.com/_/python
FROM python:3.9-slim

## Step 1:
# Create a working directory
ENV APP_HOME /app
WORKDIR $APP_HOME

## Step 2:
# Copy local code to the container image.

COPY app.py requirements.txt cat_to_name.json $APP_HOME/
COPY templates $APP_HOME/templates/
COPY static $APP_HOME/static/
COPY uploads $APP_HOME/uploads/
COPY model_data $APP_HOME/model_data/

## Step 3:
# Install packages from requirements.txt
RUN pip install -r requirements.txt && \
    rm /app/requirements.txt

## Step 4:
# Expose port 8080
EXPOSE 8080

# Run app.py at container launch
CMD ["python", "app.py"]