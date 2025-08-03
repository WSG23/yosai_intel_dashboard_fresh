# RASP / Application Firewall Evaluation

The current codebase does not include a runtime application self-protection
(RASP) or embedded web application firewall. Lightweight options such as
[pyRASP](https://github.com) or wrapping the application with a WAF like
[modsecurity] were evaluated.

Given the deployment constraints, integrating a library that instruments
Python bytecode dynamically (e.g. pyRASP) would introduce overhead and
complexity. A pragmatic approach is to deploy Nginx with ModSecurity in front
of the services to provide request filtering and anomaly detection while
keeping the application layer lightweight. Further evaluation and benchmarking
are recommended before full integration.
