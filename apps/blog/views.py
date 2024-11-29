from rest_framework_api.views import StandardAPIView
from rest_framework.exceptions import NotFound, APIException, ValidationError
from rest_framework import permissions
from django.conf import settings
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.core.cache import cache
from django.db.models import Q, F, Prefetch
from django.shortcuts import get_object_or_404
import redis

from core.permissions import HasValidAPIKey
from .models import (
    Post, 
    Heading, 
    PostAnalytics, 
    Category, 
    CategoryAnalytics, 
    PostView, 
    PostInteraction, 
    Comment,
    PostLike,
    PostShare
)
from .serializers import PostListSerializer, PostSerializer, HeadingSerializer, CategoryListSerializer, CommentSerializer
from utils.ip_utils import get_client_ip
from apps.authentication.models import UserAccount
from apps.media.models import Media
from utils.string_utils import sanitize_string, sanitize_html

from faker import Faker
import random
import uuid
from django.utils.text import slugify


redis_client = redis.StrictRedis(host=settings.REDIS_HOST, port=6379, db=0)


class PostAuthorViews(StandardAPIView):
    permission_classes = [HasValidAPIKey, permissions.IsAuthenticated]

    def get(self, request):
        """
        Enlistar los posts de un autor
        """
        user = request.user
        if user.role == 'customer':
            return self.error("You do not have permission to create posts")
        
        posts = Post.objects.filter(user=user)

        if not posts.exists():
            raise NotFound(detail="No posts found.")
        
        serialized_posts = PostListSerializer(posts, many=True).data

        return self.paginate(request, serialized_posts)

    def post(self, request):
        """
        Crear un post para un autor
        """
        user = request.user
        if user.role == 'customer':
            return self.error("You do not have permission to create posts")

        # Validar campos obligatorios
        required_fields = ["title", "content", "slug", "category"]
        missing_fields = [
            field for field in required_fields if not request.data.get(field)
        ]
        if missing_fields:
            return self.error(f"Missing required fields: {', '.join(missing_fields)}")

        # Obtener parametros
        title = sanitize_string(request.data.get('title', None))
        description = sanitize_string(request.data.get('description', ""))
        content = sanitize_html(request.data.get('content', None))        

        # Thumbnail params
        thumbnail_order = request.data.get("thumbnail_order", None)
        thumbnail_name = request.data.get("thumbnail_name", None)
        thumbnail_size = request.data.get("thumbnail_size", None)
        thumbnail_type = request.data.get("thumbnail_type", None)
        thumbnail_key = request.data.get("thumbnail_key", None)
        thumbnail_media_type = request.data.get("thumbnail_media_type", None)
        # Other params
        keywords = sanitize_string(request.data.get("keywords", ""))
        slug = slugify(request.data.get("slug", None))
        category_slug = slugify(request.data.get("category", None))

        # Validar existencia de la categoría
        try:
            category = Category.objects.get(slug=category_slug)
        except Category.DoesNotExist:
            return self.error(
                f"Category '{category_slug}' does not exist.", status=400
            )
        
        try:
            post = Post.objects.create(
                user=user,
                title=title,
                description=description,
                content=content,
                keywords=keywords,
                slug=slug,
                category=category,
            )

            if thumbnail_key:
                thumbnail = Media.objects.create(
                    order=thumbnail_order,
                    name=thumbnail_name,
                    size=thumbnail_size,
                    type=thumbnail_type,
                    key=thumbnail_key,
                    media_type=thumbnail_media_type
                )

                post.thumbnail = thumbnail
                post.save()

            # Crear encabezado (heading)
            headings = request.data.get("headings", [])
            for heading_data in headings:
                Heading.objects.create(
                    post=post,
                    title=heading_data.get('title'),
                    slug=heading_data.get('slug'),
                    level=heading_data.get('level'),
                    order=heading_data.get('order'),
                )

        except Exception as e:
            return self.error(f"An error occurred: {str(e)}")
        
        return self.response(f"Post '{post.title}' created successfully. It will be showed in a few minutes")

    def put(self, request):
        """
        Actualizar un post para un autor
        """
        user = request.user
        if user.role == 'customer':
            return self.error("You do not have permission to create posts")
        
        post_slug = request.data.get("post_slug", None)
        if not post_slug:
            raise NotFound(detail="Post slug must be provided.")
        
        try:
            post = Post.objects.get(slug=post_slug, user=user)
        except Post.DoesNotExist:
            raise NotFound(f"Post {post_slug} does not exist.")
        
        # Obtener parametros
        title = sanitize_string(request.data.get('title', None))
        description = sanitize_string(request.data.get('description', None))
        content = sanitize_html(request.data.get('content', None))
        post_status = sanitize_string(request.data.get('status', 'draft'))
        category_slug = slugify(request.data.get("category", post.category.slug))
        # Thumbnail params
        thumbnail_order = request.data.get("thumbnail_order", None)
        thumbnail_name = request.data.get("thumbnail_name", None)
        thumbnail_size = request.data.get("thumbnail_size", None)
        thumbnail_type = request.data.get("thumbnail_type", None)
        thumbnail_key = request.data.get("thumbnail_key", None)
        thumbnail_media_type = request.data.get("thumbnail_media_type", None)

        # Validar existencia de la categoría
        if category_slug:
            try:
                category = Category.objects.get(slug=category_slug)
            except Category.DoesNotExist:
                return self.error(
                    f"Category '{category_slug}' does not exist.", status=400
                )
            post.category = category

        if title:
            post.title = title

        if description:
            post.description = description

        if content:
            post.content = content

        if thumbnail_key:
                thumbnail = Media.objects.create(
                    order=thumbnail_order,
                    name=thumbnail_name,
                    size=thumbnail_size,
                    type=thumbnail_type,
                    key=thumbnail_key,
                    media_type=thumbnail_media_type
                )

                post.thumbnail = thumbnail
                
        post.status = post_status

        # Actualizar encabezados (headings)
        headings = request.data.get("headings", [])
        if headings:
            post.headings.all().delete()  # Eliminar encabezados existentes
            for heading_data in headings:
                Heading.objects.create(
                    post=post,
                    title=heading_data.get("title"),
                    level=heading_data.get("level"),
                    order=heading_data.get("order"),
                )

        post.save()

        return self.response(f"Post {post.title} edited successfully. Changes will be processed in a few minutes")

    def delete(self, request):
        """
        Borrar un post para un autor
        """

        user = request.user
        if user.role == 'customer':
            return self.error("You do not have permission to create posts")
        
        post_slug = request.query_params.get("slug", None)
        if not post_slug:
            raise NotFound(detail="Post slug must be provided.")
        
        try:
            post = Post.objects.get(slug=post_slug, user=user)
        except Post.DoesNotExist:
            raise NotFound(f"Post {post_slug} does not exist.")
        
        post.delete()
        
        return self.response(f"Post with slug {post_slug} deleted successully.")


