from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import CanManagePatientsPermission

from .permissions import IsOwner
from .serializers import PatientInputSerializer, PatientOutputSerializer
from .services import (
	create_patient,
	delete_patient,
	get_patient_by_id,
	list_patients_for_user,
	update_patient,
)


class PatientListCreateAPIView(APIView):
	permission_classes = [CanManagePatientsPermission]
	pagination_class = PageNumberPagination

	def get(self, request, *args, **kwargs):
		queryset = list_patients_for_user(user=request.user)

		paginator = self.pagination_class()
		page = paginator.paginate_queryset(queryset, request, view=self)
		if page is not None:
			serializer = PatientOutputSerializer(page, many=True)
			return paginator.get_paginated_response(serializer.data)

		serializer = PatientOutputSerializer(queryset, many=True)
		return Response(serializer.data, status=status.HTTP_200_OK)

	def post(self, request, *args, **kwargs):
		input_serializer = PatientInputSerializer(data=request.data)
		input_serializer.is_valid(raise_exception=True)

		patient = create_patient(user=request.user, data=input_serializer.validated_data)
		output_serializer = PatientOutputSerializer(patient)
		return Response(output_serializer.data, status=status.HTTP_201_CREATED)


class PatientDetailAPIView(APIView):
	permission_classes = [CanManagePatientsPermission, IsOwner]

	def _get_patient(self, pk):
		patient = get_patient_by_id(patient_id=pk)
		self.check_object_permissions(self.request, patient)
		return patient

	def get(self, request, pk, *args, **kwargs):
		patient = self._get_patient(pk)
		serializer = PatientOutputSerializer(patient)
		return Response(serializer.data, status=status.HTTP_200_OK)

	def put(self, request, pk, *args, **kwargs):
		patient = self._get_patient(pk)

		input_serializer = PatientInputSerializer(data=request.data)
		input_serializer.is_valid(raise_exception=True)

		patient = update_patient(patient=patient, data=input_serializer.validated_data)
		output_serializer = PatientOutputSerializer(patient)
		return Response(output_serializer.data, status=status.HTTP_200_OK)

	def delete(self, request, pk, *args, **kwargs):
		patient = self._get_patient(pk)
		delete_patient(patient=patient)
		return Response(status=status.HTTP_204_NO_CONTENT)
