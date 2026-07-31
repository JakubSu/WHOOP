package com.jakubsuran.aicoachapi.training.api.contracts;

import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;

public record ExerciseRequest(
		@NotBlank(message = "name is required.")
		@Size(max = 200, message = "name must be at most 200 characters.")
		String name,
		String prescriptionType,
		@Min(value = 0, message = "defaultSets cannot be negative.")
		@Max(value = Long.MAX_VALUE, message = "defaultSets is too large.")
		Long defaultSets,
		@Min(value = 0, message = "defaultReps cannot be negative.")
		@Max(value = Long.MAX_VALUE, message = "defaultReps is too large.")
		Long defaultReps,
		@Size(max = 200, message = "muscleGroup must be at most 200 characters.")
		String muscleGroup,
		@Min(value = 0, message = "defaultTime cannot be negative.")
		@Max(value = Long.MAX_VALUE, message = "defaultTime is too large.")
		Long defaultTime,
		String notes) {
}
