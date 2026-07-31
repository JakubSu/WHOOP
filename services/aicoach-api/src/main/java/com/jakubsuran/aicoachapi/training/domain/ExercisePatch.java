package com.jakubsuran.aicoachapi.training.domain;

import java.util.Optional;

public record ExercisePatch(
		Optional<String> name,
		Optional<PrescriptionType> prescriptionType,
		Optional<Long> defaultSets,
		Optional<Long> defaultReps,
		Optional<String> muscleGroup,
		Optional<Long> defaultTime,
		Optional<String> notes) {
}
