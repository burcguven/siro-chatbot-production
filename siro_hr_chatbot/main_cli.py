from rag.pipeline import chat_with_rag

history = []

print("🛡 SIRO HR ASİSTANI")
print("=========================\n")

while True:
    q = input("👤 Soru: ")
    if q.lower() in ["q", "exit", "çık"]:
        break
    if not q.strip():
        continue

    answer = chat_with_rag(q, history, debug=True)  # burada debug=True

    print("\n🤖 Asistan:", answer, "\n")

    history.append((q, answer))