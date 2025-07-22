package com.example

import io.gatling.core.Predef._
import io.gatling.http.Predef._

class ApiGatewaySimulation extends Simulation {
  val httpProtocol = http.baseUrl("http://localhost:8080")

  val scn = scenario("Gateway load")
    .exec(http("health").get("/health"))
    .pause(1)

  setUp(
    scn.inject(constantUsersPerSec(50).during(60))
  ).protocols(httpProtocol)
}
