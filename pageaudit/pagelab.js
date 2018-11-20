/*

   PageLab server

   Author: David Dahl, d.dahl@ibm.com, ( https://github.com/daviddahl )

   https://github.com/IBM/page-lab

   PageLab server pulls a list of urls from a Django API, feeds it into
   redis-server, and each worker launched plucks the next url from the
   queue and runs headless chrome / ligthouse to audit the page
   performance, accessibility, SEO, etc.

   The result data is POSTed to Django for visualization and storage.

*/

const EventEmitter = require('events');
const cluster = require('cluster');

const program = require('commander');
const lighthouse = require('lighthouse');
const chromeLauncher = require('chrome-launcher');

const validUrl = require('valid-url');
const fetch = require('node-fetch');
const RedisSMQ = require('rsmq');
const redis = require('redis');
const jsonify = require('redis-jsonify');
const express = require('express');
const shell = require('shelljs');

const log = require('lighthouse-logger');
const LOG_LEVEL = process.env['PL_LH_LOG_LEVEL'] || 'error';
log.setLevel(LOG_LEVEL);

const VERSION = '0.0.2';
const PL_APP_NAME = 'PageLab';
const PL_EXPRESS_PORT = 1717;

const MAX_RUNS_BEFORE_RESTART = process.env['PAGE_LAB_MAX_RUNS_BEFORE_RESTART'] || 1000;
const WORKERS_CLEARED_TS = 'workersClearedTS';
var SERVER_START_TS = Date.now();

const MSG_REPORT_URL = 'Worker url is:';
const MSG_WORKER_DISCONNECT = 'Worker disconnecting...';
const ACTION_CHROME_PID = 100;
const ACTION_COLLECTION_COMPLETE = 101;
const ACTION_REPORT_URL = 1000;

const SUCCESS_RUNS = 'successfulRuns';

program
    .version(VERSION)
    .option('-q, --queuename <name>',
            'The name of the redis queue')
    .option('-i, --infinity',
            'set Infinity Mode defaults to 0. 1 is on')
    .option('-t, --timeout',
            'Queue fill timeout in seconds. Default 10',
            parseInt) // Not working?!
    .option('-r, --reporturl <url>',
            'The report POST url (Django view)')
    .option('-l, --listurl <url>',
            'The get url list enpoint (Django view)');
program.parse(process.argv);

const Q_NAME = program.queuename ||
      process.env['PAGE_LAB_REDIS_Q_NAME'] ||
      'lighthouse-queue';
const Q_EMPTY = 'q_empty';
const Q_INFINITY_MODE = program.infinity ||
      process.env['PAGE_LAB_INFINITY_MODE']
      || false;
var Q_LAST_FILLED = null;
// Do not fill the queue if it has been filled in th elast 10 seconds
const Q_FILL_TIMEOUT = program.timeout ||
      process.env['PAGE_LAB_Q_FILL_TIMEOUT']
      || 10;

// Chrome flags
const opts = {
    logLevel: LOG_LEVEL,
    chromeFlags: [
        '--headless',
        '--config-path=config.js',
    ]
};

// Lighthouse config file
const lhConfig = require('./config.js');

const REPORT_POST_URL = program.reporturl ||
      process.env['PAGE_LAB_REPORT_POST_URL'] ||
      'https://127.0.0.1:8000/collect/report/';
const MSG_HTTP_POST_ENDPOINT_ERR = `Is HTTP POST API ENDPOINT (${REPORT_POST_URL}) DOWN?`;
const URLS_LIST_URL = program.listurl ||
      process.env['URLS_LIST_URL'] ||
      'https://127.0.0.1:8000/queue/';
const URLS_LOADED = 'urlsLoaded';

const PAGE_LAB_WORKER_TIMEOUT_MS = 2000;

const lhQ = new RedisSMQ({
    host: process.env['PAGE_LAB_REDIS_HOST'] || '127.0.0.1',
    port: process.env['PAGE_LAB_REDIS_PORT'] || 6379,
    ns: process.env['PAGE_LAB_REDIS_NS'] || 'rsmq'
});