class PostListView(StandardAPIView):
    permission_classes = [HasValidAPIKey]

    def get(self, request, *args, **kwargs):
        try:
            # Parametros de solicitud
            search = request.query_params.get("search", "").strip()
            sorting = request.query_params.get("sorting", None)
            ordering = request.query_params.get("ordering", None)
            author = request.query_params.get("author", None)
            categories = request.query_params.getlist("category", [])
            page = request.query_params.get("p", "1")

            # Construir clave de cache para resultados paginados
            cache_key = f"post_list:{search}:{sorting}:{ordering}:{author}:{categories}:{page}"
            cached_posts = cache.get(cache_key)
            if cached_posts:
                # Serializar los datos del caché
                serialized_posts = PostListSerializer(cached_posts, many=True).data
                # Incrementar impresiones en Redis para los posts del caché
                for post in cached_posts:
                    redis_client.incr(f"post:impressions:{post.id}")  # Usar `post.id`
                return self.paginate(request, serialized_posts)

            # Consulta inicial optimizada
            posts = Post.postobjects.all().select_related("category").prefetch_related(
                Prefetch("post_analytics", to_attr="analytics_cache")
            )

            if not posts.exists():
                raise NotFound(detail="No posts found.")
            
            # Filtrar por busqueda
            if search:
                posts = posts.filter(
                    Q(title__icontains=search) |
                    Q(description__icontains=search) |
                    Q(content__icontains=search) |
                    Q(keywords__icontains=search) 
                )
            
            # Filtrar por autor
            if author:
                posts = posts.filter(user__username=author)

            # Filtrar por categoria
            if categories:
                category_queries = Q()
                for category in categories:
                    # Check if category is a valid uuid
                    try:
                        uuid.UUID(category)
                        uuid_query = (
                            Q(category__id=category)
                        )
                        category_queries |= uuid_query
                    except ValueError:
                        slug_query = (
                            Q(category__slug=category)
                        )
                        category_queries |= slug_query
                posts = posts.filter(category_queries)
            
            # Ordenamiento
            if sorting:
                if sorting == 'newest':
                    posts = posts.order_by("-created_at")
                elif sorting == 'recently_updated':
                    posts = posts.order_by("-updated_at")
                elif sorting == 'most_viewed':
                    posts = posts.annotate(popularity=F("analytics_cache__views")).order_by("-popularity")

            if ordering:
                if ordering == 'az':
                    posts = posts.order_by("title")
                if ordering == 'za':
                    posts = posts.order_by("-title")

            # Guardar los objetos en el caché
            cache.set(cache_key, posts, timeout=60 * 5)

            # Serializar los datos para la respuesta
            serialized_posts = PostListSerializer(posts, many=True).data

            # Incrementar impresiones en Redis
            for post in posts:
                redis_client.incr(f"post:impressions:{post.id}")  # Usar `post.id`

            return self.paginate(request, serialized_posts)
        except Exception as e:
            raise APIException(detail=f"An unexpected error occurred: {str(e)}")


