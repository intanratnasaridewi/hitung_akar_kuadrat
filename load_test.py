from locust import HttpUser, task, between

class MyUser(HttpUser):
    wait_time = between(1, 5)  # Time between requests in seconds

    @task
    def hitung_akar_kuadrat(self):
        # Define the payload for your API request
        payload = {"angka": 16}  # You may adjust the value accordingly

        # Make a POST request to your API endpoint
        response = self.client.post("https://kelompok-11-ppl-x7kxkrodya-et.a.run.app/api/hitung-akar-kuadrat-api", json=payload)

        # Print the response content (optional)
        print(response.content)

# Run Locust using the following command in your terminal:
# locust -f your_script_name.py
