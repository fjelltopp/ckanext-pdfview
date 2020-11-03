import pylons.config as config
import urlparse
import pytest
import ckan.model as model
import ckan.plugins as plugins
import ckan.lib.helpers as h
import ckanext.pdfview.plugin as plugin
import ckan.lib.create_test_data as create_test_data

try:
    import ckan.tests.legacy as tests
except ImportError:
    # CKAN <= 2.3
    import ckan.tests as tests


def _create_test_view():
    context = {'model': model,
               'session': model.Session,
               'user': model.User.get('testsysadmin').name}

    package = model.Package.get('annakarenina')
    resource_id = package.resources[1].id
    resource_view = {'resource_id': resource_id,
                     'view_type': 'pdf_view',
                     'title': u'Test View',
                     'description': u'A *nice* test view'}
    resource_view = plugins.toolkit.get_action('resource_view_create')(
        context, resource_view)
    return resource_view, package, resource_id


@pytest.fixture
def pdf_view_plugin():
    p = plugin.PdfView()
    p.proxy_is_enabled = False
    create_test_data.CreateTestData.create()
    return p


@pytest.mark.ckan_config(u'ckan.plugins', u'pdf_view')
@pytest.mark.ckan_config(u'ckan.legacy_templates', u'false')
@pytest.mark.usefixtures(u'with_plugins', u'with_request_context',
                         u'app', u'clean_db', 'pdf_view_plugin')
class TestPdfView(tests.WsgiAppCase):
    view_type = 'pdf_view'

    def test_can_view(self, app, pdf_view_plugin):
        url_same_domain = urlparse.urljoin(
            config.get('ckan.site_url', '//localhost:5000'),
            '/resource.txt')
        url_different_domain = 'http://some.com/resource.pdf'

        data_dict = {'resource': {'format': 'pdf', 'url': url_same_domain}}
        assert pdf_view_plugin.can_view(data_dict)

        data_dict = {'resource': {'format': 'x-pdf', 'url': url_same_domain}}
        assert pdf_view_plugin.can_view(data_dict)

        data_dict = {'resource': {'format': 'pdf',
                                  'url': url_different_domain}}
        assert not pdf_view_plugin.can_view(data_dict)

    def test_js_included(self, app, pdf_view_plugin):
        resource_view, package, resource_id = _create_test_view()
        url = h.url_for('resource.view',
                        id=package.name, resource_id=resource_id,
                        view_id=resource_view['id'])
        result = app.get(url)
        print(result.body)
        assert (('_pdfview.js' in result.body) or
                ('_pdfview.min.js' in result.body))

    def test_css_included(self, app, pdf_view_plugin):
        resource_view, package, resource_id = _create_test_view()
        url = h.url_for('resource.view',
                        id=package.name, resource_id=resource_id,
                        view_id=resource_view['id'])
        result = app.get(url)
        print(result.body)
        assert (('_pdfview.css' in result.body) or
                ('_pdfview.min.css' in result.body))

    def test_title_description_iframe_shown(self, app, pdf_view_plugin):
        resource_view, package, resource_id = _create_test_view()
        url = h.url_for('resource.read',
                        id=package.name, resource_id=resource_id)
        result = app.get(url)
        assert resource_view['title'] in result
        assert 'data-module="data-viewer"' in result.body

    def test_description_supports_markdown(self, app, pdf_view_plugin):
        resource_view, package, resource_id = _create_test_view()
        url = h.url_for('resource.read',
                        id=package.name, resource_id=resource_id)
        result = app.get(url)
        assert 'A <em>nice</em> test view' in result
