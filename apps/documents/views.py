from django.shortcuts import render
import logging
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from apps.documents.models import Document
from apps.documents.serializers import DocumentUploadSerializer, DocumentListSerializer
from apps.documents.services.extractor import extract_document

logger = logging.getLogger(__name__)

class DocumentUploadView(APIView): 
    permission_classes = [IsAuthenticated]
    
    def post(self, request) :
        serializer = DocumentUploadSerializer(
            data=request.data,
            context={'request': request}
        )
        if serializer.is_valid() :
            document = serializer.save()
            logger.info(f"Document uploaded : {document.title} by { request.user.email}")
            
            success = extract_document(document)
            if not success : 
                logger.warning(f"Extraction thất bại rồi con vk ơi for document_id={document.id}")
            
            return Response (
                DocumentListSerializer(document).data,
                status = status.HTTP_201_CREATED
            )
            
        logger.error(f"Uploaded failed roi cung oi !! Error : {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class DocumentListView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request) :
        documents = Document.objects.filter(user=request.user)
        serializer = DocumentListSerializer(documents, many = True)
        return Response(serializer.data)
    
class DocumentDetailView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request, pk) :
        try :
            document = Document.objects.get(pk = pk, user = request.user)
            serializer = DocumentListSerializer(document)
            return Response(serializer.data)
        
        except Document.DoesNotExist :
            return Response(
                {"error": "Document not found to watch detail con vk oi"},
                status = status.HTTP_404_NOT_FOUND
            )
    
    def delete(self, request, pk) :
        try :
            document = Document.objects.get(pk = pk, user = request.user)
            document.file.delete()  # xoa file that tren disk
            document.delete()       # xoa record trong
            logger.info(f"Document deleted: {pk} by {request.user.email}")
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Document.DoesNotExist :
            return Response (
                {"error": "Document can not found to delete con vk oi"},
                status = status.HTTP_404_NOT_FOUND
            )