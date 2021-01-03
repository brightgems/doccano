from django.urls import path
from rest_framework.authtoken.views import obtain_auth_token
from rest_framework.urlpatterns import format_suffix_patterns
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

from .views import Me, Features, Users, Health
from .views import ProjectList, ProjectDetail
from .views import LabelList, LabelDetail, ApproveLabelsAPI, LabelUploadAPI
from .views import DocumentList, DocumentDetail, DeleteAllDocsAPI
from .views import AnnotationList, AnnotationDetail
from .views import TextUploadAPI, TextDownloadAPI, CloudUploadAPI
from .views import DocumentAssignToAPI
from .views import StatisticsAPI
from .views import RoleMappingList, RoleMappingDetail, Roles
from .views import CommentList, CommentDetail
from .views import ModelProjectList, ModelProjectDetail, ModelBackendList, ModelTrain, ModelPredition

schema_view = get_schema_view(
    openapi.Info(
        title="Demo API",
        default_version='v1',
        description="Demo description",
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    path('health', Health.as_view(), name='health'),
    path('auth-token', obtain_auth_token),
    path('me', Me.as_view(), name='me'),
    path('features', Features.as_view(), name='features'),
    path('cloud-upload', CloudUploadAPI.as_view(), name='cloud_uploader'),
    path('projects', ProjectList.as_view(), name='project_list'),
    path('users', Users.as_view(), name='user_list'),
    path('roles', Roles.as_view(), name='roles'),
    path('projects/<int:project_id>', ProjectDetail.as_view(), name='project_detail'),
    path('projects/<int:project_id>/delete_all_documents', DeleteAllDocsAPI.as_view(), name='project_detail'),
    path('projects/<int:project_id>/statistics',
         StatisticsAPI.as_view(), name='statistics'),
    path('projects/<int:project_id>/labels',
         LabelList.as_view(), name='label_list'),
    path('projects/<int:project_id>/label-upload',
         LabelUploadAPI.as_view(), name='label_upload'),
    path('projects/<int:project_id>/labels/<int:label_id>',
         LabelDetail.as_view(), name='label_detail'),
    path('projects/<int:project_id>/docs',
         DocumentList.as_view(), name='doc_list'),
    path('projects/<int:project_id>/docs/<int:doc_id>',
         DocumentDetail.as_view(), name='doc_detail'),
    path('projects/<int:project_id>/docs/<int:doc_id>/approve-labels',
         ApproveLabelsAPI.as_view(), name='approve_labels'),
    path('projects/<int:project_id>/docs/<int:doc_id>/annotations',
         AnnotationList.as_view(), name='annotation_list'),
    path('projects/<int:project_id>/docs/<int:doc_id>/annotations/<int:annotation_id>',
         AnnotationDetail.as_view(), name='annotation_detail'),
    path('projects/<int:project_id>/docs/upload',
         TextUploadAPI.as_view(), name='doc_uploader'),
    path('projects/<int:project_id>/docs/download',
         TextDownloadAPI.as_view(), name='doc_downloader'),
    path('projects/<int:project_id>/docs/doc_assign_to',
         DocumentAssignToAPI.as_view(), name='doc_assign_to'),
    path('projects/<int:project_id>/roles',
         RoleMappingList.as_view(), name='rolemapping_list'),
    path('projects/<int:project_id>/roles/<int:rolemapping_id>',
         RoleMappingDetail.as_view(), name='rolemapping_detail'),
    path('projects/<int:project_id>/docs/<int:doc_id>/comments',
         CommentList.as_view(), name='comment_list'),
    path('projects/<int:project_id>/docs/<int:doc_id>/comments/<int:comment_id>',
         CommentDetail.as_view(), name='comment_detail'),
    # active learning
    path('models', ModelProjectList.as_view(), name='model_list'),
    path('models/<int:model_id>', ModelProjectDetail.as_view(), name='model_detail'),
    path('model_backends', ModelBackendList.as_view(), name='model_backend'),
]

# urlpatterns = format_suffix_patterns(urlpatterns, allowed=['json', 'xml'])
