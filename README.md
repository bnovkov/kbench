# kbench
`kbench` is a FreeBSD benchmarking framework designed for testing kernel changes.
The projects aims to facilitate kernel performance testing and repoducibility of results.
It fetches and runs a set of well-known benchmarks, tracks various system metrics during their runtime, and exports the gathered data for further processing.

# Installing
`kbench` requires Python 3.11 or greater. After cloning the repo, make sure to install the required modules listed in `requirements.txt`.

# Running
To come.

# Contributing
`kbench` currently has a minimal set of features and development is currently focused on adding new benchmarks and metrics. 
You are very welcome to share your way of benchmarking and testing FreeBSD kernel patches by opening an issue or contacting the maintainer.
When opening an issue or contacting the maintainer, please include the following information:
1. A list of benchmarks you use (including an URL to the source files if necessary),
2. A list of metrics you track when benchmarking.
