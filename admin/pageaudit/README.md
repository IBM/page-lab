# PageLab - Reporting app

* The PageLab reporting app is built on Django. It consumes Lighthouse report data objects and visualizes URL audits, averages and historical page trends.

## Installation

**Dependencies**

* node 8+
* python 3+
* postgres 10+
* 
* [PageLab node app](../../pageaudit)


_Note_: We are using python 3, so any command should use  `python3` for the command, not `python`.
If you accidentally use `python` you will get an error like: _"Couldn't import Django. Are you sure it's installed..."_

## Getting started - First time install:

- Ensure you have the dependencies installed.
- Create a database called `perf_lab`.
- Clone the repo.
- `npm install`
- Setup some environment variables on your machine, replacing the `___` with your local Postgres DB user ID/PW.
 
```
DJANGO_DB_HOST=127.0.0.1
DJANGO_DB_PASSWORD=____
DJANGO_DB_USER=____
DJANGO_DEBUG_FLAG=True
DJANGO_ENV=production
DJANGO_FORCE_SCRIPT_NAME=
```



## Getting started - Coding:
- Start the app by running `runserver` (in this root directory).
- To view the site, open a browser to `http://localhost:8000/report/`
- To view the Django admin, goto `http://localhost:8000/admin/`
- We try and follow the Django and Python coding design and style guides as found here: 
    - https://docs.djangoproject.com/en/2.0/misc/design-philosophies/
    - https://docs.djangoproject.com/en/2.0/internals/contributing/writing-code/coding-style/

## Populating data
- To populate the PageLab Django app with data, goto the Django admin and add a couple URL to test.
- Install and run the [PageLab node app](../../pageaudit)
- The [PageLab node app](../../pageaudit) will test each URL you have in the Django app once, then stop.
- Go back and view the site at `http://localhost:8000/report/` and you should see some reports.


