# Page Lab

Web Page Performance Laboratory: Scaling [Lighthouse](https://github.com/GoogleChrome/Lighthouse "Google Lighthouse") performace and web testing tools

* This is Alpha software and needs some testing and automation. PR's are accepted!

## Page Lab is an attempt at understanding web performace at scale

The goals here are 3-fold:

## Understand page performance now (and provide a historical record)

* Easy automated Lighthouse tests of any URL
* A history of each test run, for as many runs as desired
* Historical data will allow us to track performance of our pages over time, giving us insight into when changes cause performance regressions
* Coupled with the Web Timing API, Page Lab will be able to drill into any included scripts (properly instrumented) and understand what EXACTLY is impacting page performance

## Get started

### Setup Django 'Heads Up Display' dashboard

* see: [Django README](admin/pageaudit/README.md "Django README")

### Setup Node testing server

* see: [node README](pageaudit/README.md "Node README")

## Roadmap & Ideas

### Automate _some_ fixes for pages

* For instance, being able to tell developers that certain scripts are not even used on the page
* Automation of image compression to the proper smaller size
* Automatically give guidance on which assets can be preloaded, etc

## Pre-flight check tool for newly published pages

* Developers can run their page through *Pag Lab* and see what can be fixed - some of which will be automated for them, e.g.: compressed web assets, etc
