from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import CanManageMappingsPermission, CanViewMappingsPermission

from .serializers import (
	MappingFilterSerializer,
	MappingInputSerializer,
	MappingOutputSerializer,
)
from .services import assign_doctor_to_patient, list_mappings_for_user


class MappingListCreateAPIView(APIView):
	pagination_class = PageNumberPagination

	def get_permissions(self):
		if self.request.method == "GET":
			return [CanViewMappingsPermission()]

		return [CanManageMappingsPermission()]

	def get(self, request, *args, **kwargs):
		filter_serializer = MappingFilterSerializer(data=request.query_params)
		filter_serializer.is_valid(raise_exception=True)

		queryset = list_mappings_for_user(
			user=request.user,
			patient_id=filter_serializer.validated_data.get("patient_id"),
		)

		paginator = self.pagination_class()
		page = paginator.paginate_queryset(queryset, request, view=self)
		if page is not None:
			serializer = MappingOutputSerializer(page, many=True)
			return paginator.get_paginated_response(serializer.data)

		serializer = MappingOutputSerializer(queryset, many=True)
		return Response(serializer.data, status=status.HTTP_200_OK)

	def post(self, request, *args, **kwargs):
		input_serializer = MappingInputSerializer(data=request.data)
		input_serializer.is_valid(raise_exception=True)

		mapping = assign_doctor_to_patient(
			user=request.user,
			patient_id=input_serializer.validated_data["patient_id"],
			doctor_id=input_serializer.validated_data["doctor_id"],
			slot_start=input_serializer.validated_data.get("slot_start"),
			slot_end=input_serializer.validated_data.get("slot_end"),
		)
		output_serializer = MappingOutputSerializer(mapping)
		return Response(output_serializer.data, status=status.HTTP_201_CREATED)
