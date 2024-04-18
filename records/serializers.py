from rest_framework import serializers
from django.db.models import Q
from .models import Patient, Doctor, Appointment

class PatientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Patient
        fields = '__all__'

class DoctorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Doctor
        fields = '__all__'

class AppointmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Appointment
        fields = '__all__'
        extra_kwargs = {'doctor': {'required': False}}  # Doctor is not required in the request

    def validate(self, data):
        # Ensure the appointment creation does not duplicate doctor-patient pair with 'Scheduled' status
        if 'doctor' not in data:  # If doctor not explicitly given, assume first available will be assigned
            doctor = Doctor.objects.filter(is_available=True).first()
            if not doctor:
                raise serializers.ValidationError({"doctor": "No available doctors at the moment."})
            data['doctor'] = doctor
        else:
            doctor = data['doctor']

        # Check for existing scheduled appointment with the same doctor-patient pair
        if Appointment.objects.filter(doctor=doctor, patient=data['patient'], status='Scheduled').exists():
            raise serializers.ValidationError("This doctor already has a scheduled appointment with this patient.")
        
        return data

    def create(self, validated_data):
        # Assign the doctor from validated_data or find the first available
        doctor = validated_data.get('doctor') or Doctor.objects.filter(is_available=True).first()
        if not doctor:
            raise serializers.ValidationError({"doctor": "No available doctors at the moment."})
        
        # Create the appointment
        appointment = Appointment.objects.create(**validated_data)
        
        # Mark the doctor as unavailable
        doctor.is_available = False
        doctor.save()

        return appointment
