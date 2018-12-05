# PageLab - Reporting app

* The PageLab reporting app is built on Django. It consumes Lighthouse report data objects and visualizes URL audits, averages and historical page trends.

## Installation

**Dependencies**

* node 8+
* python 3+
* postgres 9.6+
* [PageLab node app](../../pageaudit)


**Note**: We are using python 3. If you already have python 2 setup and mapped to `python` command, you will need to use `python3`. Or you can setup a virtual env. and make life easy for yourself and have `python` mapped to `python3`.



## Getting started - First time install:

1. Ensure you have the dependencies installed.
2. Clone the repo.
3. From the repo root directory, run `pip3 install -r admin/requirements.txt` to install Django and all it's requirements for the app.
4. There are some local variables and settings needed for your implementation. They can either be set as environment variables, or you can add a `settings_local.py` file alongside the Django default `settings.py` file in the `admin/pageaudit/pageaudit/` directory with them.
 Replace the `___` with your local Postgres DB user ID/PW.


```
    DJANGO_DB_HOST=127.0.0.1
    DJANGO_DB_PASSWORD=____
    DJANGO_DB_USER=____
    DJANGO_DEBUG_FLAG=True
    DJANGO_ENV=production
    DJANGO_FORCE_SCRIPT_NAME=
```
- Create a database called `perf_lab` (default), or create a variable called `DJANGO_DB_NAME` and set it to your local database name.



## Getting started - Sample data:
A sample data set is available to be loaded via Django's `manage.py loaddata` command. The sample data set contains:
- 51 URLs (50 with runs)
- Each URL has ~13 test runs.
- Superuser with ID/PW: `superuser` / `django4ever`
- The sample data set file is available here: https://github.com/ecumike/page-lab-sampledata


## Getting started - Coding:
- Run `./manage.py migrate` so Django can create and setup your database as needed.
- Start the app by running `runserver` (in this root directory).
- To view the site, open a browser to `https://localhost:8000/report/`
- To view the Django admin, goto `https://localhost:8000/admin/`
- We try and follow the Django and Python coding design and style guides as found here: 
    - https://docs.djangoproject.com/en/2.0/misc/design-philosophies/
    - https://docs.djangoproject.com/en/2.0/internals/contributing/writing-code/coding-style/


## Populating data
You can pre-populate the app with the sample data set as above, and/or you can add URLs via the Django admin and run a few test runs via the Node app.
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

