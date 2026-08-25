import json
import os
import random

# Synthetic data generation for Customer Support fine-tuning
intent_templates = [
    {
        "intent": "refund",
        "inputs": [
            "I need a refund for my last order.",
            "Can I get my money back?",
            "I am not happy with the product, please refund me.",
            "Cancel my subscription and give me a refund."
        ],
        "outputs": [
            "I'm sorry to hear that you're not satisfied. I've initiated a full refund for your last transaction. You should see it in your account in 3-5 business days.",
            "Certainly, I can help you with that. A refund has been processed to your original payment method. Please allow up to 5 business days for it to appear.",
            "I apologize for the inconvenience. Your refund has been approved and is being processed now."
        ]
    },
    {
        "intent": "technical_issue",
        "inputs": [
            "The app keeps crashing when I open it.",
            "I can't log in to my account.",
            "Why is the website so slow today?",
            "My dashboard is not loading properly."
        ],
        "outputs": [
            "I'm sorry you're experiencing this issue. Let's try clearing your browser cache and cookies, then restarting the application.",
            "Thank you for reporting this. Our engineering team is currently looking into a known issue affecting login. Please try again in 30 minutes.",
            "I understand that's frustrating. Could you please let me know which version of the app you are currently using?"
        ]
    },
    {
        "intent": "billing_question",
        "inputs": [
            "Why was I charged twice this month?",
            "Can you explain this invoice to me?",
            "How do I update my credit card info?",
            "I didn't authorize this charge."
        ],
        "outputs": [
            "I'd be happy to explain. The first charge was a prorated amount for your plan upgrade, and the second is your standard monthly renewal.",
            "To update your billing information, please navigate to Settings > Billing and click on 'Update Payment Method'.",
            "Let me look into that for you. It appears there was a duplicate authorization hold, which should drop off in 24 hours."
        ]
    },
    {
        "intent": "feature_request",
        "inputs": [
            "Do you have a dark mode?",
            "When will you support integration with Slack?",
            "I would love it if I could export my data to CSV.",
            "Can you add a feature to schedule emails?"
        ],
        "outputs": [
            "That's a great suggestion! I've added your vote to this feature request for our product team to review.",
            "We are actually currently working on that! It is scheduled to be released in our next major update in Q3.",
            "While we don't currently support that natively, you can achieve a similar result using our Zapier integration."
        ]
    }
]

def generate_dataset(num_samples=150, output_path="data/raw/customer_support_dataset.jsonl"):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        for _ in range(num_samples):
            template = random.choice(intent_templates)
            input_text = random.choice(template["inputs"])
            output_text = random.choice(template["outputs"])
            
            # OpenAI/Alpaca style instruct format
            record = {
                "instruction": "You are a helpful customer support AI. Respond politely and effectively to the user's inquiry.",
                "input": input_text,
                "output": output_text
            }
            f.write(json.dumps(record) + "\n")
            
    print(f"Successfully generated {num_samples} samples at {output_path}")

if __name__ == "__main__":
    generate_dataset()