class PostDetailView(StandardAPIView):
    permission_classes = [HasValidAPIKey]

    def get(self, request):
        ip_address = get_client_ip(request)
        slug = request.query_params.get("slug")
        user = request.user if request.user.is_authenticated else None

        if not slug:
            raise NotFound(detail="A valid slug must be provided")

        try:
            # Verificar si los datos están en caché
            cache_key = f"post_detail:{slug}"
            cached_post = cache.get(cache_key)
            if cached_post:
                serialized_post = PostSerializer(cached_post, context={'request': request}).data
                self._register_view_interaction(cached_post, ip_address, user)
                return self.response(serialized_post)

            # Si no está en caché, obtener el post de la base de datos
            try:
                post = Post.postobjects.get(slug=slug)
            except Post.DoesNotExist:
                raise NotFound(f"Post {slug} does not exist.")

            serialized_post = PostSerializer(post, context={'request': request}).data

            # Guardar en el caché
            cache.set(cache_key, post, timeout=60 * 5)

            # Registrar interaccion
            self._register_view_interaction(post, ip_address, user)
            

        except Post.DoesNotExist:
            raise NotFound(detail="The requested post does not exist")
        except Exception as e:
            raise APIException(detail=f"An unexpected error occurred: {str(e)}")

        return self.response(serialized_post)

    def _register_view_interaction(self, post, ip_address, user):
        """
        Registra la interacción de tipo 'view', maneja incrementos de vistas únicas 
        y totales, y actualiza PostAnalytics.
        """
        # Verifica si esta IP y usuario ya registraron una vista única
        if not PostView.objects.filter(post=post, ip_address=ip_address, user=user).exists():
            # Crea un registro de vista unica
            PostView.objects.create(post=post, ip_address=ip_address, user=user)

            try:
                PostInteraction.objects.create(
                    user=user,
                    post=post,
                    interaction_type="view",
                    ip_address=ip_address,
                )
            except Exception as e:
                raise ValueError(f"Error creeating PostInteraction: {e}")

            analytics, _ = PostAnalytics.objects.get_or_create(post=post)
            analytics.increment_metric('views')
        

