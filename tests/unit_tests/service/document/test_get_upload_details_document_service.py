import app.service.document as doc_service


def test_document_service_get_upload_details(test_s3_client, monkeypatch):
    monkeypatch.setenv("CDN_URL", "https://cdn.climatepolicyradar.org")
    monkeypatch.setenv("CACHE_BUCKET", "test-document-bucket")

    result = doc_service.get_upload_details("path/file.ext", True)
    assert result is not None
    assert len(result) == 2
    # Check the signed url starts with the right path

    first_result = str(result[0])
    assert first_result.startswith(
        "https://test-document-bucket.s3.amazonaws.com/path/file.ext?"
    )
    assert "X-Amz-Algorithm" in first_result
    assert "X-Amz-Credential" in first_result
    assert "X-Amz-Date" in first_result
    assert "X-Amz-Expires=3600" in first_result
    assert "X-Amz-Signature" in first_result

    assert str(result[1]) == "https://cdn.climatepolicyradar.org/path/file.ext"
