# Use an official Python runtime as a parent image
FROM python:3.8-slim-buster

# Set the working directory to /app
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

RUN chmod 777 -R /app

# pip installations
RUN pip install --upgrade pip
RUN pip install pycountry
RUN pip install "dash[diskcache]"
RUN pip install dash-bootstrap-components
RUN pip install dash-daq
RUN pip install numpy
RUN pip install pandas
RUN pip install boto3
RUN pip install tqdm
RUN pip install fsspec
RUN pip install s3fs
RUN pip install road-database-toolkit

ENV PYTHONPATH=/app
ENV AWS_STS_REGIONAL_ENDPOINTS=regional
USER root

# Make port 6007 available to the world outside this container
EXPOSE 6007

# Run app.py when the container launches
CMD ["python", "/app/road_eval_dashboard/app.py"]