class PostHeadingsView(StandardAPIView):
    permission_classes = [HasValidAPIKey]

    def get(self,request):
        post_slug = request.query_params.get("slug")
        heading_objects = Heading.objects.filter(post__slug = post_slug)
        serialized_data = HeadingSerializer(heading_objects, many=True).data
        return self.response(serialized_data)
    

class IncrementPostClickView(StandardAPIView):
    permission_classes = [HasValidAPIKey]

    def post(self, request):
        """
        Incrementa el contador de clics de un post basado en su slug.
        """
        data = request.data

        try:
            post = Post.postobjects.get(slug=data['slug'])
        except Post.DoesNotExist:
            raise NotFound(detail="The requested post does not exist")
        
        try:
            post_analytics, created = PostAnalytics.objects.get_or_create(post=post)
            post_analytics.increment_click()
        except Exception as e:
            raise APIException(detail=f"An error ocurred while updating post analytics: {str(e)}")

        return self.response({
            "message": "Click incremented successfully",
            "clicks": post_analytics.clicks
        })


class CategoryListView(StandardAPIView):
    permission_classes = [HasValidAPIKey]

    def get(self, request):

        try:
            # Parametros de solicitud
            parent_slug = request.query_params.get("parent_slug", None)
            ordering = request.query_params.get("ordering", None)
            sorting = request.query_params.get("sorting", None)
            search = request.query_params.get("search", "").strip()
            page = request.query_params.get("p", "1")

            # Construir clave de cache para resultados paginados
            cache_key = f"category_list:{page}:{ordering}:{sorting}:{search}:{parent_slug}"
            cached_categories = cache.get(cache_key)
            if cached_categories:
                # Serializar los datos del caché
                serialized_categories = CategoryListSerializer(cached_categories, many=True).data
                # Incrementar impresiones en Redis para los posts del caché
                for category in cached_categories:
                    redis_client.incr(f"category:impressions:{category.id}")  # Usar `post.id`
                return self.paginate(request, serialized_categories)

            # Consulta inicial optimizada
            if parent_slug:
                categories = Category.objects.filter(parent__slug=parent_slug).prefetch_related(
                    Prefetch("category_analytics", to_attr="analytics_cache")
                )
            else:
                # Si no especificamos un parent_slug buscamos las categorias padre
                categories = Category.objects.filter(parent__isnull=True).prefetch_related(
                    Prefetch("category_analytics", to_attr="analytics_cache")
                )

            if not categories.exists():
                raise NotFound(detail="No categories found.")
            
            # Filtrar por busqueda
            if search != "":
                categories = categories.filter(
                    Q(name__icontains=search) |
                    Q(slug__icontains=search) |
                    Q(title__icontains=search) |
                    Q(description__icontains=search)
                )
            
            # Ordenamiento
            if sorting:
                if sorting == 'newest':
                    categories = categories.order_by("-created_at")
                elif sorting == 'recently_updated':
                    categories = categories.order_by("-updated_at")
                elif sorting == 'most_viewed':
                    categories = categories.annotate(popularity=F("analytics_cache__views")).order_by("-popularity")

            if ordering:
                if ordering == 'az':
                    posts = posts.order_by("name")
                if ordering == 'za':
                    posts = posts.order_by("-name")

            # Guardar los objetos en el caché
            cache.set(cache_key, categories, timeout=60 * 5)

            # Serializacion
            serialized_categories = CategoryListSerializer(categories, many=True).data

            # Incrementar impresiones en Redis
            for category in categories:
                redis_client.incr(f"category:impressions:{category.id}")

            return self.paginate(request, serialized_categories)
        except Exception as e:
                raise APIException(detail=f"An unexpected error occurred: {str(e)}")


