from locust import HttpUser, between, task

class ClipTest(HttpUser):
    wait_time = between(1, 2)
    @task
    def post_image(self):
        headers = {
            "serve_multiplexed_model_id": "openai/clip-vit-base-patch32"
        }
        payload = {
            "image_url": "https://c02.purpledshub.com/uploads/sites/41/2024/08/Cats-vs-dogs-whos-smarter.jpg?w=1029&webp=1"
        }
        self.client.post("/clip", json=payload, headers=headers)

class TranslateTest(HttpUser):

    @task
    def translate_text(self):
        # headers = {
        #     "serve_multiplexed_model_id": "translation-model-id"  # Update with your actual translation model ID
        # }
        payload = {
            "text": "Cô cho biết: trước giờ tôi không đến phòng tập công cộng, mà tập cùng giáo viên Yoga riêng hoặc tự tập ở nhà."
        }
        self.client.post("/vi2en", json=payload, 
                        #  headers=headers
                         )

