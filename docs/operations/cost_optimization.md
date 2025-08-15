# Cost Optimization Initiatives

To manage infrastructure spend while maintaining reliability, the following initiatives are in progress:

## Spot/Preemptible Nodes and Autoscaling
- Pilot workloads on spot or preemptible nodes where interruption is acceptable.
- Couple spot usage with autoscaling policies to maintain necessary capacity.

## Per-Service Cost Metrics
- Instrument each service with cost-related metrics (CPU, memory, network, storage).
- Export metrics to dashboards to track cost trends and identify outliers.

## Rightsizing Resources
- Review resource requests and limits regularly using actual usage data.
- Adjust requests/limits to match observed utilization and reduce over-provisioning.

These steps help ensure efficient resource usage and provide visibility into the cost profile of each service.
