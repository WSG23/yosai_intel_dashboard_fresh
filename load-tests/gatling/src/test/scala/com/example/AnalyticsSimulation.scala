package com.example

import io.gatling.core.Predef._
import io.gatling.http.Predef._

class AnalyticsSimulation extends Simulation {
  val httpProtocol = http.baseUrl("http://localhost:8001")

  val scn = scenario("Analytics load")
    .exec(http("query").get("/analytics?q=latest"))
    .pause(1)

  setUp(
    scn.inject(constantUsersPerSec(30).during(60))
  ).protocols(httpProtocol)
}
