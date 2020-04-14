Intelligent Show Room (ISR)

# Deployment Guide:

*Prerequisite*:
* Python 2.7
* MySQL [Install Guide](http://supervisord.org/installing.html)
* Redis [Install Guide](http://redis.io/topics/quickstart)
* Nodejs [Install Guide](https://nodejs.org/en/download/package-manager/)
* Grunt [Install Guide](http://gruntjs.com/getting-started)

*Steps*:

 1) Clone project code
```bash
$ git clone git@github.com:5peng/ucdip.git
```

 2) List item
```bash
$ cd ucdip/isr/
$ virtualenv venv
```

3) Activate venv
```bash
$ source venv/bin/activate
```

4) Setup database
```bash
$ mysql -uroot -p
mysql > CREATE SCHEMA `isr` DEFAULT CHARACTER SET utf8;
mysql > CREATE USER 'isr'@'localhost' IDENTIFIED BY 'welcome';
mysql> GRANT ALL PRIVILEGES ON isr.* TO 'isr'@'localhost';
mysql> FLUSH PRIVILEGES;
mysql> exit;
$ export DATABASE_URL=mysql://isr:1qaz2wsx@localhost/isr?charset=utf8
```

5) Setup redis
```bash
export REDIS_URL=redis://:foobared@localhost:6379
```

6) Run app
```bash
make run-all
```

7)  Test application
```bash
$ export MODE=debug
$ python manage.py runserver
$ curl http://127.0.0.1:5000/api/stores/2/sales
```
The application runs OK if an empty json array is returned. 

*Others:*

- Setup supervisor
```bash
$ cp deploy/gunicorn.conf.sample deploy/gunicorn.conf # make changes as you want
$ cp deploy/isrd.conf.sample deploy/isrd.conf # make changes as you want
$ cp deploy/celeryd.conf.sample deploy/celeryd.conf # make changes as you want
```
Then add isrd.conf and celeryd.conf to /etc/supervisor.conf

- Config nginx to dispatch request to gunicorn

- Grunt tasks
1) compile all scss and combine js files in projects with source map, without source code compress.
```bash
$ grunt dev
```
2) compile all js files only (combine all js, without compress)
```bash
$ grunt shampoo:dev
```
3) compile all scss files with source map, without compress.
```bash
$ make sass:dev
```
4) compile all scss with source map and combine js files, with js files modify watcher (will automatic update target js after file changes).
```bash
$ grunt watch
```
5) combine all js files (only) without compress and watch js file changes.
```bash
$ grunt shampoo:watch
```

- Load lookups
1) Setup lookups for a new store
```bash
$ python manage.py lookup setup -s <store_id>
```
2) Reload lookupvalues for a lookup
```bash
$ python manage.py lookup reload --id <lookup_id> -l <lookup_values_csv_location>
```