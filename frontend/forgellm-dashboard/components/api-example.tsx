"use client";

import { useState } from "react";
import { Copy, Check } from "lucide-react";

export function ApiExample({ modelName = "customer-support" }: { modelName?: string }) {
  const [copied, setCopied] = useState(false);
  const [language, setLanguage] = useState<"cURL" | "Python" | "JavaScript">("cURL");

  const examples = {
    cURL: `curl https://api.forgellm.com/v1/chat/completions \\
  -H "Authorization: Bearer $FORGELLM_API_KEY" \\
  -H "Content-Type: application/json" \\
  -d '{
    "model": "${modelName}",
    "messages": [
      {
        "role": "user",
        "content": "How do I return an order?"
      }
    ]
  }'`,
    Python: `import os
from openai import OpenAI

client = OpenAI(
    api_key=os.environ.get("FORGELLM_API_KEY"),
    base_url="https://api.forgellm.com/v1"
)

response = client.chat.completions.create(
    model="${modelName}",
    messages=[
        {"role": "user", "content": "How do I return an order?"}
    ]
)
print(response.choices[0].message.content)`,
    JavaScript: `import OpenAI from 'openai';

const client = new OpenAI({
  apiKey: process.env['FORGELLM_API_KEY'],
  baseURL: 'https://api.forgellm.com/v1'
});

async function main() {
  const response = await client.chat.completions.create({
    model: '${modelName}',
    messages: [{ role: 'user', content: 'How do I return an order?' }],
  });
  console.log(response.choices[0].message.content);
}
main();`
  };

  const code = examples[language];

  const handleCopy = () => {
    navigator.clipboard.writeText(code);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="rounded-xl border border-neutral-800 bg-[#0A0A0A] overflow-hidden">
      <div className="flex justify-between items-center bg-neutral-900 border-b border-neutral-800 px-4 py-2">
        <div className="flex gap-2">
          {(Object.keys(examples) as Array<keyof typeof examples>).map(lang => (
            <button
              key={lang}
              onClick={() => setLanguage(lang)}
              className={`px-3 py-1 text-xs font-medium rounded ${language === lang ? 'bg-neutral-800 text-white' : 'text-neutral-400 hover:text-white hover:bg-neutral-800/50'}`}
            >
              {lang}
            </button>
          ))}
        </div>
        <button
          onClick={handleCopy}
          className="p-1.5 text-neutral-400 hover:text-white hover:bg-neutral-800 rounded transition-colors"
          title="Copy code"
        >
          {copied ? <Check className="w-4 h-4 text-emerald-500" /> : <Copy className="w-4 h-4" />}
        </button>
      </div>
      <div className="p-4 overflow-x-auto">
        <pre className="text-sm font-mono text-neutral-300">
          <code>{code}</code>
        </pre>
      </div>
    </div>
  );
}
