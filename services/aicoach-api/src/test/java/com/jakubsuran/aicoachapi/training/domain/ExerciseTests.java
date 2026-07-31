package com.jakubsuran.aicoachapi.training.domain;

import com.jakubsuran.aicoachapi.shared.application.ValidationException;
import org.junit.jupiter.api.Test;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

class ExerciseTests {
	@Test
	void strengthExerciseRejectsDefaultTime() {
		assertThatThrownBy(() -> Exercise.create("user-1", "Bench Press", PrescriptionType.STRENGTH, 4L, 8L, "Chest", 30L, ""))
				.isInstanceOf(ValidationException.class)
				.hasMessage("Strength exercises cannot use a default time.");
	}

	@Test
	void timedExerciseAcceptsDefaultTime() {
		var exercise = Exercise.create("user-1", "Plank", PrescriptionType.TIMED, null, null, "Core", 45L, null);

		assertThat(exercise.defaultTime()).isEqualTo(45);
		assertThat(exercise.defaultSets()).isZero();
		assertThat(exercise.defaultReps()).isZero();
		assertThat(exercise.notes()).isEmpty();
	}
}