var Q_TIME_CREATED = 0;
var Q_URLS_LENGTH = 0;
var ATTEMPTED_RUNS = 'attemptedRuns';

lhQ.createQueue({qname:Q_NAME}, (err, resp) => {
    if (err) {
        if (err.message == 'Queue exists') {
            console.info('queue exists...');
        } else {
            console.error(err);
            process.exit(1);
        }
    } else if (resp === 1) {
        Q_TIME_CREATED = Date.now();
        console.log('queue created');
    }
});

process.env['NODE_TLS_REJECT_UNAUTHORIZED'] = '0';

// Reference to mapping # workers to CPU cores
const numWorkers = process.env['PAGE_LAB_NUM_WORKERS'] || 12;

// set up the jsonStore
const jsonStore = jsonify(redis.createClient());

let workerIndex = 0;

const appState = {
    get [workerIndex]() {
        return jsonStore.get(workerIndex, (err, result) => {
            if (err) {
                return null;
            }
            return result;
        });
    },

    set [workerIndex](value) {
        return jsonStore.set(workerIndex, value, (err, result) => {
            if (err) {
                throw new Error(`Cannot set worker data: ${workerIndex}: ${value}`);
            }

            return result;
        });
    },

    del: (key, cb) => {
        return jsonStore.send_command('DEL', key, (err, result) => {
            if (err) {
                return cb(err, null);
            } else {
                return cb(err, result);
            }
        });
    },

    get current() {
        // Get all of the keys we can find
        let state = [];
        for (let i = 1; i < 1000; i++) { // <-- TODO: FIX THIS... ridiculous I know
            let val = appState[i];
            if (typeof val === 'object' && val !== null) {
                state.push(val);
            }
        }
        return state;
    }
};


