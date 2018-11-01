'use strict';

const Audit = require('lighthouse').Audit;

class LocalStorageAudit extends Audit {
    static get meta() {
        return {
            id: 'localstorage',
            title: 'localStorage in use',
            failureTitle: 'LocalStorage is employed by page',
            description: 'LocalStorage is deprecated and should be avoided as it is a cause of blocking I/O',

            // The name of the custom gatherer class that provides input to this audit.
            requiredArtifacts: ['LocalStorageGather'],
        };
    }

    static audit(artifacts) {
        const storageData = artifacts.localStorage;

        // Audit will pass when the search box loaded in less time than our threshold.
        // This score will be binary, so will get a red ✘ or green ✓ in the report.
        const belowThreshold = storageData.length;

        return {
            rawValue: belowThreshold,
            // Cast true/false to 1/0
            score: Number(belowThreshold),
        };
    }
}

module.exports = LocalStorageAudit;