class CategoryDetailView(StandardAPIView):
    permission_classes = [HasValidAPIKey]

    def get(self, request):

        try:
            # Obtener parametros
            slug = request.query_params.get("slug", None)
            page = request.query_params.get("p", "1")

            if not slug:
                return self.error("Missing slug parameter")
            
            # Construir cache
            cache_key = f"category_posts:{slug}:{page}"
            cached_posts = cache.get(cache_key)
            if cached_posts:
                # Serializar los datos del caché
                serialized_posts = PostListSerializer(cached_posts, many=True).data
                # Incrementar impresiones en Redis para los posts del caché
                for post in cached_posts:
                    redis_client.incr(f"post:impressions:{post.id}")  # Usar `post.id`
                return self.paginate(request, serialized_posts)

            # Obtener la categoria por slug
            category = get_object_or_404(Category, slug=slug)

            # Obtener los posts que pertenecen a esta categoria
            posts = Post.postobjects.filter(category=category).select_related("category").prefetch_related(
                Prefetch("post_analytics", to_attr="analytics_cache")
            )
            
            if not posts.exists():
                raise NotFound(detail=f"No posts found for category '{category.name}'")
            
            # Guardar los objetos en el caché
            cache.set(cache_key, posts, timeout=60 * 5)

            # Serializar los posts
            serialized_posts = PostListSerializer(posts, many=True).data

            # Incrementar impresiones en Redis
            for post in posts:
                redis_client.incr(f"post:impressions:{post.id}")

            return self.paginate(request, serialized_posts)
        except Exception as e:
            raise APIException(detail=f"An unexpected error occurred: {str(e)}")


class IncrementCategoryClickView(StandardAPIView):
    permission_classes = [HasValidAPIKey]

    def post(self, request):
        """
        Incrementa el contador de clics de una categoria basado en su slug.
        """
        data = request.data

        try:
            category = Category.objects.get(slug=data['slug'])
        except Category.DoesNotExist:
            raise NotFound(detail="The requested category does not exist")
        
        try:
            category_analytics, created = CategoryAnalytics.objects.get_or_create(category=category)
            category_analytics.increment_click()
        except Exception as e:
            raise APIException(detail=f"An error ocurred while updating category analytics: {str(e)}")

        return self.response({
            "message": "Click incremented successfully",
            "clicks": category_analytics.clicks
        })


class ListPostCommentsView(StandardAPIView):
    permission_classes = [HasValidAPIKey]

    def get(self, request):

        post_slug = request.query_params.get("slug", None)
        page = request.query_params.get("p", "1")

        if not post_slug:
            raise NotFound(detail="A valid post slug must be provided")
        
        # Definir clave cache
        cache_key = f"post_comments:{post_slug}:{page}"
        cached_comments = cache.get(cache_key)
        if cached_comments:
            return self.paginate(request, cached_comments)
        
        try:
            post = Post.objects.get(slug=post_slug)
        except Post.DoesNotExist:
            raise ValueError(f"Post: {post_slug} does not exist")
        
        # Obtener solo los comentarios principales
        comments = Comment.objects.filter(post=post, parent=None)

        serialized_comments = CommentSerializer(comments, many=True).data

        # Guardar clave en el índice
        cache_index_key = f"post_comments_cache_keys:{post_slug}"
        cache_keys = cache.get(cache_index_key, [])
        cache_keys.append(cache_key)
        cache.set(cache_index_key, cache_keys, timeout=60 * 5)

        # Almacenar los datos en caché
        cache.set(cache_key, serialized_comments, timeout=60 * 5)

        return self.paginate(request, serialized_comments)


