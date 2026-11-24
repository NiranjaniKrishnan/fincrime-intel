import duckdb
from anthropic import Anthropic
from dotenv import load_dotenv

# 1. Open the pocket and set up the phone
load_dotenv()
client = Anthropic()

# 2. Take the newest fincrime story out of the filing cabinet
con = duckdb.connect("fincrime.duckdb", read_only=True)
title, body = con.execute("""
    SELECT title, body_text
    FROM int_doj_fincrime_candidates
    ORDER BY release_date DESC
    LIMIT 1
""").fetchone()
con.close()

# 3. Ask Claude about it
message = client.messages.create(
    model="claude-haiku-5-5",
    max_tokens=1000,
    messages=[
        {
            "role": "user",
            "content": (
                "Summarize this DOJ press release in 2 sentences "
                "for a financial crime compliance analyst.\n\n"
                f"Title: {title}\n\n{body}"
            ),
        }
    ],
)

# 4. Show the result
reply = next(block.text for block in message.content if block.type == "text")

print("STORY:  ", title)
print("\nCLAUDE: ", reply)
print("\nTOKENS: ", message.usage.input_tokens, "in /", message.usage.output_tokens, "out")