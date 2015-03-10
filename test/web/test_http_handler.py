import json

import pytest
from werkzeug.wrappers import Response

from nameko.web.handlers import http


class ExampleService(object):

    @http('GET', '/foo/<int:bar>')
    def do_get(self, bar):
        return 'value: {}'.format(bar)

    @http('POST', '/post')
    def do_post(self, payload):
        data = json.loads(payload)
        value = data['value']

        return value

    @http('GET', '/custom')
    def do_custom(self):
        return Response('response')

    @http('GET', '/status_code')
    def do_status_code(self):
        return 201, 'created'

    @http('GET', '/headers')
    def do_headers(self):
        return 201, {'x-foo': 'bar'}, 'created'

    @http('GET', '/fail')
    def fail(self):
        raise ValueError('oops')

    @http('GET', '/fail_expected', expected_exceptions=ValueError)
    def fail_expected(self):
        raise ValueError('oops')


@pytest.fixture
def web_session(container_factory, web_config, web_session):
    container = container_factory(ExampleService, web_config)
    container.start()
    return web_session


def test_get(web_session):
    rv = web_session.get('/foo/42')
    assert rv.text == 'value: 42'

    rv = web_session.get('/foo/something')
    assert rv.status_code == 404


def test_post(web_session):
    rv = web_session.post('/post', json={
        'value': 'foo',
    })
    assert rv.text == "foo"


def test_custom_response(web_session):
    rv = web_session.get('/custom')
    assert rv.content == 'response'


def test_custom_status_code(web_session):
    rv = web_session.get('/status_code')
    assert rv.text == 'created'
    assert rv.status_code == 201


def test_custom_headers(web_session):
    rv = web_session.get('/headers')
    assert rv.text == 'created'
    assert rv.status_code == 201
    assert rv.headers['x-foo'] == 'bar'


def test_broken_method(web_session):
    rv = web_session.get('/fail')
    assert rv.status_code == 500
    assert "ValueError: oops" in rv.text


def test_broken_method_expected(web_session):
    rv = web_session.get('/fail_expected')
    assert rv.status_code == 400
    assert "ValueError: oops" in rv.text


def test_bad_payload(web_session):
    rv = web_session.post('/post', json={'value': 23})
    assert rv.status_code == 500
    assert "Unserializable value: `23`" in rv.text