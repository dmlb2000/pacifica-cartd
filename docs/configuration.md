# Configuration

The Pacifica Core services require two configuration files. The REST
API utilizes [CherryPy](https://github.com/cherrypy) and review of
their
[configuration documentation](http://docs.cherrypy.org/en/latest/config.html)
is recommended. The service configuration file is a INI formatted
file containing configuration for database connections.

## CherryPy Configuration File

An example of Cartd server CherryPy configuration:

```ini
[global]
log.screen: True
log.access_file: 'access.log'
log.error_file: 'error.log'
server.socket_host: '0.0.0.0'
server.socket_port: 8081

[/]
request.dispatch: cherrypy.dispatch.MethodDispatcher()
tools.response_headers.on: True
tools.response_headers.headers: [('Content-Type', 'application/json')]
```

## Service Configuration File

The service configuration is an INI file and an example is as follows:

```ini
[cartd]
; This section describes cartd specific configuration

; Local directory to stage data
volume_path = /tmp/

; Least recently used buffer time
lru_buffer_time = 0

; Bundle backend task enable/disable
bundle_task = True

[archiveinterface]
; This section describe where the archive interface is

; URL to the archive interface
url = http://127.0.0.1:8080/

[celery]
; This section describe celery task configuration

; Broker message url
broker_url = pyamqp://

; Backend task channel
backend_url = rpc://

[database]
; This section contains database connection configuration

; peewee_url is defined as the URL PeeWee can consume.
; http://docs.peewee-orm.com/en/latest/peewee/database.html#connecting-using-a-database-url
peewee_url = sqliteext:///db.sqlite3

; connect_attempts are the number of times the service will attempt to
; connect to the database if unavailable.
connect_attempts = 10

; connect_wait are the number of seconds the service will wait between
; connection attempts until a successful connection to the database.
connect_wait = 20
```

## Starting the Service

Starting the Cartd service can be done by two methods. However,
understanding the requirements and how they apply to REST services
is important to address as well. Using the
internal CherryPy server to start the service is recommended for
Windows platforms. For Linux/Mac platforms it is recommended to
deploy the service with
[uWSGI](https://uwsgi-docs.readthedocs.io/en/latest/).

### Deployment Considerations

The Cartd service stages data for consumption by data users. This
service (like Ingest) should be put on the edge of your
infrastructure to allow for fast access. Other considerations about
data transfers over these networks should also be considerred. ESNet
has some good documentation on how to
[optimize Linux](http://fasterdata.es.net/) for fast data transfers.

### CherryPy Server

To make running the Cartd service using the CherryPy's builtin
server easier we have a command line entry point.

```
$ pacifica-cartd --help
usage: pacifica-cartd [-h] [-c CONFIG] [--cpconfig CONFIG] [-p PORT]
                      [-a ADDRESS]

Run the cart server.

optional arguments:
  -h, --help            show this help message and exit
  -c CONFIG, --config CONFIG
                        cart config file
  --cpconfig CONFIG     cherrypy config file
  -p PORT, --port PORT  port to listen on
  -a ADDRESS, --address ADDRESS
                        address to listen on
$ pacifica-cartd-cmd dbsync
$ pacifica-cartd
[09/Jan/2019:09:17:26] ENGINE Listening for SIGTERM.
[09/Jan/2019:09:17:26] ENGINE Bus STARTING
[09/Jan/2019:09:17:26] ENGINE Set handler for console events.
[09/Jan/2019:09:17:26] ENGINE Started monitor thread 'Autoreloader'.
[09/Jan/2019:09:17:26] ENGINE Serving on http://0.0.0.0:8081
[09/Jan/2019:09:17:26] ENGINE Bus STARTED
```

### uWSGI Server

To make running the Cartd service using uWSGI easier we have a
module to be included as part of the uWSGI configuration. uWSGI is
very configurable and can use this module many different ways. Please
consult the
[uWSGI Configuration](https://uwsgi-docs.readthedocs.io/en/latest/Configuration.html)
documentation for more complicated deployments.

```
$ pip install uwsgi
$ uwsgi --http-socket :8081 --master --module pacifica.cartd.wsgi
```
