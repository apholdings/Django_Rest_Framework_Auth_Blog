from django.urls import path

from .views import (
    PostListView, 
    PostDetailView, 
    PostHeadingsView, 
    IncrementPostClickView,
    CategoryListView,
    CategoryDetailView,
    IncrementCategoryClickView,
    GenerateFakePostsView,
    GenerateFakeAnalyticsView
)

urlpatterns = [
    path('generate_posts/', GenerateFakePostsView.as_view()),
    path('generate_analytics/', GenerateFakeAnalyticsView.as_view()),
    path('posts/', PostListView.as_view(), name='post-list'),
    path('post/', PostDetailView.as_view(), name='post-detail'),
    path('post/headings/', PostHeadingsView.as_view(), name='post-headings'),
    path('post/increment_click/', IncrementPostClickView.as_view(), name='increment-post-click'),
    path('categories/', CategoryListView.as_view(), name='category-list'),
    path('category/posts/', CategoryDetailView.as_view(), name='category-posts'),
    path('category/increment_click/', IncrementCategoryClickView.as_view(), name='increment-category-click'),
]