if (cluster.isMaster) {
    // debugger;
    appState[SUCCESS_RUNS] = 0;
    appState[WORKERS_CLEARED_TS] = 0;
    appState[ATTEMPTED_RUNS] = 0;

    // Only Fill the queue if it is empty!
    lhQ.getQueueAttributes({ qname: Q_NAME }, (err, resp) => {
        if (err) {
            console.error(err);
            throw new Error(err);
        } else {
            if (parseInt(resp.msgs) === 0) {
                fillQueue();
                return;
            } else if (parseInt(resp.msgs) > 0) {
                console.log(URLS_LOADED);
                urlEmit.emit(URLS_LOADED);
                Q_URLS_LENGTH = parseInt(resp.msgs).length;
                Q_TIME_CREATED = Date.now();
                SERVER_START_TS = Date.now();
            }
        }
    });

    // Server operations
    function fillQueue () {
        fetch(URLS_LIST_URL).then((res) => res.json())
            .then((json) => {
                Q_LAST_FILLED = Date.now();
                Q_URLS_LENGTH = json.message.length;
                json.message.forEach((url) => {
                    lhQ.sendMessage({
                        qname: Q_NAME,
                        message: url.url}, (err, resp) => {
                            if (resp) {
                                console.log("Url added to queue. ID:", resp);
                            } else if (err) {
                                console.error(err);
                            }
                        });
                });
                urlEmit.emit(URLS_LOADED);
            })
            .catch((error) => {
                console.error(error);
            });
    }

    class UrlEmitter extends EventEmitter {}
    const urlEmit = new UrlEmitter();
    const BACKOFF_MS = 100;

    urlEmit.on(URLS_LOADED, () => {
        console.log('urls Loaded!');
        for (let i = 0; i < numWorkers; i++) {
            // Create a worker
            // Incrementally space out workers so they don't choke eachother.
            setTimeout(() => {
                let worker = cluster.fork();
            }, PAGE_LAB_WORKER_TIMEOUT_MS + (BACKOFF_MS * i));
        }
    });

    cluster.on('message', (worker, msg) => {
        console.log(`msg received from worker:`, msg);

        if (msg.err) {
            if (msg.err == Q_EMPTY) {
                if (Q_INFINITY_MODE) {
                    fillQueue();
                    return;
                }
            }
        }
        if (msg.action) {
            switch (msg.action) {
            case ACTION_REPORT_URL:
                // we can update our array
                var state = appState[msg.worker];
                if (state) {
                    state.url = msg.url.message;
                    appState[msg.worker] = state;
                } else {
                    appState[msg.worker] = {
                        id: msg.worker,
                        url: msg.url.message
                    };
                }
                break;
            case ACTION_CHROME_PID:
                try {
                    var state = appState[msg.worker];
                    if (state) {
                        state.pid = msg.pid;
                        state.browserStart = Date.now();
                        appState[msg.worker] = state;
                    } else {
                        appState[msg.worker] = {
                            pid: msg.pid,
                            id: msg.worker,
                            browserStart: Date.now()
                        };
                    }
                } catch (ex) {
                    console.error(ex);
                }
                break;
            case ACTION_COLLECTION_COMPLETE:
                var state = appState[msg.worker];
                if (state) {
                    // appState.del(msg.worker);
                    // for now just null it:
                    appState[msg.worker] = null;
                }
                let success = appState[SUCCESS_RUNS];
                appState[SUCCESS_RUNS] = parseInt(success) + 1;

                break;
            default:
                return;
            }
        }
    });

    cluster.on('disconnect', (worker) => {
        console.log(MSG_WORKER_DISCONNECT, worker.id);

        lhQ.getQueueAttributes({ qname: Q_NAME }, (err, resp) => {
            if (err) {
                console.error(err);
            } else {
                if (parseInt(resp.msgs) === 0) {
                    console.info('...QUEUE EXHAUSTED...');
                    console.info(`Workers: ${Object.keys(cluster.workers).length}`);
                    // XXX: Perhaps we ping the database endpoint at this point to see if we are allotted more urls to process?
                    if (!Q_INFINITY_MODE) {
                        // We will not kill the server unless INFINITY_MODE is on
                        // pm2 will restart the server when we kill it - so if we do not want to run tests 24x7 we just wait

                        // By not killing the server, it never restarts and does not re-fill the queue
                        return;
                    }
                    if (!Object.keys(cluster.workers).length) {
                        // all workers are gone
                        // kill server
                        console.info('All workers are complete, quitting server...');
                        appState[WORKERS_CLEARED_TS] = Date.now();
                        // process.exit(0);
                    }
                    return;
                }

                // Let's check to see if we have hit max runs - if not fork()
                if (parseInt(resp.msgs) > 0 &&
                    (appState[SUCCESS_RUNS] <= MAX_RUNS_BEFORE_RESTART)) {
                    appState[WORKERS_CLEARED_TS] = 0;
                    cluster.fork();
                    return;
                }

                if (appState[SUCCESS_RUNS] >= MAX_RUNS_BEFORE_RESTART) {
                    // Set the workers_cleared_ts as we want to force them
                    // to die if zombies or inconvenenient
                    appState[WORKERS_CLEARED_TS] = Date.now();

                    if (Object.keys(cluster.workers).length === 0) {
                        // no more workers, shutdown app as we have
                        // reached MAX_RUNS
                        console.info('PageLab: reached end of MAX_RUNS_BEFORE_RESTART');
                        console.info('PageLab: Killing Chrome instances');
                        if (shell.exec('killall chrome').code === 0) {
                            shell.echo('killed Chrome instances');
                            shell.exit(0);
                        } else {
                            shell.echo('Could not killed Chrome instances?');
                            shell.exit(1);
                        }
                        process.exit(0);
                        // Restart via pm2 or supervisor
                    } else if ((Date.now() - appState[WORKERS_CLEARED_TS]) > 2000) {
                        // we have hanging workers kill them and exit
                        cluster.workers.forEach((worker, idx) => {
                            try {
                                worker.kill();
                            } catch (ex) {
                                console.warn(`Error killing off worker: ${ex}`);
                            }
                        });
                        console.error('PageLab has hanging workers');
                        // process.exit(1);
                    }
                }
            }
        });

        // check to make sure any hung workers are killed:
        let current = appState.current;
        current.forEach((worker, idx) => {
            if (worker !== null) {
                if (!cluster.workers[worker.id]) {
                    appState[worker.id] = null;
                } else {
                    let workerData = appState[worker.id];
                    let now = Date.now();
                    if ((now - workerData.browserStart) > 20000) {
                        // hung test, kill it
                        cluster.workers[worker.id].kill();
                        appState[worker.id] = null;
                    }
                }
            }
        });
    });

    cluster.on('online', (worker) => {
        console.log('Yay, the worker responded after it was forked');
    });

    const app = express();
    app.get('/status', (req, res) => {
        // return the current status of the server
        serverStatus((status) => {
            res.send(status);
        });
    });

    app.get('/', (req, res) => {
        res.send(`${PL_APP_NAME} ${VERSION}`);
    });

    app.listen(PL_EXPRESS_PORT, () => {
        console.info(`${PL_APP_NAME} master server running on port ${PL_EXPRESS_PORT}`);
    });

    function serverStatus(cb) {
        // server version & config data/ env
        // number of workers
        // server start time
        // number of processed url tests
        // number of errors
        // last n list of urls processed
        // queue length

        if (typeof cb != 'function') {
            throw new Error('cb arg should be a function');
        }
        let errors = ['ERROR_COLLECTION_NOT_IMPLEMENTED'];
        let response = null;

        lhQ.getQueueAttributes({ qname: Q_NAME }, (err, resp) => {
            if (err) {
                console.error(err);
                errors.push(err);
            }
            let currentQLength = 0;
            try {
                currentQLength = parseInt(resp.msgs);
            } catch (ex) {
                console.info(ex);
            }

            let elapsedTime = (Date.now() - SERVER_START_TS) / 1000;
            let averageRunTime = 'TBD';
            if (appState[SUCCESS_RUNS] > 0) {
                averageRunTime = (elapsedTime / appState[SUCCESS_RUNS]);
            }
            cb({
                version: VERSION,
                numberOfActualWorkers: Object.keys(cluster.workers).length,
                currentQLength: currentQLength,
                errors: errors,
                appState: appState.current,
                numWorkersConfigured: parseInt(numWorkers),
                qTimeCreated: Q_TIME_CREATED,
                serverStart: SERVER_START_TS,
                qLength: Q_URLS_LENGTH,
                urlsProcessedSuccessfully: appState[SUCCESS_RUNS],
                elapsedTimeSeconds: elapsedTime,
                averageRunTimeSeconds: averageRunTime,
                maxRunsBeforeRestart: parseInt(MAX_RUNS_BEFORE_RESTART),
                attemptedRuns: appState[ATTEMPTED_RUNS]
            });
        });
    }

} else {
    ///////////////////////
    // BEGIN Worker CODE //
    ///////////////////////
    const PL_WORKER_EXPRESS_PORT = 7272;

    // Start a Worker and run a test
    const wApp = express();

    wApp.listen(PL_WORKER_EXPRESS_PORT, () => {
        console.info(`${PL_APP_NAME} worker server running on port ${PL_WORKER_EXPRESS_PORT}`);
    });

    process.send({msg: 'New worker started...'});

    lhQ.popMessage({ qname: Q_NAME }, (err, resp) => {
        if (err) {
            process.send({err: err, action: 'popMessage'});
            return;
        }
        process.send({
            action: ACTION_REPORT_URL,
            msg: `${MSG_REPORT_URL}: ${resp.message}`,
            url: resp,
            worker: cluster.worker.id
        });

        runTest(resp, cluster.worker.id);
    });

    process.on('message', (msg) => {
        console.log(`msg received from master:`, msg);
    });
}

