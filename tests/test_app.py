import falcon
from falcon import testing
import msgpack
import pytest
from unittest.mock import mock_open, call

from look.app import api

@pytest.fixture
def client():
    return testing.TestClient(api)

# pytest will inject the object returned by the "client" function
# as an additional parameter.
def test_list_images(client):
    doc = {
        'images': [
            {
                'href': '/images/1eaf6ef1-7f2d-4ecc-a8d5-6e8adba7cc0e.png'
            }
        ]
    }

    response = client.simulate_get('/images')
    result_doc = msgpack.unpackb(response.content, encoding='utf-8')

    assert result_doc == doc
    assert response.status == falcon.HTTP_OK

# "monkeypatch" is a  special built-in pytest fixture that can be
# used to install mocks.
def test_posted_image_gets_saved(client, monkeypatch):
    mock_file_open = mock_open()
    monkeypatch.setattr('io.open', mock_file_open)

    fake_uuid = '123e4567-e89b-12d3-a456-426655440000'
    monkeypatch.setattr('uuid.uuid4', lambda: fake_uuid)

    # when the service receives an image through POST...
    fake_image_bytes = b'fake-image-bytes'
    response = client.simulate_post(
        '/images',
        body=fake_image_bytes,
        headers={'content-type': 'image/png'}
    )

    # ...it must return 201 and resource location
    assert response.status == falcon.HTTP_CREATED
    assert call().write(fake_image_bytes) in mock_file_open.mock_calls
    assert response.headers['location'] == '/images/{}.png'.format(fake_uuid)



