from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse
from django.conf import settings
from django.core.cache import cache
from rest_framework.test import APIClient
from rest_framework import status


from .models import Category, Post, PostAnalytics, Heading

### MODELS TESTS

class CategoryModelTest(TestCase):
    def setUp(self):
        self.category = Category.objects.create(
            name="Tech",
            title="Technology",
            description="All about technology",
            slug="tech"
        )
    
    def test_category_creation(self):
        self.assertEqual(str(self.category), 'Tech')
        self.assertEqual(self.category.title, 'Technology')


class PostModelTest(TestCase):
    def setUp(self):
        self.category = Category.objects.create(
            name="Tech",
            title="Technology",
            description="All about technology",
            slug="tech"
        )

        self.post = Post.objects.create(
            title="Post 1",
            description="A test post",
            content="Content for the post",
            thumbnail=None,
            keywords="test, post",
            slug="post-1",
            category=self.category,
            status="published"
        )
    
    def test_post_creation(self):
        self.assertEqual(str(self.post), "Post 1")
        self.assertEqual(self.post.category.name, "Tech")
    
    def test_post_published_manager(self):
        self.assertTrue(Post.postobjects.filter(status="published").exists())
    

class PostAnalyticsModelTest(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name="Analytics", slug="analytics")
        self.post = Post.objects.create(
            title="Analytics Post",
            description="Post for analytics",
            content="Analytics content",
            slug="analytics-post",
            category=self.category
        )
        self.analytics = PostAnalytics.objects.create(post=self.post)

    def test_click_through_rate_update(self):
        self.analytics.increment_impression()
        self.analytics.increment_click()
        self.analytics.refresh_from_db()
        self.assertEqual(self.analytics.click_through_rate, 100.0)


class HeadingModelTest(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name="Heading", slug="heading")
        self.post = Post.objects.create(
            title="Post with Headings",
            description="Post containing headings",
            content="Content with headings",
            slug="post-with-headings",
            category=self.category
        )
        self.heading = Heading.objects.create(
            post=self.post,
            title="Heading 1",
            slug="heading-1",
            level=1,
            order=1
        )

    def test_heading_creation(self):
        self.assertEqual(self.heading.slug, "heading-1")
        self.assertEqual(self.heading.level, 1)


# VIEWS TESTS
class PostListViewTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        cache.clear()  # Limpia el caché antes de cada prueba

        self.category = Category.objects.create(name="API", slug="api")
        self.api_key = settings.VALID_API_KEYS[0]
        self.post = Post.objects.create(
            title="API Post",
            description="API post description",
            content="API content",
            slug="api-post",
            category=self.category,
            status="published"
        )

    def tearDown(self):
        cache.clear() 
    
    def test_get_post_list(self):
        url = reverse('post-list')
        response = self.client.get(
            url,
            HTTP_API_KEY=self.api_key
        )

        data = response.json()

        self.assertIn('success', data)
        self.assertTrue(data['success'])
        self.assertIn('status', data)
        self.assertEqual(data['status'], 200)
        self.assertIn('results', data)
        self.assertEqual(data['count'], 1)

        results = data['results']
        self.assertEqual(len(results), 1)

        post_data = results[0]
        self.assertEqual(post_data['id'], str(self.post.id))
        self.assertEqual(post_data['title'], self.post.title)
        self.assertEqual(post_data['description'], self.post.description)
        self.assertIsNone(post_data['thumbnail'])
        self.assertEqual(post_data['slug'], self.post.slug)

        category_data = post_data['category']
        self.assertEqual(category_data['name'], self.category.name)
        self.assertEqual(category_data['slug'], self.category.slug)

        self.assertEqual(post_data['view_count'], 0)

        self.assertIsNone(data['next'])
        self.assertIsNone(data['previous'])


class PostDetailViewTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        cache.clear()

        # Configuración de la API-Key de prueba
        self.api_key = settings.VALID_API_KEYS[0]

        # Crear datos de prueba
        self.category = Category.objects.create(name="Detail Category", slug="detail-category")
        self.post = Post.objects.create(
            title="Detail Post",
            description="Detailed post description",
            content="Detailed content",
            slug="detail-post",
            category=self.category,
            status="published"
        )

    def tearDown(self):
        cache.clear() 
    
    @patch('apps.blog.tasks.increment_post_views_task.delay')
    def test_get_post_detail_success(self, mock_increment_views):
        """
        Test para verificar que se obtienen los detalles de un post existente
        y que la tarea de incremento de vistas se ejecuta correctamente.
        """
        # Ruta hacia la vista con query parameter 'slug'
        url = reverse('post-detail') + f"?slug={self.post.slug}"

        # Simula una solicitud GET con encabezado API-Key
        response = self.client.get(
            url,
            HTTP_API_KEY=self.api_key
        )

        # Verifica el estado de la respuesta
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Decodifica la respuesta JSON
        data = response.json()

        # Verifica el formato de la respuesta
        self.assertIn('success', data)
        self.assertTrue(data['success'])
        self.assertIn('status', data)
        self.assertEqual(data['status'], 200)
        self.assertIn('results', data)

        post_data = data['results']

        self.assertEqual(post_data['id'], str(self.post.id))
        self.assertEqual(post_data['title'], self.post.title)
        self.assertEqual(post_data['description'], self.post.description)
        self.assertIsNone(post_data['thumbnail'])
        self.assertEqual(post_data['slug'], self.post.slug)

        # Verifica los detalles de la categoría
        category_data = post_data['category']
        self.assertEqual(category_data['name'], self.category.name)
        self.assertEqual(category_data['slug'], self.category.slug)

        # Verifica que el conteo de vistas sea inicial (0)
        self.assertEqual(post_data['view_count'], 0)

        mock_increment_views.assert_called_once_with(self.post.slug, '127.0.0.1')  # IP predeterminada en tests

    @patch('apps.blog.tasks.increment_post_views_task.delay')
    def test_get_post_detail_not_found(self, mock_increment_views):
        """
        Test para verificar que se devuelve un error 404 si el post no existe.
        """
        # Ruta hacia la vista con un slug inexistente
        url = reverse('post-detail') + "?slug=non-existent-slug"

        # Simula una solicitud GET con encabezado API-Key
        response = self.client.get(
            url,
            HTTP_API_KEY=self.api_key
        )

        # Verifica el estado de la respuesta
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        # Decodifica la respuesta JSON
        data = response.json()

        # Verifica el mensaje de error
        self.assertIn('detail', data)
        self.assertEqual(data['detail'], "The requested post does not exist")


class PostHeadingsViewTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        cache.clear()

        # Configuración de la API-Key de prueba
        self.api_key = settings.VALID_API_KEYS[0]

        # Crear datos de prueba
        self.category = Category.objects.create(name="Test Category", slug="test-category")
        self.post = Post.objects.create(
            title="Post with Headings",
            description="Post with multiple headings",
            content="Content",
            slug="post-with-headings",
            category=self.category,
            status="published"
        )
        self.heading1 = Heading.objects.create(
            post=self.post,
            title="Heading 1",
            slug="heading-1",
            level=1,
            order=1
        )
        self.heading2 = Heading.objects.create(
            post=self.post,
            title="Heading 2",
            slug="heading-2",
            level=2,
            order=2
        )

    def tearDown(self):
        cache.clear() 
    
    def test_get_post_headings_success(self):
        """
        Test para obtener encabezados de un post existente.
        """
        url = reverse('post-headings') + f"?slug={self.post.slug}"

        response = self.client.get(
            url,
            HTTP_API_KEY=self.api_key
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()

        self.assertTrue(data['success'])
        self.assertEqual(data['status'], 200)
        self.assertIn('results', data)

        # Verificar los encabezados
        results = data['results']
        self.assertEqual(len(results), 2)

        self.assertEqual(results[0]['title'], self.heading1.title)
        self.assertEqual(results[0]['slug'], self.heading1.slug)
        self.assertEqual(results[0]['level'], self.heading1.level)

        self.assertEqual(results[1]['title'], self.heading2.title)
        self.assertEqual(results[1]['slug'], self.heading2.slug)
        self.assertEqual(results[1]['level'], self.heading2.level)

    def test_get_post_headings_not_found(self):
        """
        Test para verificar que no se encuentran encabezados para un slug inexistente.
        """
        url = reverse('post-headings') + "?slug=non-existent-slug"

        response = self.client.get(
            url,
            HTTP_API_KEY=self.api_key
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()

        self.assertTrue(data['success'])
        self.assertEqual(data['status'], 200)
        self.assertEqual(len(data['results']), 0)


class IncrementPostClickViewTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        cache.clear()

        self.api_key = settings.VALID_API_KEYS[0]

        self.category = Category.objects.create(name="Analytics Category", slug="analytics-category")
        self.post = Post.objects.create(
            title="Post for Analytics",
            description="Post description",
            content="Content",
            slug="post-for-analytics",
            category=self.category,
            status="published"
        )

    def tearDown(self):
        cache.clear() 
    
    def test_increment_post_click_success(self):
        """
        Test para incrementar clics exitosamente.
        """
        url = reverse('increment-post-click')

        response = self.client.post(
            url,
            {"slug": self.post.slug},
            HTTP_API_KEY=self.api_key,
            format='json'
        )

        # Verifica el estado de la respuesta
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Decodifica la respuesta JSON
        data = response.json()

        # Verifica la estructura de la respuesta
        self.assertIn('success', data)
        self.assertTrue(data['success'])
        self.assertIn('status', data)
        self.assertEqual(data['status'], 200)
        self.assertIn('results', data)

        # Verifica el contenido de los resultados
        results = data['results']
        self.assertIn('message', results)
        self.assertEqual(results['message'], "Click incremented successfully")
        self.assertIn('clicks', results)

        # Verifica que los clics han incrementado correctamente
        self.assertEqual(results['clicks'], 1)  # El contador debe ser 1 en la primera llamada

        # Verifica el estado del modelo `PostAnalytics`
        from apps.blog.models import PostAnalytics
        post_analytics = PostAnalytics.objects.get(post=self.post)
        self.assertEqual(post_analytics.clicks, 1)