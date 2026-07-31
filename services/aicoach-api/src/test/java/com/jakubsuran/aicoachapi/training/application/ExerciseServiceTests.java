package com.jakubsuran.aicoachapi.training.application;

import com.jakubsuran.aicoachapi.shared.application.NotFoundException;
import com.jakubsuran.aicoachapi.training.domain.Exercise;
import com.jakubsuran.aicoachapi.training.domain.ExercisePatch;
import com.jakubsuran.aicoachapi.training.domain.ExerciseRepository;
import com.jakubsuran.aicoachapi.training.domain.PrescriptionType;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;
import java.util.Optional;
import java.util.UUID;
import org.junit.jupiter.api.Test;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

class ExerciseServiceTests {
	private final InMemoryExerciseRepository repository = new InMemoryExerciseRepository();
	private final ExerciseService service = new ExerciseService(repository);

	@Test
	void createAssignsCurrentUser() {
		var exercise = service.create(Exercise.create("user-1", "Push-Up", null, 3L, 12L, "Chest", 0L, "Keep core tight."));

		assertThat(exercise.userId()).isEqualTo("user-1");
		assertThat(exercise.prescriptionType()).isEqualTo(PrescriptionType.STRENGTH);
		assertThat(repository.saved).contains(exercise);
	}

	@Test
	void listReturnsUserOwnedAndSharedExercises() {
		repository.save(Exercise.create("user-1", "Mine", null, null, null, null, null, null));
		repository.save(Exercise.create("", "Shared", null, null, null, null, null, null));
		repository.save(Exercise.create("user-2", "Theirs", null, null, null, null, null, null));

		assertThat(service.list("user-1")).extracting(Exercise::name).containsExactly("Mine", "Shared");
	}

	@Test
	void patchPreservesUnspecifiedFields() {
		var exercise = repository.save(Exercise.create("user-1", "Plank", PrescriptionType.TIMED, null, null, "Core", 30L, "Brace."));

		var updated = service.patch(
				exercise.id(),
				"user-1",
				new ExercisePatch(
						Optional.of("Long Plank"),
						Optional.empty(),
						Optional.empty(),
						Optional.empty(),
						Optional.empty(),
						Optional.of(45L),
						Optional.empty()));

		assertThat(updated.name()).isEqualTo("Long Plank");
		assertThat(updated.prescriptionType()).isEqualTo(PrescriptionType.TIMED);
		assertThat(updated.muscleGroup()).isEqualTo("Core");
		assertThat(updated.notes()).isEqualTo("Brace.");
		assertThat(updated.defaultTime()).isEqualTo(45);
	}

	@Test
	void updateRejectsSharedExercise() {
		var shared = repository.save(Exercise.create("", "Shared", null, null, null, null, null, null));

		var replacement = Exercise.create(shared.id(), "user-1", "Updated", null, null, null, null, null, null);

		assertThatThrownBy(() -> service.replace(shared.id(), "user-1", replacement))
				.isInstanceOf(NotFoundException.class)
				.hasMessage("Exercise was not found.");
	}

	private static class InMemoryExerciseRepository implements ExerciseRepository {
		private final List<Exercise> saved = new ArrayList<>();

		@Override
		public List<Exercise> findVisibleTo(String userId) {
			return saved.stream()
					.filter(exercise -> exercise.userId().equals(userId) || exercise.userId().isBlank())
					.sorted(Comparator.comparing(Exercise::name))
					.toList();
		}

		@Override
		public Optional<Exercise> findVisibleById(UUID id, String userId) {
			return saved.stream()
					.filter(exercise -> exercise.id().equals(id))
					.filter(exercise -> exercise.userId().equals(userId) || exercise.userId().isBlank())
					.findFirst();
		}

		@Override
		public Exercise save(Exercise exercise) {
			saved.removeIf(existing -> existing.id().equals(exercise.id()));
			saved.add(exercise);
			return exercise;
		}

		@Override
		public void delete(Exercise exercise) {
			saved.removeIf(existing -> existing.id().equals(exercise.id()));
		}
	}
}
