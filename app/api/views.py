import collections
import hashlib
import json
from django.conf import settings
from django.contrib.auth.models import User
from django.db import transaction
from django.db.utils import IntegrityError
from django.shortcuts import get_object_or_404, redirect
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Count, F, Q
from libcloud.base import DriverType, get_driver
from libcloud.storage.types import ContainerDoesNotExistError, ObjectDoesNotExistError
from rest_framework.decorators import action
from rest_framework import generics, mixins, viewsets, filters, status
from rest_framework.exceptions import ParseError, ValidationError
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser
from rest_framework_csv.renderers import CSVRenderer

from .filters import DocumentFilter
from .models import Project, Label, Document, RoleMapping, Role, Comment, ModelProject, ModelBackend
from .permissions import IsProjectAdmin, IsAnnotatorAndReadOnly, IsAnnotator, IsAnnotationApproverAndReadOnly, IsOwnAnnotation, IsAnnotationApprover,IsOwnComment
from .serializers import ProjectSerializer, LabelSerializer, DocumentSerializer, UserSerializer, DocumentAssignToSerializer, CommentSerializer
from .serializers import ProjectPolymorphicSerializer, RoleMappingSerializer, RoleSerializer
from .serializers import ActiveLearningModelProjectSerializer, ActiveLearningModelBackendSerializer
from .utils import CSVParser, ExcelParser, JSONParser, PlainTextParser, CoNLLParser, AudioParser, iterable_to_io
from .utils import JSONLRenderer
from .utils import JSONPainter, CSVPainter

IsInProjectReadOnlyOrAdmin = (IsAnnotatorAndReadOnly | IsAnnotationApproverAndReadOnly | IsProjectAdmin)
IsInProjectOrAdmin = (IsAnnotator | IsAnnotationApprover | IsProjectAdmin)


class Health(APIView):
    permission_classes = (IsAuthenticatedOrReadOnly,)

    def get(self, request, *args, **kwargs):
        return Response({'status': 'green'})


