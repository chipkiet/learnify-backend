import os
from django.shortcuts import render
import logging
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from apps.documents.models import Document
from apps.documents.serializers import DocumentUploadSerializer, DocumentListSerializer, DocumentDetailSerializer, DocumentUpdateSerializer
from apps.documents.services.extractor import extract_document
from django.http import FileResponse, Http404


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

    def get(self, request, pk):
        try:
            document = Document.objects.get(pk=pk, user=request.user)
            serializer = DocumentDetailSerializer(document)  # ← đổi sang Detail
            return Response(serializer.data)
        except Document.DoesNotExist:
            return Response({"error": "Not found"}, status=status.HTTP_404_NOT_FOUND)

    def patch(self, request, pk):
        try:
            document = Document.objects.get(pk=pk, user=request.user)
            serializer = DocumentUpdateSerializer(
                document, data=request.data, partial=True
            )
            if serializer.is_valid():
                serializer.save()
                return Response(DocumentDetailSerializer(document).data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Document.DoesNotExist:
            return Response({"error": "Not found"}, status=status.HTTP_404_NOT_FOUND)

    def delete(self, request, pk):
        try:
            document = Document.objects.get(pk=pk, user=request.user)
            document.file.delete()
            document.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Document.DoesNotExist:
            return Response({"error": "Not found"}, status=status.HTTP_404_NOT_FOUND)

class DocumentPreviewView(APIView): 
    permission_classes = [IsAuthenticated]
    
    def get(self, request, pk ) :
        try :
            document = Document.objects.get(pk=pk, user=request.user)
        except Document.DoesNotExist:
            return Response(
                {"error": "Not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        if document.status != Document.Status.DONE:
            return Response (
                {
                    "error": "Document chưa sẵn sàng baby ơi !!!",
                    "status": document.status
                },
                status = status.HTTP_400_BAD_REQUEST
            )
        return Response({
            "id": document.id,
            "title": document.title,
            "file_type": document.file_type,
            "word_count": document.word_count,
            "char_count": document.char_count,
            "page_count": document.page_count,
            "content": document.extracted_text,
        })