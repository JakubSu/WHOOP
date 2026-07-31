package com.jakubsuran.aicoachapi.training.api.converters;

import com.jakubsuran.aicoachapi.shared.application.ValidationException;
import com.jakubsuran.aicoachapi.training.api.contracts.ExerciseRequest;
import com.jakubsuran.aicoachapi.training.api.contracts.ExerciseResponse;
import com.jakubsuran.aicoachapi.training.domain.Exercise;
import com.jakubsuran.aicoachapi.training.domain.ExercisePatch;
import com.jakubsuran.aicoachapi.training.domain.PrescriptionType;
import java.util.Map;
import java.util.Optional;
import java.util.UUID;
import org.springframework.stereotype.Component;

@Component
public class ExerciseContractConverter {
	public Exercise toNewDomain(ExerciseRequest request, String userId) {
		return Exercise.create(
				userId,
				request.name(),
				toPrescriptionType(request.prescriptionType()),
				request.defaultSets(),
				request.defaultReps(),
				request.muscleGroup(),
				request.defaultTime(),
				request.notes());
	}

	public Exercise toReplacementDomain(UUID id, ExerciseRequest request, String userId) {
		return Exercise.create(
				id,
				userId,
				request.name(),
				toPrescriptionType(request.prescriptionType()),
				request.defaultSets(),
				request.defaultReps(),
				request.muscleGroup(),
				request.defaultTime(),
				request.notes());
	}

	public ExercisePatch toPatchDomain(Map<String, Object> raw) {
		return new ExercisePatch(
				optionalString(raw, "name"),
				optionalPrescriptionType(raw, "prescriptionType"),
				optionalLong(raw, "defaultSets"),
				optionalLong(raw, "defaultReps"),
				optionalString(raw, "muscleGroup"),
				optionalLong(raw, "defaultTime"),
				optionalString(raw, "notes"));
	}

	public ExerciseResponse toResponse(Exercise exercise) {
		return new ExerciseResponse(
				exercise.id(),
				exercise.name(),
				exercise.prescriptionType().getValue(),
				exercise.defaultSets(),
				exercise.defaultReps(),
				exercise.muscleGroup(),
				exercise.defaultTime(),
				exercise.notes());
	}

	private PrescriptionType toPrescriptionType(String value) {
		try {
			return PrescriptionType.fromValue(value);
		} catch (IllegalArgumentException exception) {
			throw new ValidationException(exception.getMessage());
		}
	}

	private Optional<PrescriptionType> optionalPrescriptionType(Map<String, Object> raw, String fieldName) {
		if (!raw.containsKey(fieldName)) {
			return Optional.empty();
		}
		var value = raw.get(fieldName);
		return Optional.of(toPrescriptionType(value == null ? null : value.toString()));
	}

	private Optional<String> optionalString(Map<String, Object> raw, String fieldName) {
		if (!raw.containsKey(fieldName)) {
			return Optional.empty();
		}
		var value = raw.get(fieldName);
		return Optional.of(value == null ? "" : value.toString());
	}

	private Optional<Long> optionalLong(Map<String, Object> raw, String fieldName) {
		if (!raw.containsKey(fieldName)) {
			return Optional.empty();
		}
		var value = raw.get(fieldName);
		if (value == null) {
			return Optional.of(0L);
		}
		if (value instanceof Number number) {
			return Optional.of(number.longValue());
		}
		try {
			return Optional.of(Long.parseLong(value.toString()));
		} catch (NumberFormatException exception) {
			throw new ValidationException(fieldName + " must be a number.");
		}
	}
}
