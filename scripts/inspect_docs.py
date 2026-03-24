import json
docs = json.load(open('vector_index/documents.json', 'r', encoding='utf-8'))
print(f"Total docs: {len(docs)}")
if docs:
    print(f"Sample keys: {list(docs[0].keys())}")
    for d in docs[:15]:
        did = d.get("id", "?")
        char = d.get("character", "?")
        dtype = d.get("type", "?")
        title = d.get("title", "?")
        tlen = len(d.get("text", ""))
        print(f"  {did}: char={char}, type={dtype}, title={title}, text_len={tlen}")
    print("\n--- Type distribution ---")
    types = {}
    chars = {}
    for d in docs:
        t = d.get("type", "?")
        c = d.get("character", "?")
        types[t] = types.get(t, 0) + 1
        chars[c] = chars.get(c, 0) + 1
    for t, cnt in sorted(types.items()):
        print(f"  {t}: {cnt}")
    print("\n--- Character distribution ---")
    for c, cnt in sorted(chars.items()):
        print(f"  {c}: {cnt}")
    print("\n--- Text length stats ---")
    lengths = [len(d.get("text", "")) for d in docs]
    print(f"  min={min(lengths)}, max={max(lengths)}, avg={sum(lengths)//len(lengths)}, median={sorted(lengths)[len(lengths)//2]}")
