import pytest


@pytest.mark.asyncio
async def test_query_service(fake_services):
    qs = fake_services["query_service"]
    result = await qs.run_query("test query")

    assert "final_answer" in result
    assert "retrieved_docs" in result
    assert result["final_answer"].startswith("Answer for:")
