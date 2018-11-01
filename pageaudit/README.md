# perf_lab

* PageAudit node server

## node server that queues up Lighthouse test runs

* Node app talks to the pageaudit admin app via HTTP
* Gets a url to run through Lighthouse
* Reports back the results to the admin app which stores each run's report data

## Installation

## Dependencies

* node 8
* redis-server https://redis.io/topics/quickstart
* (`brew install redis` or `sudo apt install redis-server`)
* _pageaudit_ django app [../]

Get _pageaudit_ django app up and running, add some Urls then...

`npm install`

`node cluster.js` to start

PageAudit node server will connect to the Django server, request all the Urls and fill the redis queue with them.

Wokers will fork, grab a url from the queue and run a Lighthouse performance , a18y or other audit and report back to the Django server.