class PostCommentViews(StandardAPIView):
    permission_classes = [HasValidAPIKey, permissions.IsAuthenticated]
    
    def post(self, request):
        """
        Crear un comentario para un post
        """
        # Obtener parametros
        post_slug = request.data.get("slug", None)
        user = request.user
        ip_address = get_client_ip(request)
        content = sanitize_html(request.data.get("content", None))

        if not post_slug:
            raise NotFound(detail="A valid post slug must be provided")
        
        try:
            post = Post.objects.get(slug=post_slug)
        except Post.DoesNotExist:
            raise NotFound(detail=f"Post: {post_slug} does not exist")
        
        # Crear comentario
        comment = Comment.objects.create(
            user=user,
            post=post,
            content=content,
        )

        # Invalidar el cache de comentarios para el post
        self._invalidate_post_comments_cache(post_slug)

        # Actualizar interaccion de post
        self._register_comment_interaction(comment, post, ip_address, user)

        return self.response(f"Comment created for post {post.title}")
    
    def put(self, request):
        """
        Modificar un comentario
        """
        # Obtener parametros
        comment_id = request.data.get("comment_id", None)
        content = sanitize_html(request.data.get("content", None))

        if not comment_id:
            raise NotFound(detail="A valid comment id must be provided")
        
        try:
            comment = Comment.objects.get(id=comment_id, user=request.user)
        except Comment.DoesNotExist:
            raise NotFound(detail=f"Comment with id: {comment_id} does not exist")
        
        comment.content = content
        comment.save()

        # Invalidar el cache de comentarios para el post
        self._invalidate_post_comments_cache(comment.post.slug)

        if comment.parent and comment.parent.replies.exists():
            self._invalidate_comment_replies_cache(comment.parent.id)

        return self.response("Comment content updated successfully")
    
    def delete(self, request):
        """
        Borrar un comentario
        """
        comment_id = request.query_params.get("comment_id", None)

        if not comment_id:
            raise NotFound(detail="A valid comment id must be provided")
        
        try:
            comment = Comment.objects.get(id=comment_id, user=request.user)
        except Comment.DoesNotExist:
            raise NotFound(detail=f"Comment with id: {comment_id} does not exist")
        
        post = comment.post
        post_analytics, _ = PostAnalytics.objects.get_or_create(post=post)

        if comment.parent and comment.parent.replies.exists():
            self._invalidate_comment_replies_cache(comment.parent.id)

        comment.delete()

        # Actualizar metricas
        comments_count = Comment.objects.filter(post=post, is_active=True).count()

        post_analytics.comments = comments_count
        post_analytics.save()

        # Invalidar el cache de comentarios para el post
        self._invalidate_post_comments_cache(post.slug)

        return self.response("Comment deleted successfully")
    
    def _register_comment_interaction(self, comment, post, ip_address, user):

        PostInteraction.objects.create(
            user=user,
            post=post,
            interaction_type="comment",
            comment=comment,
            ip_address=ip_address
        )

        analytics, _ = PostAnalytics.objects.get_or_create(post=post)
        analytics.increment_metric("comments")

    def _invalidate_post_comments_cache(self, post_slug):
        """
        Invalida todas las claves de caché relacionadas con los comentarios de un post.
        """
        # definir clave cache
        cache_index_key = f"post_comments_cache_keys:{post_slug}"
        cache_keys = cache.get(cache_index_key, [])

        # Eliminar cada clave almacenada en el indice
        for key in cache_keys:
            cache.delete(key)

        # Limpiar el indice de claves
        cache.delete(cache_index_key)

    def _invalidate_comment_replies_cache(self, comment_id):
        """
        Invalida todas las claves de caché relacionadas con las respuestas de un comentario.
        """
        cache_index_key = f"comment_replies_cache_keys:{comment_id}"
        cache_keys = cache.get(cache_index_key, [])

        for key in cache_keys:
            cache.delete(key)

        cache.delete(cache_index_key)


class ListCommentRepliesView(StandardAPIView):
    permission_classes = [HasValidAPIKey]

    def get(self, request):

        comment_id = request.query_params.get("comment_id")
        page = request.query_params.get("p", "1")

        if not comment_id:
            raise NotFound(detail="A valid comment_id must be provided")
        
        # Definir la clave cache
        cache_key = f"comment_replies:{comment_id}:{page}"
        cached_replies = cache.get(cache_key)
        if cached_replies:
            return self.paginate(request, cached_replies)
        
        # Obtener el comentario padre
        try:
            parent_comment = Comment.objects.get(id=comment_id)
        except Comment.DoesNotExist:
            raise NotFound(detail=f"Comment with id: {comment_id} does not exist")
        
        # Filtrar las respuestas activas del comentario padre
        replies = parent_comment.replies.filter(is_active=True).order_by("-created_at")

        # Serializar respuesta
        serialized_replies = CommentSerializer(replies, many=True).data

        # Registrar la clave en el índice de caché
        self._register_comment_reply_cache_key(comment_id, cache_key)

        # Guardar las respuestas en el caché
        cache.set(cache_key, serialized_replies, timeout=60 * 5)

        return self.paginate(request, serialized_replies)
    
    def _register_comment_reply_cache_key(self, comment_id, cache_key):
        """
        Registrar claves de caché relacionadas con las respuestas de un comentario.
        """
        cache_index_key = f"comment_replies_cache_keys:{comment_id}"
        cache_keys = cache.get(cache_index_key, [])
        if cache_key not in cache_keys:
            cache_keys.append(cache_key)
        cache.set(cache_index_key, cache_keys, timeout=60 * 5)

    
