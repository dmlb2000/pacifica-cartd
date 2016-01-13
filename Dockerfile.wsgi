FROM python:2-onbuild
EXPOSE 8080
CMD [ "python", "cartserver.py", "--port", "8080", "--address", "0.0.0.0" ]

