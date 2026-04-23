from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import CanManageDoctorsPermission, CanViewDoctorsPermission

from .serializers import DoctorInputSerializer, DoctorOutputSerializer
from .services import (
	create_doctor,
	delete_doctor,
	get_doctor_by_id,
	list_doctors,
	update_doctor,
)


class DoctorListCreateAPIView(APIView):
	pagination_class = PageNumberPagination

	def get_permissions(self):
		if self.request.method == "GET":
			return [CanViewDoctorsPermission()]

		return [CanManageDoctorsPermission()]

	def get(self, request, *args, **kwargs):
		queryset = list_doctors()

		paginator = self.pagination_class()
		page = paginator.paginate_queryset(queryset, request, view=self)
		if page is not None:
			serializer = DoctorOutputSerializer(page, many=True)
			return paginator.get_paginated_response(serializer.data)

		serializer = DoctorOutputSerializer(queryset, many=True)
		return Response(serializer.data, status=status.HTTP_200_OK)

	def post(self, request, *args, **kwargs):
		input_serializer = DoctorInputSerializer(data=request.data)
		input_serializer.is_valid(raise_exception=True)

		doctor = create_doctor(data=input_serializer.validated_data)
		output_serializer = DoctorOutputSerializer(doctor)
		return Response(output_serializer.data, status=status.HTTP_201_CREATED)


class DoctorDetailAPIView(APIView):
	def get_permissions(self):
		if self.request.method == "GET":
			return [CanViewDoctorsPermission()]

		return [CanManageDoctorsPermission()]

	def get(self, request, pk, *args, **kwargs):
		doctor = get_doctor_by_id(doctor_id=pk)
		serializer = DoctorOutputSerializer(doctor)
		return Response(serializer.data, status=status.HTTP_200_OK)

	def put(self, request, pk, *args, **kwargs):
		doctor = get_doctor_by_id(doctor_id=pk)

		input_serializer = DoctorInputSerializer(data=request.data)
		input_serializer.is_valid(raise_exception=True)

		doctor = update_doctor(doctor=doctor, data=input_serializer.validated_data)
		output_serializer = DoctorOutputSerializer(doctor)
		return Response(output_serializer.data, status=status.HTTP_200_OK)

	def delete(self, request, pk, *args, **kwargs):
		doctor = get_doctor_by_id(doctor_id=pk)
		delete_doctor(doctor=doctor)
		return Response(status=status.HTTP_204_NO_CONTENT)