class CommentReplyViews(StandardAPIView):
    permission_classes = [HasValidAPIKey, permissions.IsAuthenticated]

    def post(self, request):

        # Obtener parametros
        comment_id = request.data.get("comment_id")
        user = request.user
        ip_address = get_client_ip(request)
        content = sanitize_html(request.data.get("content", None))

        if not comment_id:
            raise NotFound(detail="A valid comment_id must be provided")

        # Obtener el comentario padre
        try:
            parent_comment = Comment.objects.get(id=comment_id)
        except Comment.DoesNotExist:
            raise NotFound(detail=f"Comment with id: {comment_id} does not exist")
        
        # Crear el reply
        comment = Comment.objects.create(
            user=user,
            post=parent_comment.post,
            parent=parent_comment,
            content=content,
        )

        # Invalidar caché de respuestas
        self._invalidate_comment_replies_cache(comment_id)

        # Actualiizar metricas
        self._register_comment_interaction(comment, comment.post, ip_address, user)

        return self.response("Comment reply created successfully")

    def _register_comment_interaction(self, comment, post, ip_address, user):

        PostInteraction.objects.create(
            user=user,
            post=post,
            interaction_type="comment",
            comment=comment,
            ip_address=ip_address
        )

        analytics, _ = PostAnalytics.objects.get_or_create(post=post)
        analytics.increment_metric("comments")

    def _invalidate_comment_replies_cache(self, comment_id):
        """
        Invalida todas las claves de caché relacionadas con las respuestas de un comentario.
        """
        cache_index_key = f"comment_replies_cache_keys:{comment_id}"
        cache_keys = cache.get(cache_index_key, [])

        for key in cache_keys:
            cache.delete(key)

        cache.delete(cache_index_key)


class PostLikeViews(StandardAPIView):
    permission_classes = [HasValidAPIKey, permissions.IsAuthenticated]

    def post(self, request):
        """
        Crear un 'like' para un post.
        """
        post_slug = request.data.get("slug", None)
        user = request.user

        ip_address = get_client_ip(request)

        if not post_slug:
            raise NotFound(detail="A valid post slug must be provided")
        
        try:
            post = Post.objects.get(slug=post_slug)
        except Post.DoesNotExist:
            raise NotFound(detail=f"Post: {post_slug} does not exist")
        
        # Verificar si el usuario ya ha dado like al post
        if PostLike.objects.filter(post=post, user=user).exists():
            raise ValidationError(detail="You have already liked this post.")
        
        # Crear 'like'
        PostLike.objects.create(post=post, user=user)

        # Registrar interacción
        PostInteraction.objects.create(
            user=user,
            post=post,
            interaction_type="like",
            ip_address=ip_address
        )

        # Incrementar métricas
        analytics, _ = PostAnalytics.objects.get_or_create(post=post)
        analytics.increment_metric("likes")

        return self.response(f"You have liked the post: {post.title}")
    
    def delete(self, request):
        """
        Eliminar un 'like' de un post.
        """
        post_slug = request.query_params.get("slug", None)
        user = request.user

        if not post_slug:
            raise NotFound(detail="A valid post slug must be provided")

        try:
            post = Post.objects.get(slug=post_slug)
        except Post.DoesNotExist:
            raise NotFound(detail=f"Post with slug: {post_slug} does not exist")
        
        # Verificar si el usuario ha dado like al post
        try:
            like = PostLike.objects.get(post=post, user=user)
        except PostLike.DoesNotExist:
            raise ValidationError(detail="You have not liked this post.")
        
        # Eliminar 'like'
        like.delete()

        # Actualizar métricas
        analytics, _ = PostAnalytics.objects.get_or_create(post=post)
        analytics.likes = PostLike.objects.filter(post=post).count()
        analytics.save()

        return self.response(f"You have unliked the post: {post.title}")


