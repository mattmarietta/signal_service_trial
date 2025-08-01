# Signal Logging & Visualization Microservice
<img width="748" height="480" alt="Screenshot 2025-07-31 at 5 00 06 PM" src="https://github.com/user-attachments/assets/8233bc66-e8e8-4e89-97fd-b5268bc99042" />


## Inspiration
Understanding user sentiment during AI-agent interactions is crucial for improving experiences. Many teams collect raw logs but lack tools to **classify signals** (positive, neutral, stressed, uncertain) or **visualize trends** easily.  

This project solves that by providing a **lightweight logging & visualization microservice** with:  
- Automated signal classification  
- REST API for log retrieval & summaries  
- Interactive dashboard for visualization

---

## What It Does
The microservice provides:  
- **Logging** of user-agent interactions into a JSONL file  
- **Signal classification** using simple keyword-based NLP  
- **API endpoints** to fetch recent logs, summaries, and visualizations  
- **Web dashboard** to view signal trends and recent interactions  

Users can:  
1. **POST** logs to the API  
2. **View recent logs** in a table with **emoji and color-coded escalation highlights**  
3. **See a bar chart** of signal frequencies using **Chart.js**  
4. **Monitor conversation sentiment trends**


---

## Tech Stack
- **Backend**: Python, FastAPI, Matplotlib  
- **Frontend**: HTML, CSS (glassmorphism), JavaScript, Chart.js  
- **Storage**: JSON Lines (`logs.jsonl`)  

---

## Features
- **POST** `/log` → Log a new user-agent interaction  
- **GET** `/logs/{agent_id}/{user_id}` → Retrieve the 10 most recent logs  
- **GET** `/summary/{agent_id}/{user_id}` → Get signal frequency (JSON)  
- **GET** `/visualize/{agent_id}/{user_id}` → Generate bar chart (PNG)  
- **Web Dashboard** → Interactive Chart.js + Recent Logs Table

---

## Quick Start

### 1. Install dependencies
pip install fastapi uvicorn matplotlib

### 2. Run the API
uvicorn api:app --reload

### 3.  Test with curl
curl -X POST http://127.0.0.1:8000/log \
-H "Content-Type: application/json" \
-d '{"agent_id":"agent1","user_id":"user1","user_input":"I am so stressed"}'

### 4. Open the Dashboard
- Open static/index.html in your browser
- Enter Agent ID and User ID, click Refresh
- See updated signal chart and recent logs table

---

## Project Structure
<img width="458" height="205" alt="Screenshot 2025-07-31 at 4 58 14 PM" src="https://github.com/user-attachments/assets/124d7e99-e169-4adf-b31b-91645822b69a" />

---

## Contributors
Vy Vuong (Trial Assignment Project)
