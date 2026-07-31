package com.jakubsuran.aicoachapi.training.domain;

import java.util.List;
import java.util.Optional;
import java.util.UUID;

public interface ExerciseRepository {
	List<Exercise> findVisibleTo(String userId);

	Optional<Exercise> findVisibleById(UUID id, String userId);

	Exercise save(Exercise exercise);

	void delete(Exercise exercise);
}
