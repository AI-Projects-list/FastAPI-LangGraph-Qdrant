import pytest


@pytest.mark.asyncio
async def test_ingest_and_list(fake_services):
    ds = fake_services["document_service"]
    es = fake_services["embeddings"]

    doc_id = await ds.ingest_document("Hello world", {"tag": "test"})
    vector = es.embed("Hello world")
    payload = {"content": "Hello world", "metadata": {"tag": "test"}, "ingested_at": "now"}

    await ds.ingest_with_vector(doc_id, vector, payload)

    docs = await ds.list_documents()
    assert len(docs) == 1
    assert docs[0]["id"] == doc_id


@pytest.mark.asyncio
async def test_delete(fake_services):
    ds = fake_services["document_service"]
    es = fake_services["embeddings"]

    doc_id = await ds.ingest_document("Doc", {})
    vector = es.embed("Doc")
    payload = {"content": "Doc", "metadata": {}, "ingested_at": "now"}

    await ds.ingest_with_vector(doc_id, vector, payload)
    await ds.delete_document(doc_id)

    docs = await ds.list_documents()
    assert len(docs) == 0
