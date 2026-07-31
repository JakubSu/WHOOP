package com.jakubsuran.aicoachapi.training.application;

import com.jakubsuran.aicoachapi.shared.application.NotFoundException;
import com.jakubsuran.aicoachapi.training.domain.Exercise;
import com.jakubsuran.aicoachapi.training.domain.ExercisePatch;
import com.jakubsuran.aicoachapi.training.domain.ExerciseRepository;
import java.util.List;
import java.util.UUID;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
public class ExerciseService {
	private static final String NOT_FOUND_MESSAGE = "Exercise was not found.";

	private final ExerciseRepository exercises;

	public ExerciseService(ExerciseRepository exercises) {
		this.exercises = exercises;
	}

	@Transactional(readOnly = true)
	public List<Exercise> list(String userId) {
		return exercises.findVisibleTo(userId);
	}

	@Transactional(readOnly = true)
	public Exercise get(UUID id, String userId) {
		return exercises.findVisibleById(id, userId)
				.orElseThrow(() -> new NotFoundException(NOT_FOUND_MESSAGE));
	}

	@Transactional
	public Exercise create(Exercise exercise) {
		return exercises.save(exercise);
	}

	@Transactional
	public Exercise replace(UUID id, String userId, Exercise replacement) {
		var exercise = getMutableExercise(id, userId);
		exercise.replace(replacement);
		return exercises.save(exercise);
	}

	@Transactional
	public Exercise patch(UUID id, String userId, ExercisePatch patch) {
		var exercise = getMutableExercise(id, userId);
		exercise.patch(patch);
		return exercises.save(exercise);
	}

	@Transactional
	public void delete(UUID id, String userId) {
		var exercise = getMutableExercise(id, userId);
		exercises.delete(exercise);
	}

	private Exercise getMutableExercise(UUID id, String userId) {
		var exercise = get(id, userId);
		if (exercise.isShared() || !exercise.isOwnedBy(userId)) {
			throw new NotFoundException(NOT_FOUND_MESSAGE);
		}
		return exercise;
	}
}
