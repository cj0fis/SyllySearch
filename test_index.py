import math, os, tempfile
from search_engine import tokenize, BM25FIndex, SyllySearch, demo_engine, parse_query

print("1) tokenizer")
print("  ", tokenize("CSCE 221: Data Structures and the Algorithms"))
assert "csce221" in tokenize("csce-221") and "the" not in tokenize("the cat")

eng = demo_engine()
idx = eng.index
print("2) index stats")
print("   docs:", len(idx.docs), "| unique terms:", len(idx.postings))
print("   avg field lengths:", {k: round(v, 2) for k, v in idx.avg_len.items()})

print("3) postings for 'trees' and 'csce221'")
for t in ("trees", "csce221"):
    print("  ", t, "->", {idx.docs[i]["id"]: tf for i, tf in idx.postings[t].items()})

print("4) idf: rarer term should score higher")
print("   idf(haskell)=%.3f  idf(csce)=%.3f" % (idx._idf("haskell"), idx._idf("csce")))
assert idx._idf("haskell") > idx._idf("csce")

print("5) BM25F hand-check for doc 3 / term 'haskell'")
i = next(n for n, d in enumerate(idx.docs) if d["id"] == 3)
tfs = idx.postings["haskell"][i]
tf_t = sum(idx.w[f]*tf/(1-idx.b[f]+idx.b[f]*idx.field_len[i][f]/idx.avg_len[f]) for f, tf in tfs.items())
manual = idx._idf("haskell") * tf_t / (idx.k1 + tf_t)
got = dict(idx.search("haskell"))[i]
print("   manual=%.6f  engine=%.6f" % (manual, got)); assert abs(manual-got) < 1e-9

print("6) ranking sanity")
for q in ("haskell", "data structures", "csce 221", "vector calculus"):
    print("  ", q, "->", [(idx.docs[i]["id"], round(s, 2)) for i, s in idx.search(q)[:3]])

print("7) filters restrict candidates")
print("   ", parse_query("easy 300 level csce course", ["CSCE"]))
D = ["CSCE", "MATH"]
for q, exp in [("easy 300 level csce course", dict(intent="easy", level=3, dept="CSCE", course=None, text="")),
               ("best csce 221 professor", dict(intent="good", level=None, dept=None, course=("CSCE", "221"), text="")),
               ("hard math 400 level", dict(intent="hard", level=4, dept="MATH", course=None, text="")),
               ("machine learning", dict(intent=None, level=None, dept=None, course=None, text="machine learning")),
               ("csce 221 trees", dict(intent=None, level=None, dept=None, course=("CSCE", "221"), text="trees"))]:
    got = parse_query(q, D); print("   ", q, "->", got); assert got == exp, (q, got)

print("8) save/load roundtrip")
p = os.path.join(tempfile.mkdtemp(), "idx.pkl"); eng.save(p)
e2 = SyllySearch.load(p)
assert idx.search("trees") == e2.index.search("trees")
print("   OK, file size %d bytes" % os.path.getsize(p))

print("9) empty / unknown query")
print("   ", idx.search("zzzzqqq"), idx.search(""))
print("ALL PASSED")