from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from .models import Patient, Doctor, Appointment
from .serializers import PatientSerializer, DoctorSerializer, AppointmentSerializer

class PatientViewSet(viewsets.ModelViewSet):
    queryset = Patient.objects.all()
    serializer_class = PatientSerializer

class DoctorViewSet(viewsets.ModelViewSet):
    queryset = Doctor.objects.all()
    serializer_class = DoctorSerializer

    @action(detail=True, methods=['post'], url_path='set-availability')
    def set_availability(self, request, pk=None):
        doctor = self.get_object()
        is_available = request.data.get('is_available', None)

        if is_available is None:
            return Response({'error': 'Availability status not provided'}, status=status.HTTP_400_BAD_REQUEST)

        # Convert is_available to boolean
        is_available = str(is_available).lower() in ['true', '1', 't', 'yes']
        doctor.is_available = is_available
        doctor.save()

        return Response({'status': f"Doctor {'available' if is_available else 'unavailable'}"}, status=status.HTTP_200_OK)

class AppointmentViewSet(viewsets.ModelViewSet):
    queryset = Appointment.objects.all()
    serializer_class = AppointmentSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
            headers = self.get_success_headers(serializer.data)
            return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
        except ValidationError as e:
            # Custom handling of specific errors can be enhanced here
            if 'No available doctors at the moment.' in str(e.detail):
                return Response({"error": "No available doctors at the moment."}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'], url_path='complete')
    def complete_appointment(self, request, pk=None):
        appointment = self.get_object()
        if appointment.status == 'Scheduled':
            appointment.status = 'Completed'
            appointment.doctor.is_available = True
            appointment.doctor.save()
            appointment.save()
            return Response({'status': 'Appointment completed'}, status=status.HTTP_200_OK)
        else:
            return Response({'error': 'Appointment is not in a scheduled state'}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'], url_path='cancel')
    def cancel_appointment(self, request, pk=None):
        appointment = self.get_object()
        if appointment.status == 'Scheduled':
            appointment.status = 'Canceled'
            appointment.doctor.is_available = True
            appointment.doctor.save()
            appointment.save()
            return Response({'status': 'Appointment canceled'}, status=status.HTTP_200_OK)
        else:
            return Response({'error': 'Appointment is not in a scheduled state'}, status=status.HTTP_400_BAD_REQUEST)
