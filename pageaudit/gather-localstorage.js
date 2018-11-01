'use strict';

const Gatherer = require('lighthouse').Gatherer;

/**
 * @fileoverview Extracts `window.localStorage/sessionStorage` from the test page.
 */

class LocalStorageGather extends Gatherer {
  afterPass(options) {
    const driver = options.driver;

    return driver.evaluateAsync('window.localStorage')
      // Ensure returned value is what we expect.
      .then(localStorage => {
        if (!localStorage) {
          // Throw if page didn't provide the metrics we expect. This isn't
          // fatal -- the Lighthouse run will continue, but any audits that
          // depend on this gatherer will show this error string in the report.
          throw new Error('Unable to find localStorage in page');
        }
        return localStorage;
      });
  }
}

module.exports = LocalStorageGather;