// Each worker that exits() is reported here
cluster.on('exit', (worker, code, signal) => {
    console.log(
        'Worker %d killed/died with code/signal %s',
        worker.process.pid, signal || code
    );
});


process.on("uncaughtException", (error) => {
    console.error('Uncaught Exception: ', error);
    if (!cluster.isMaster) {
        process.exit(1);
    } else {
        if (!Object.keys(cluster.workers).length) {
            // no more workers, kill master
            process.exit(1);
        }
    }
});

function runTest(url, workerId) {
    let config = {
        url: url.message,
        worker: workerId
    };

    performAudit(config);
}

// Validate the url object we get from the Redis Queue
// Launch Chrome headlessly and run the audit
// TODO: handle additional configuration parameters for individual
// test runs: simulation of network throuput, devices, SEO, SPA, Ofline, etc
function performAudit (config) {
    if (!config.url) {
        throw new Error('config.url is required');
    }

    if (!validUrl.isUri(config.url)) {
        throw new Error('config.url is not a valid URL');
    }

    if (!config.worker) {
        throw new Error('config.worker is required (worker custer id)');
    }

    if (config.reportUrl && !validUrl(config.reportUrl)) {
        throw new Error('config.reportUrl is not valid');
    }

    process.send({ msg: `Processing url: ${config.url}` });

    launchChromeAndRunLighthouse(config.url, opts, lhConfig, config.worker)
        .then((response) => {
            // TODO: Attempted here does not work
            let attempted = appState[ATTEMPTED_RUNS];
            appState[ATTEMPTED_RUNS] = attempted + 1;
            process.send({msg: config.url, status: 'Received response from Lighthouse'});
            if (response) {
                debugger;
                if (!response.report) {
                    process.send({
                        msg: config.url,
                        status: 'response.report is undefined',
                        response: response
                    });
                    response.report = {
                        'error': 'Cannot get response.report from LH',
                        'url': 'config.url'
                    };
                    process.send(response);
                } else {
                    // we have the report
                    debugger;
                    fetch(REPORT_POST_URL, {
                        method: 'POST',
                        body: JSON.stringify({
                            lhr:{ },
                            report: response.report,
                            artifacts: { }
                        }),
                        headers:{
                            'Content-Type': 'text/plain',
                            'Referrer': process.env['PAGE_LAB_REFERRER_URL'] ||
                                'https://127.0.0.1:8000/'
                        }
                    }).then((jsonResponse) => {
                        if (!jsonResponse.ok) {
                            process.send({
                                jsonResponse: jsonResponse.ok,
                                error: MSG_HTTP_POST_ENDPOINT_ERR
                            });
                            console.error(MSG_HTTP_POST_ENDPOINT_ERR);
                            console.error(jsonResponse.statusText);
                            // throw new Error(MSG_HTTP_POST_ENDPOINT_ERR);
                        }
                        process.send({
                            action: ACTION_COLLECTION_COMPLETE,
                            worker: config.worker
                        });
                        process.exit(0);
                    }).catch((error) => {
                        process.send({
                            error: error,
                            error: MSG_HTTP_POST_ENDPOINT_ERR
                        });
                        process.exit(1);
                    });
                }
            } else {
                process.send({
                    url: config.url,
                    error: 'Response is null',
                    response: response
                });
            }
            // }); // end async function
        });
}

