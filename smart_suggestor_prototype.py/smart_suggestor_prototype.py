

import random

def classify_phase(query):
    if "why" in query.lower() or "reason" in query.lower():
        return "Investigate"
    elif any(word in query.lower() for word in ["how", "optimize", "reduce", "suggest"]):
        return "Implement"
    elif any(word in query.lower() for word in ["impact", "result", "effect", "evaluate"]):
        return "Evaluate"
    else:
        return "Discover"

def process_query(phase, query):
    if phase == "Discover":
        return "🚨 Alert: Anomaly detected in HVAC Unit 3. You can investigate it for deeper insights."
    elif phase == "Investigate":
        return ("🔍 Based on past logs, the increase in vibration was due to filter clogging. "
                "Recommend checking sensor logs and maintenance tickets from last 48 hours.")
    elif phase == "Implement":
        return ("🛠️ Suggestion: Schedule a check for Pump A using QR-scan checklist. "
                "Assign task to on-ground technician via OpsManager.")
    elif phase == "Evaluate":
        return ("📈 Evaluation: Your last maintenance action reduced energy usage by 8% "
                "and improved MTBF. Great job!")
    else:
        return "🤖 I'm not sure how to respond. Please rephrase your request."

def main():
    print("Welcome to Smart Suggestor AI (Xempla Prototype)")
    print("------------------------------------------------\n")

    while True:
        user_query = input("🔎 Ask me something (or type 'exit' to quit):\n> ")
        if user_query.strip().lower() == "exit":
            print("👋 Exiting Smart Suggestor. Have a productive day!")
            break

        phase = classify_phase(user_query)
        print(f"\n📘 Classified Phase: {phase}")
        response = process_query(phase, user_query)
        print(f"💬 Suggestor: {response}\n")

if __name__ == "__main__":
    main()
