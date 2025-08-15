from locust import HttpUser, task, between


class UploadUser(HttpUser):
    """Minimal load test hitting the upload endpoint."""

    wait_time = between(1, 3)

    @task
    def upload_file(self):
        data = {"file": ("data.csv", "a,b\n1,2\n")}
        self.client.post("/api/v1/upload", files=data)