// ### NOTES FROM Lighthouse Docs:
// use results.lhr for the JS-consumeable output
// https://github.com/GoogleChrome/lighthouse/blob/master/typings/lhr.d.ts
// use results.report for the HTML/JSON/CSV output as a string
// use results.artifacts for the trace/screenshots/other specific case you need (rarer)
async function launchChromeAndRunLighthouse(url, opts, config = null, workerId = null) {
    return chromeLauncher.launch({chromeFlags: opts.chromeFlags})
        .then(chrome => {
            // tell master process about chrome.pid
            process.send({
                action: ACTION_CHROME_PID,
                pid: chrome.pid,
                worker: workerId
            });
            opts.port = chrome.port;
            return lighthouse(url, opts, config)
                .then(results => {
                    return chrome.kill().then(() => results);
            }).catch((error) => {
                try {
                    process.send({error: error});
                } catch (ex) {
                    console.error(error);
                }
                chrome.kill();
                process.exit(1);
            });
        }).catch(error => {
            process.send({err: error, msg: 'Could not launch Chrome'});
            process.exit(1);
        });
}

// [PM2] To setup the Startup Script, copy/paste the following command:
// sudo env PATH=$PATH:/home/webplatform/.nvm/versions/node/v10.8.0/bin /home/webplatform/.nvm/versions/node/v10.8.0/lib/node_modules/pm2/bin/pm2 unstartup systemd -u webplatform --hp /home/webplatform
