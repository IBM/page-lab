'use strict';

// Specs used for reference:  
// https://github.com/WPO-Foundation/webpagetest/blob/master/www/settings/connectivity.ini.sample
// https://github.com/GoogleChrome/lighthouse/blob/8f500e00243e07ef0a80b39334bedcc8ddc8d3d0/lighthouse-core/config/constants.js#L19-L26

// AVG GLOBAL WEB VISITOR profile according to Akamai global speed reports.
// Using 4G option from URL above, adjusted based on "global average" visits, 
//  countries + cross-reference Akamai state-of-the-internet quarterly report.
// CPUslowdown.. if we are to assume it's "the factor slowdown of machine this is running on"...
//  considering we're running this on the server... 3 seems good. 4 is what they use for 3g mobile.
const throttlingAvgUser = {
    rttMs: 75,
    requestLatencyMs: 150,
    downloadThroughputKbps: 10000,
    uploadThroughputKbps: 3000,
    throughputKbps: 10000,
    cpuSlowdownMultiplier: 3,
};


// LIGHTHOUSE SOURCE CODE SETTINGS.
// Adding here for testing and reference how they do it.
const DEVTOOLS_RTT_ADJUSTMENT_FACTOR = 3.75;
const DEVTOOLS_THROUGHPUT_ADJUSTMENT_FACTOR = 0.9;
const throttlingMobile3G = {
    rttMs: 150,
    throughputKbps: 1.6 * 1024,
    requestLatencyMs: 150 * DEVTOOLS_RTT_ADJUSTMENT_FACTOR,
    downloadThroughputKbps: 1.6 * 1024 * DEVTOOLS_THROUGHPUT_ADJUSTMENT_FACTOR,
    uploadThroughputKbps: 750 * DEVTOOLS_THROUGHPUT_ADJUSTMENT_FACTOR,
    cpuSlowdownMultiplier: 4,
};


module.exports = {
    extends: 'lighthouse:default',
    settings: {
        throttlingMethod: 'simulate',
        throttling: throttlingAvgUser,
        onlyCategories: ['performance','accessibility', 'seo',],
        disableDeviceEmulation: false,
    },

    passes: [{
        passName: 'defaultPass',
        gatherers: [
            'gather-localstorage',
        ],
    }],

    audits: [
        'audit-localstorage',
    ],

    categories: {
        localstorage: {
            title: 'LocalStorage audit',
            description: 'Localstorage usage metrics',
            auditRefs: [
                // When we add more custom audits, `weight` controls how they're averaged together.
                {id: 'audit-localstorage', weight: 1},
            ],
        },
    },
};

