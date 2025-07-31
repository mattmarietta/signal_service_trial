import json
from datetime import datetime
from collections import Counter
from classifier import classify_signal

class Logger:
    def __init__(self, output="logs.jsonl"):
        self.output = output

    def write(self, agent_id, user_id, user_input,
              detected_signal=None, response_type="",
              coherence_score_impact=None,
              escalation_flag=False, session_id=None):
        """Write a log entry with optional classification."""
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        detected_signal = detected_signal or classify_signal(user_input)

        data = {
            "timestamp": current_time,
            "agent_id": agent_id,
            "user_id": user_id,
            "user_input": user_input,
            "detected_signal": detected_signal,
            "response_type": response_type,
            "coherence_score_impact": coherence_score_impact,
            "escalation_flag": escalation_flag,
            "session_id": session_id
        }

        with open(self.output, 'a') as f:
            f.write(json.dumps(data) + '\n')

    def read_recent(self, agent_id, user_id, limit=10):
        """Read last `limit` logs for a specific agent-user pair."""
        try:
            with open(self.output, 'r') as f:
                logs = [json.loads(line) for line in f]
        except FileNotFoundError:
            return []

        filtered = [log for log in logs if log['agent_id'] == agent_id and log['user_id'] == user_id]
        return filtered[-limit:]

    def summarize_signals(self, agent_id, user_id):
        """Return frequency of detected signals."""
        recent_logs = self.read_recent(agent_id, user_id, limit=1000)
        signals = [log['detected_signal'] for log in recent_logs]
        return dict(Counter(signals))
