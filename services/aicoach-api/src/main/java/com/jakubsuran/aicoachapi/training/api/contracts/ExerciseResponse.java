package com.jakubsuran.aicoachapi.training.api.contracts;

import java.util.UUID;

public record ExerciseResponse(
		UUID id,
		String name,
		String prescriptionType,
		long defaultSets,
		long defaultReps,
		String muscleGroup,
		long defaultTime,
		String notes) {
}