class PostShareView(StandardAPIView):
    permission_classes = [HasValidAPIKey]

    def post(self, request):
        """
        Maneja la acción de compartir un post.
        """
        # Obtener parámetros
        post_slug = request.data.get("slug", None)
        platform = request.data.get("platform", "other").lower()
        user = request.user if request.user.is_authenticated else None
        ip_address = get_client_ip(request)

        if not post_slug:
            raise NotFound(detail="A valid post slug must be provided")
        
        try:
            post = Post.objects.get(slug=post_slug)
        except Post.DoesNotExist:
            raise NotFound(detail=f"Post: {post_slug} does not exist")

        # Verificar que la plataforma es válida
        valid_platforms = [choice[0] for choice in PostShare._meta.get_field("platform").choices]
        if platform not in valid_platforms:
            raise ValidationError(detail=f"Invalid platform. Valid options are: {', '.join(valid_platforms)}")
        
        # Crear un registro de 'share'
        PostShare.objects.create(
            post=post,
            user=user,
            platform=platform
        )

        # Registrar interacción
        PostInteraction.objects.create(
            user=user,
            post=post,
            interaction_type="share",
            ip_address=ip_address
        )

        # Actualizar métricas
        analytics, _ = PostAnalytics.objects.get_or_create(post=post)
        analytics.increment_metric("shares")

        return self.response(f"Post '{post.title}' shared successfully on {platform.capitalize()}")


class GenerateFakePostsView(StandardAPIView):

    def get(self,request):
        # Configurar Faker
        fake = Faker()

        # Obtener todas las categorías existentes
        categories = list(Category.objects.all())

        if not categories:
            return self.response("No hay categorías disponibles para asignar a los posts", 400)

        posts_to_generate = 100  # Número de posts ficticios a generar
        status_options = ["draft", "published"]

        for _ in range(posts_to_generate):
            title = fake.sentence(nb_words=6)  # Generar título aleatorio
            user = UserAccount.objects.get(username="test_editor")
            post = Post(
                id=uuid.uuid4(),
                user=user,
                title=title,
                description=fake.sentence(nb_words=12),
                content=fake.paragraph(nb_sentences=5),
                keywords=", ".join(fake.words(nb=5)),
                slug=slugify(title),  # Generar slug a partir del título
                category=random.choice(categories),  # Asignar una categoría aleatoria
                status=random.choice(status_options),
            )
            post.save()

        return self.response(f"{posts_to_generate} posts generados exitosamente.")
    

class GenerateFakeAnalyticsView(StandardAPIView):

    def get(self, request):
        fake = Faker()

        # Obtener todos los posts existentes
        posts = Post.objects.all()

        if not posts:
            return self.response({"error": "No hay posts disponibles para generar analíticas"}, status=400)

        analytics_to_generate = len(posts)  # Una analítica por post

        # Generar analíticas para cada post
        for post in posts:
            views = random.randint(50, 1000)  # Número aleatorio de vistas
            impressions = views + random.randint(100, 2000)  # Impresiones >= vistas
            clicks = random.randint(0, views)  # Los clics son <= vistas
            avg_time_on_page = round(random.uniform(10, 300), 2)  # Tiempo promedio en segundos
            
            # Crear o actualizar analíticas para el post
            analytics, created = PostAnalytics.objects.get_or_create(post=post)
            analytics.views = views
            analytics.impressions = impressions
            analytics.clicks = clicks
            analytics.avg_time_on_page = avg_time_on_page
            analytics._update_click_through_rate()  # Recalcular el CTR
            analytics.save()

        return self.response({"message": f"Analíticas generadas para {analytics_to_generate} posts."})