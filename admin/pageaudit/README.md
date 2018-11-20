# PageLab - Reporting app

* The PageLab reporting app is built on Django. It consumes Lighthouse report data objects and visualizes URL audits, averages and historical page trends.

## Installation

**Dependencies**

* node 8+
* python 3+
* postgres 9.6+
* [PageLab node app](../../pageaudit)


**Note**: We are using python 3, so any command should use  `python3` for the command, not `python`.
If you accidentally use `python` you will get an error like: _"Couldn't import Django. Are you sure it's installed..."_

## Getting started - First time install:

- Ensure you have the dependencies installed.
- Setup some environment variables on your machine, replacing the `___` with your local Postgres DB user ID/PW.
 
```
DJANGO_DB_HOST=127.0.0.1
DJANGO_DB_PASSWORD=____
DJANGO_DB_USER=____
DJANGO_DEBUG_FLAG=True
DJANGO_ENV=production
DJANGO_FORCE_SCRIPT_NAME=
```
- Create a database called `perf_lab` (default), or create an ENV variable called `DJANGO_DB_NAME` and set it to your local database name.
- Clone the repo.
- Run `npm install`.



## Getting started - Coding:
- Run `./manage.py migrate` so Django can create and setup your database as needed.
- Start the app by running `runserver` (in this root directory).
- To view the site, open a browser to `https://localhost:8000/report/`
- To view the Django admin, goto `https://localhost:8000/admin/`
- We try and follow the Django and Python coding design and style guides as found here: 
    - https://docs.djangoproject.com/en/2.0/misc/design-philosophies/
    - https://docs.djangoproject.com/en/2.0/internals/contributing/writing-code/coding-style/

## Populating data
- To populate the PageLab Django app with data, goto the Django admin and add a couple URLs to test.
- Install the [PageLab node app](../../pageaudit).
- Run the PageLab node app.
- The PageLab node app will test each URL you have in the Django app once, then stop.
- Go back and view the site at `https://localhost:8000/report/` and you should see some reports.

## Design
We are using:
- [Tachyons](https://tachyons.io/) for the main app theme.
- [Eva icons](https://akveo.github.io/eva-icons/#/) for the icons.
- [Hint.css](https://kushagragour.in/lab/hint/) for the tooltip.
- [Micromodal.js](https://micromodal.now.sh/) for the modal overlays.

