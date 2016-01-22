FROM python:2-onbuild
EXPOSE 8081
CMD [ "python", "cartserver.py", "--port", "8081", "--address", "0.0.0.0" ]

