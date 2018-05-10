import io
import falcon
from falcon import testing
import msgpack
import pytest
from unittest.mock import mock_open, call, MagicMock

import look.app
import look.images

@pytest.fixture
def mock_store():
    MagickMock()

@pytest.fixture
def client(mock_store):
    api = look.app.create_app(mock_store)
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
# def test_posted_image_gets_saved(client, monkeypatch):
#     mock_file_open = mock_open()
#     monkeypatch.setattr('io.open', mock_file_open)
#
#     fake_uuid = '123e4567-e89b-12d3-a456-426655440000'
#     monkeypatch.setattr('uuid.uuid4', lambda: fake_uuid)
#
#     # when the service receives an image through POST...
#     fake_image_bytes = b'fake-image-bytes'
#     response = client.simulate_post(
#         '/images',
#         body=fake_image_bytes,
#         headers={'content-type': 'image/png'}
#     )
#
#     # ...it must return 201 and resource location
#     assert response.status == falcon.HTTP_CREATED
#     assert call().write(fake_image_bytes) in mock_file_open.mock_calls
#     assert response.headers['location'] == '/images/{}.png'.format(fake_uuid)

# With clever composition of fixtures, we can observe what happens with
# the mock injected into the image resource.
def test_post_image(client, mock_store):
    file_name = 'fake-image-name.xyz'

    # we need to know what ImageStore method will be used
    mock_store.save.return_value = file_name
    image_content_type = 'image/xyz'

    response = client.simulate_post(
        '/images',
        body=b'some-fake-bytes',
        headers={'content-type': image_content_type}
    )

    assert response.status == falcon.HTTP_CREATED
    assert response.headers['location'] == '/images/{}'.format(file_name)
    saver_call = mock_store.save.call_args

    # saver_call is a unittest.mock.call tuple with first element
    # as a tuple of positional arguments supplied when calling the mock.
    assert isinstance(saver_call[0][0], falcon.request_helpers.BoundedStream)
    assert saver_call[0][1] == image_content_type

    def test_saving_image(monkeypatch):
        # this still has some mocks, but they are more localized
        # and do not have to be monkeypatched into standard library modules
        mock_file_open = mock_open()
        
        fake_uuid = '123e4567-e89b-12d3-a456-426655440000'
        def mock_uuidgen():
            return fake_uuid

        fake_image_bytes = b'fake-image-bytes'
        fake_request_stream = io.BytesIO(fake_image_bytes)
        storage_path = 'fake-storage-path'
        store = look.images.ImageStore(
            storage_path,
            uuidgen=mock_uuidgen,
            fopen=mock_file_open
        )

        assert store.save(fake_request_stream, 'image/png') == fake_uuid + '.png'
        assert call().write(fake_image_bytes) in mock_file_open.mock_calls
