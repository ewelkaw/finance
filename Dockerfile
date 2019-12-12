FROM python:3.6.9-alpine3.10
WORKDIR /app
ENV FLASK_APP application.py
ENV FLASK_ENV development
ENV FLASK_RUN_HOST 0.0.0.0
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt
COPY . .
RUN python db_request.py
EXPOSE 8000
CMD ["flask", "run"]

# docker login
# docker build . -t investment_app
# docker image ls

