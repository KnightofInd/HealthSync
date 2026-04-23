from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import RegisterInputSerializer, UserOutputSerializer
from .services import register_user


class RegisterAPIView(APIView):
	permission_classes = [AllowAny]

	def post(self, request, *args, **kwargs):
		input_serializer = RegisterInputSerializer(data=request.data)
		input_serializer.is_valid(raise_exception=True)

		user = register_user(**input_serializer.validated_data)
		output_serializer = UserOutputSerializer(user)
		return Response(output_serializer.data, status=status.HTTP_201_CREATED)
