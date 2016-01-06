FROM python:2-onbuild
USER "daemon"
CMD [ "celery", "-A","cart","worker","-l", "info" ]

