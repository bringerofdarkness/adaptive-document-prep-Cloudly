from qdrant_client import QdrantClient

client = QdrantClient(url="http://localhost:16433")
records, _ = client.scroll(collection_name="slatefall_chunks", limit=1)

if records:
    print("\n🎯 --- ACTUAL QDRANT PAYLOAD FOUND --- 🎯")
    print(records[0].payload)
    print("----------------------------------------\n")
else:
    print("❌ Collection is empty.")