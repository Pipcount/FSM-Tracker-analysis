# Official Python image : https://hub.docker.com/_/python
FROM python:3.12-slim

WORKDIR /app

COPY . /app

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install cron
RUN apt-get update && apt-get install -y cron

# Add crontab file in the cron directory
ADD crontab /etc/cron.d/polar_cron

# Give execution rights on the cron job
RUN chmod 0644 /etc/cron.d/polar_cron

# Apply cron job
RUN crontab /etc/cron.d/polar_cron

# Create the log file to be able to run tail
RUN touch /var/log/cron.log

# Run the command on container startup
CMD cron && tail -f /var/log/cron.log
