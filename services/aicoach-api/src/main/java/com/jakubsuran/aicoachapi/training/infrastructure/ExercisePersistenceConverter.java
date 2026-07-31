package com.jakubsuran.aicoachapi.training.infrastructure;

import com.jakubsuran.aicoachapi.training.domain.Exercise;
import org.springframework.stereotype.Component;

@Component
class ExercisePersistenceConverter {
	Exercise toDomain(ExerciseEntity entity) {
		return Exercise.restore(
				entity.getId(),
				entity.getUserId(),
				entity.getName(),
				entity.getPrescriptionType(),
				entity.getDefaultSets(),
				entity.getDefaultReps(),
				entity.getMuscleGroup(),
				entity.getDefaultTime(),
				entity.getNotes(),
				entity.getCreatedAt(),
				entity.getUpdatedAt());
	}

	ExerciseEntity toEntity(Exercise exercise) {
		return new ExerciseEntity(
				exercise.id(),
				exercise.userId(),
				exercise.name(),
				exercise.prescriptionType(),
				exercise.defaultSets(),
				exercise.defaultReps(),
				exercise.muscleGroup(),
				exercise.defaultTime(),
				exercise.notes(),
				exercise.createdAt(),
				exercise.updatedAt());
	}
}
