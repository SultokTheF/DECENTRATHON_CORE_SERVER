# ai_assistance/views.py

import torch
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import api_view
from .models import Context
from .serializers import ContextSerializer
from transformers import T5Tokenizer, T5ForConditionalGeneration
from sentence_transformers import SentenceTransformer, util

# Load Hugging Face models once at startup
tokenizer = T5Tokenizer.from_pretrained("Kyrmasch/t5-kazakh-qa")
model = T5ForConditionalGeneration.from_pretrained("Kyrmasch/t5-kazakh-qa")
model.eval()  # Set to evaluation mode

# Load the embedding model
embedding_model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')

class ContextViewSet(viewsets.ModelViewSet):
    """
    A viewset for viewing and editing context instances.
    """
    queryset = Context.objects.all()
    serializer_class = ContextSerializer

@api_view(['POST'])
def answer_question(request):
    """
    API endpoint to answer a question based on the most similar context.
    """
    try:
        # Extract the question from the request data
        question = request.data.get('question', '').strip()
        if not question:
            return Response({'error': 'Question is required.'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Retrieve all available contexts
        contexts = Context.objects.all()
        if not contexts.exists():
            return Response({'error': 'No contexts available.'}, status=status.HTTP_404_NOT_FOUND)
        
        # Prepare texts for embedding
        context_texts = [ctx.context for ctx in contexts]
        
        # Compute embeddings
        question_embedding = embedding_model.encode(question, convert_to_tensor=True)
        context_embeddings = embedding_model.encode(context_texts, convert_to_tensor=True)
        
        # Compute cosine similarities
        cosine_scores = util.pytorch_cos_sim(question_embedding, context_embeddings)[0]
        
        # Find the best matching context
        best_score, best_idx = torch.max(cosine_scores, dim=0)
        best_context = contexts[best_idx.item()]  # Convert tensor to integer
        
        # Generate answer using T5 model
        input_text = f"question: {question} context: {best_context.context}"
        input_ids = tokenizer.encode(input_text, return_tensors='pt')
        
        # Generate the answer
        with torch.no_grad():
            outputs = model.generate(input_ids=input_ids, max_length=128, num_beams=4, early_stopping=True)
        
        answer = tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        return Response({
            'question': question,
            'context': best_context.context,
            'answer': answer,
            'similarity_score': best_score.item()
        })
    
    except Exception as e:
        # Optional: Log the error for debugging purposes
        # import logging
        # logger = logging.getLogger(__name__)
        # logger.error(f"Error in answer_question: {e}", exc_info=True)
        
        return Response({
            'error': 'An unexpected error occurred.',
            'details': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