class Me(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        serializer = UserSerializer(request.user, context={'request': request})
        return Response(serializer.data)


class Features(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        return Response({
            'cloud_upload': bool(settings.CLOUD_BROWSER_APACHE_LIBCLOUD_PROVIDER),
        })


class ProjectList(generics.ListCreateAPIView):
    serializer_class = ProjectPolymorphicSerializer
    pagination_class = None
    permission_classes = [IsAuthenticated & IsInProjectReadOnlyOrAdmin]

    def get_queryset(self):
        return self.request.user.projects

    def perform_create(self, serializer):
        serializer.save(users=[self.request.user])


class ProjectDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer
    lookup_url_kwarg = 'project_id'
    permission_classes = [IsAuthenticated & IsInProjectReadOnlyOrAdmin]

class DeleteAllDocsAPI(APIView):
    permission_classes = [IsAuthenticated & IsInProjectReadOnlyOrAdmin]
    def post(self,request,project_id):
        docs = Document.objects.filter(project__id=project_id)
        if docs.exists():
            docs.delete()
        return Response()

class StatisticsAPI(APIView):
    pagination_class = None
    permission_classes = [IsAuthenticated & IsInProjectReadOnlyOrAdmin]

    def get(self, request, *args, **kwargs):
        p = get_object_or_404(Project, pk=self.kwargs['project_id'])

        include = set(request.GET.getlist('include'))
        response = {}

        if not include or 'label' in include:
            label_count, user_count = self.label_per_data(p)
            response['label'] = label_count
            # TODO: Make user_label count chart
            response['user_label'] = user_count

        if not include or 'total' in include or 'remaining' in include or 'user' in include:
            progress = self.progress(project=p)
            response.update(progress)

        if include:
            response = {key: value for (key, value) in response.items() if key in include}

        return Response(response)

    @staticmethod
    def _get_user_completion_data(annotation_class, annotation_filter):
        all_annotation_objects  = annotation_class.objects.filter(annotation_filter)
        set_user_data = collections.defaultdict(set)
        for ind_obj in all_annotation_objects.values('user__username', 'document__id'):
            set_user_data[ind_obj['user__username']].add(ind_obj['document__id'])
        return {i: len(set_user_data[i]) for i in set_user_data}


    def progress(self, project):
        docs = project.documents
        annotation_class = project.get_annotation_class()
        total = docs.count()
        annotation_filter = Q(document_id__in=docs.all())
        user_data = self._get_user_completion_data(annotation_class, annotation_filter)
        if not project.collaborative_annotation:
            annotation_filter &= Q(user_id=self.request.user)
        done = annotation_class.objects.filter(annotation_filter)\
            .aggregate(Count('document', distinct=True))['document__count']
        remaining = total - done
        return {'total': total, 'remaining': remaining, 'user': user_data}

    def label_per_data(self, project):
        annotation_class = project.get_annotation_class()
        return annotation_class.objects.get_label_per_data(project=project)


class ApproveLabelsAPI(APIView):
    permission_classes = [IsAuthenticated & (IsAnnotationApprover | IsProjectAdmin)]

    def post(self, request, *args, **kwargs):
        approved = self.request.data.get('approved', True)
        document = get_object_or_404(Document, pk=self.kwargs['doc_id'])
        document.annotations_approved_by = self.request.user if approved else None
        document.save()
        return Response(DocumentSerializer(document).data)


class LabelList(generics.ListCreateAPIView):
    serializer_class = LabelSerializer
    pagination_class = None
    permission_classes = [IsAuthenticated & IsInProjectReadOnlyOrAdmin]

    def get_queryset(self):
        project = get_object_or_404(Project, pk=self.kwargs['project_id'])
        return project.labels

    def perform_create(self, serializer):
        project = get_object_or_404(Project, pk=self.kwargs['project_id'])
        serializer.save(project=project)


class LabelDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Label.objects.all()
    serializer_class = LabelSerializer
    lookup_url_kwarg = 'label_id'
    permission_classes = [IsAuthenticated & IsInProjectReadOnlyOrAdmin]


class DocumentList(generics.ListCreateAPIView):
    serializer_class = DocumentSerializer
    filter_backends = (DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter)
    search_fields = ('text', )
    ordering_fields = ('created_at', 'updated_at', 'doc_annotations__updated_at',
                       'seq_annotations__updated_at', 'seq2seq_annotations__updated_at')
    filter_class = DocumentFilter
    permission_classes = [IsAuthenticated & IsInProjectReadOnlyOrAdmin]

    def get_queryset(self):
        project = get_object_or_404(Project, pk=self.kwargs['project_id'])

        queryset = project.documents
        if project.randomize_document_order:
            queryset = queryset.annotate(sort_id=F('id') % self.request.user.id).order_by('sort_id')
        else:
            queryset = queryset.order_by('id')

        return queryset

    def perform_create(self, serializer):
        project = get_object_or_404(Project, pk=self.kwargs['project_id'])
        serializer.save(project=project)


class DocumentDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Document.objects.all()
    serializer_class = DocumentSerializer
    lookup_url_kwarg = 'doc_id'
    permission_classes = [IsAuthenticated & IsInProjectReadOnlyOrAdmin]


class AnnotationList(generics.ListCreateAPIView):
    pagination_class = None
    permission_classes = [IsAuthenticated & IsInProjectOrAdmin]
    swagger_schema = None

    def get_serializer_class(self):
        project = get_object_or_404(Project, pk=self.kwargs['project_id'])
        self.serializer_class = project.get_annotation_serializer()
        return self.serializer_class

    def get_queryset(self):
        project = get_object_or_404(Project, pk=self.kwargs['project_id'])
        model = project.get_annotation_class()

        queryset = model.objects.filter(document=self.kwargs['doc_id'])
        if not project.collaborative_annotation:
            queryset = queryset.filter(user=self.request.user)

        return queryset

    def create(self, request, *args, **kwargs):
        self.check_single_class_classification(self.kwargs['project_id'], self.kwargs['doc_id'], request.user)

        request.data['document'] = self.kwargs['doc_id']
        return super().create(request, args, kwargs)

    def perform_create(self, serializer):
        serializer.save(document_id=self.kwargs['doc_id'], user=self.request.user)

    @staticmethod
    def check_single_class_classification(project_id, doc_id, user):
        project = get_object_or_404(Project, pk=project_id)
        if not project.single_class_classification:
            return

        model = project.get_annotation_class()
        annotations = model.objects.filter(document_id=doc_id)
        if not project.collaborative_annotation:
            annotations = annotations.filter(user=user)

        if annotations.exists():
            raise ValidationError('requested to create duplicate annotation for single-class-classification project')


class AnnotationDetail(generics.RetrieveUpdateDestroyAPIView):
    lookup_url_kwarg = 'annotation_id'
    permission_classes = [IsAuthenticated & (((IsAnnotator & IsOwnAnnotation) | IsAnnotationApprover)  | IsProjectAdmin)]
    swagger_schema = None

    def get_serializer_class(self):
        project = get_object_or_404(Project, pk=self.kwargs['project_id'])
        self.serializer_class = project.get_annotation_serializer()
        return self.serializer_class

    def get_queryset(self):
        project = get_object_or_404(Project, pk=self.kwargs['project_id'])
        model = project.get_annotation_class()
        self.queryset = model.objects.all()
        return self.queryset

class DocumentAssignToAPI(APIView):
    permission_classes = [IsAuthenticated & IsProjectAdmin]

    def post(self, request, *args, **kwargs):
        serializer = DocumentAssignToSerializer(data=request.data)
        serializer.is_valid()
        users = serializer.validated_data['users']
        from django.db import connection     
        cursor = connection.cursor()
        number_person=len(users)
        for person_num,user_id in enumerate(users):
            cursor.execute(
                "update api_document set annotations_assign_to_id=%d where project_id=%d and mod(id,%d)=%d"%(
                    user_id,self.kwargs['project_id'],number_person,person_num)
            )     
        # cursor.execute("commit")    
        cursor.close()    

        return Response(status=status.HTTP_200_OK)


class TextUploadAPI(APIView):
    parser_classes = (MultiPartParser,)
    permission_classes = [IsAuthenticated & IsProjectAdmin]

    def post(self, request, *args, **kwargs):
        if 'file' not in request.data:
            raise ParseError('Empty content')
        ignore_existing=request.data.get('ignore_existing', "false")=="true"
        self.save_file(
            user=request.user,
            file=request.data['file'],
            file_format=request.data['format'],
            project_id=kwargs['project_id'],
            ignore_existing=ignore_existing
        )

        return Response(status=status.HTTP_201_CREATED)

    @classmethod
    def save_file(cls, user, file, file_format, project_id,ignore_existing=False):
        project = get_object_or_404(Project, pk=project_id)
        parser = cls.select_parser(file_format)
        data = parser.parse(file)
        if ignore_existing:
            data=cls.drop_existing(data,project)
        
        storage = project.get_storage(data)
        storage.save(user)

    @classmethod
    def drop_existing(cls, data, project):
        """drop duplicated document existed in database
        """
        for batch in data:
            text_md5_ls = list(Document.objects.filter(project=project).values_list('text_md5', flat=True).all())
            dedup_data=[]
            for doc in batch:
                if 'text' not in doc:
                    dedup_data=batch
                    break
                md5= hashlib.md5(doc['text'].encode('utf-8')).hexdigest()
                if md5 not in text_md5_ls:
                    dedup_data.append(doc)
            if  len(dedup_data)>0:
                yield dedup_data

    @classmethod
    def select_parser(cls, file_format):
        if file_format == 'plain':
            return PlainTextParser()
        elif file_format == 'csv':
            return CSVParser()
        elif file_format == 'json':
            return JSONParser()
        elif file_format == 'conll':
            return CoNLLParser()
        elif file_format == 'excel':
            return ExcelParser()
        elif file_format == 'audio':
            return AudioParser()
        else:
            raise ValidationError('format {} is invalid.'.format(file_format))


class CloudUploadAPI(APIView):
    permission_classes = TextUploadAPI.permission_classes

    def get(self, request, *args, **kwargs):
        try:
            project_id = request.query_params['project_id']
            file_format = request.query_params['upload_format']
            cloud_container = request.query_params['container']
            cloud_object = request.query_params['object']
        except KeyError as ex:
            raise ValidationError('query parameter {} is missing'.format(ex))

        try:
            cloud_file = self.get_cloud_object_as_io(cloud_container, cloud_object)
        except ContainerDoesNotExistError:
            raise ValidationError('cloud container {} does not exist'.format(cloud_container))
        except ObjectDoesNotExistError:
            raise ValidationError('cloud object {} does not exist'.format(cloud_object))

        TextUploadAPI.save_file(
            user=request.user,
            file=cloud_file,
            file_format=file_format,
            project_id=project_id,
        )

        next_url = request.query_params.get('next')

        if next_url == 'about:blank':
            return Response(data='', content_type='text/plain', status=status.HTTP_201_CREATED)

        if next_url:
            return redirect(next_url)

        return Response(status=status.HTTP_201_CREATED)

    @classmethod
    def get_cloud_object_as_io(cls, container_name, object_name):
        provider = settings.CLOUD_BROWSER_APACHE_LIBCLOUD_PROVIDER.lower()
        account = settings.CLOUD_BROWSER_APACHE_LIBCLOUD_ACCOUNT
        key = settings.CLOUD_BROWSER_APACHE_LIBCLOUD_SECRET_KEY

        driver = get_driver(DriverType.STORAGE, provider)
        client = driver(account, key)

        cloud_container = client.get_container(container_name)
        cloud_object = cloud_container.get_object(object_name)

        return iterable_to_io(cloud_object.as_stream())


class TextDownloadAPI(APIView):
    permission_classes = TextUploadAPI.permission_classes

    renderer_classes = (CSVRenderer, JSONLRenderer)

    def get(self, request, *args, **kwargs):
        format = request.query_params.get('q')
        project = get_object_or_404(Project, pk=self.kwargs['project_id'])
        documents = project.documents.all()
        painter = self.select_painter(format)
        # json1 format prints text labels while json format prints annotations with label ids
        # json1 format - "labels": [[0, 15, "PERSON"], ..]
        # json format - "annotations": [{"label": 5, "start_offset": 0, "end_offset": 2, "user": 1},..]
        if format == "json1":
            labels = project.labels.all()
            data = JSONPainter.paint_labels(documents, labels)
        else:
            data = painter.paint(documents)
        return Response(data)

    def select_painter(self, format):
        if format == 'csv':
            return CSVPainter()
        elif format == 'json' or format == "json1":
            return JSONPainter()
        else:
            raise ValidationError('format {} is invalid.'.format(format))


class Users(APIView):
    permission_classes = [IsAuthenticated & IsProjectAdmin]

    def get(self, request, *args, **kwargs):
        queryset = User.objects.all()
        serialized_data = UserSerializer(queryset, many=True).data
        return Response(serialized_data)


class Roles(generics.ListCreateAPIView):
    serializer_class = RoleSerializer
    pagination_class = None
    permission_classes = [IsAuthenticated & IsProjectAdmin]
    queryset = Role.objects.all()


class RoleMappingList(generics.ListCreateAPIView):
    serializer_class = RoleMappingSerializer
    pagination_class = None
    permission_classes = [IsAuthenticated & IsProjectAdmin]

    def get_queryset(self):
        project = get_object_or_404(Project, pk=self.kwargs['project_id'])
        return project.role_mappings

    def perform_create(self, serializer):
        project = get_object_or_404(Project, pk=self.kwargs['project_id'])
        serializer.save(project=project)


class RoleMappingDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = RoleMapping.objects.all()
    serializer_class = RoleMappingSerializer
    lookup_url_kwarg = 'rolemapping_id'
    permission_classes = [IsAuthenticated & IsProjectAdmin]


class LabelUploadAPI(APIView):
    parser_classes = (MultiPartParser,)
    permission_classes = [IsAuthenticated & IsProjectAdmin]

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        if 'file' not in request.data:
            raise ParseError('Empty content')
        labels = json.load(request.data['file'])
        project = get_object_or_404(Project, pk=kwargs['project_id'])
        try:
            for label in labels:
                serializer = LabelSerializer(data=label)
                serializer.is_valid(raise_exception=True)
                serializer.save(project=project)
            return Response(status=status.HTTP_201_CREATED)
        except IntegrityError:
            content = {'error': 'IntegrityError: you cannot create a label with same name or shortkey.'}
            return Response(content, status=status.HTTP_400_BAD_REQUEST)

class CommentList(generics.ListCreateAPIView):
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticated & IsInProjectOrAdmin]

    def get_queryset(self):
        return Comment.objects.filter(
            document_id=self.kwargs['doc_id'],
            user_id=self.request.user.id,
        ).all()

    def perform_create(self, serializer):
        serializer.save(user=self.request.user, document_id=self.kwargs['doc_id'])


class CommentDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    lookup_url_kwarg = 'comment_id'
    permission_classes = [IsAuthenticated & IsInProjectOrAdmin & IsOwnComment]

# ====deep active learning API======

class ModelProjectList(generics.ListCreateAPIView):
    queryset = ModelProject.objects.all()
    serializer_class = ActiveLearningModelProjectSerializer
    pagination_class = None
    permission_classes = [IsAuthenticated & IsInProjectReadOnlyOrAdmin]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class ModelProjectDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = ModelProject.objects.all()
    serializer_class = ActiveLearningModelProjectSerializer
    lookup_url_kwarg = 'model_id'
    permission_classes = [IsAuthenticated & IsInProjectReadOnlyOrAdmin]


class ModelBackendList(generics.ListCreateAPIView):
    queryset = ModelBackend.objects.all()
    serializer_class = ActiveLearningModelBackendSerializer
    pagination_class = None
    permission_classes = [IsAuthenticated & IsInProjectReadOnlyOrAdmin]


# train/prediction

class ModelTrain(APIView):
    permission_classes = (IsAuthenticatedOrReadOnly,)

    def get(self, request, *args, **kwargs):
        return Response({'status': 'green'})

class ModelPredition(APIView):
    permission_classes = (IsAuthenticatedOrReadOnly,)

    def get(self, request, *args, **kwargs):
        return Response({'status': 'green'})