FROM python:3.10-slim

# Set up a new user named "user" with user ID 1000
# (Hugging Face Spaces requires this specific non-root user setup)
RUN useradd -m -u 1000 user
USER user

# Set home to the user's home directory
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH

# Structure the workspace
WORKDIR $HOME/app

# Copy the dependencies first (for faster rebuilds)
COPY --chown=user:user requirements.txt .

# Install dependencies (no-cache to save disk space on cloud)
RUN pip install --no-cache-dir -r requirements.txt

# Copy all the rest of the application files
COPY --chown=user:user . .

# Expose the precise port that Hugging Face listens to automatically
EXPOSE 7860

# Execute Gunicorn WSGI Server bound to HF's required port
CMD ["gunicorn", "--bind", "0.0.0.0:7860", "--workers", "1", "--timeout", "120", "run:app"]
