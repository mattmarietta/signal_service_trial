import requests
import random
import time

url = "http://127.0.0.1:8000/log"

agents = ["agent1", "agent2"]
users = ["user1", "user2", "user3"]

sample_inputs = {
    "stressed": [
        "I am so frustrated with this process",
        "This is really stressful",
        "Why is this not working?",
        "I feel upset and angry right now"
    ],
    "uncertain": [
        "Hmm, I’m not sure what to do",
        "Maybe this will work?",
        "I feel confused about this step",
        "Not sure if I clicked the right button"
    ],
    "positive": [
        "Thanks, that really helped!",
        "I am happy with this solution",
        "This is awesome, appreciate your help",
        "Great job, everything works now!"
    ],
    "neutral": [
        "Okay, I clicked submit",
        "I just entered my email",
        "I am testing the system",
        "Normal message without any emotion"
    ]
}

def generate_random_log():
    signal = random.choice(list(sample_inputs.keys()))
    user_input = random.choice(sample_inputs[signal])
    log_data = {
        "agent_id": random.choice(agents),
        "user_id": random.choice(users),
        "user_input": user_input
    }
    r = requests.post(url, json=log_data)
    print(r.json())

# Generate 30 diverse logs
for _ in range(30):
    generate_random_log()
    time.sleep(0.1)  # small delay to get unique timestamps
