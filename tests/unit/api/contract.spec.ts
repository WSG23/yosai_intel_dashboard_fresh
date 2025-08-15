import axios from "axios";

test("health returns 200", async () => {
  const res = await axios.get(process.env.API_URL + "/health");
  expect(res.status).toBe(200);
});
