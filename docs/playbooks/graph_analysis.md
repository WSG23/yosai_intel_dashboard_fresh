# Graph Analysis Playbook

This playbook outlines common workflows for leveraging graph analytics when
investigating security incidents.

1. **Build a Graph from Logs** – Use `analytics.graph_analysis.etl.build_graph_from_logs`
   to transform access logs into a graph model.
2. **Identify High-Risk Nodes** – Run `betweenness_centrality` or
   `risk_propagation` from `analytics.graph_analysis.algorithms` to spot
   influential devices and users.
3. **Export to Threat Feeds** – Use the STIX/TAXII exporter in
   `core.integrations` to share findings with external tools or SIEM systems.
4. **Automate Monitoring** – Incorporate the Kafka streaming helper
   to update graphs in real time and trigger alerts when suspicious patterns
   emerge.
