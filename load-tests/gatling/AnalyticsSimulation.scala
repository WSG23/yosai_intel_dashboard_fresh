import io.gatling.core.Predef._
import io.gatling.http.Predef._
import scala.concurrent.duration._

class AnalyticsSimulation extends Simulation {
  val baseUrl: String = System.getProperty("BASE_URL", "http://localhost:8000")
  val mode: String = System.getProperty("TEST_MODE", "sustained")
  val burstUsers: Int = Integer.getInteger("BURST_USERS", 100)
  val sustainedUsers: Int = Integer.getInteger("SUSTAINED_USERS", 50)
  val burstDuration: Int = Integer.getInteger("BURST_DURATION", 30)
  val sustainedDuration: Int = Integer.getInteger("SUSTAINED_DURATION", 300)

  val httpProtocol = http.baseUrl(baseUrl)

  val scn = scenario("Analytics Journey")
    .exec(http("dashboard").get("/api/v1/analytics/dashboard-summary"))
    .pause(1)
    .exec(http("access").get("/api/v1/analytics/access-patterns"))
    .pause(1)
    .exec(http("threat").get("/api/v1/analytics/threat_assessment"))

  val burstInjection = rampUsers(burstUsers) during (burstDuration seconds)
  val sustainedInjection = constantConcurrentUsers(sustainedUsers) during (sustainedDuration seconds)

  val setup = mode match {
    case "burst" => scn.inject(burstInjection, sustainedInjection)
    case _ => scn.inject(sustainedInjection)
  }

  setUp(setup).protocols(httpProtocol)
}
