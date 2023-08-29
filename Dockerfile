FROM python:3.11
WORKDIR /app
COPY ZimbraAPI.py AuthData.py ZimbraUser.py ResponseData.py config.py requirements.txt /app/
COPY app.py /app/
RUN pip install gunicorn
RUN pip install -r requirements.txt
RUN mkdir logs
CMD ["gunicorn", "--bind", "0.0.0.0:80", "--access-logfile", "-", "app:app"]
