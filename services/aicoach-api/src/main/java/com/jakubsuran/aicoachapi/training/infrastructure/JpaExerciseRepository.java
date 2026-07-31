package com.jakubsuran.aicoachapi.training.infrastructure;

import com.jakubsuran.aicoachapi.training.domain.Exercise;
import com.jakubsuran.aicoachapi.training.domain.ExerciseRepository;
import java.util.List;
import java.util.Optional;
import java.util.UUID;
import org.springframework.stereotype.Repository;

@Repository
class JpaExerciseRepository implements ExerciseRepository {
	private static final String SHARED_USER_ID = "";

	private final SpringDataExerciseJpaRepository repository;
	private final ExercisePersistenceConverter converter;

	JpaExerciseRepository(SpringDataExerciseJpaRepository repository, ExercisePersistenceConverter converter) {
		this.repository = repository;
		this.converter = converter;
	}

	@Override
	public List<Exercise> findVisibleTo(String userId) {
		return repository.findByUserIdInOrderByNameAsc(List.of(userId, SHARED_USER_ID)).stream()
				.map(converter::toDomain)
				.toList();
	}

	@Override
	public Optional<Exercise> findVisibleById(UUID id, String userId) {
		return repository.findByIdAndUserIdIn(id, List.of(userId, SHARED_USER_ID)).map(converter::toDomain);
	}

	@Override
	public Exercise save(Exercise exercise) {
		return converter.toDomain(repository.save(converter.toEntity(exercise)));
	}

	@Override
	public void delete(Exercise exercise) {
		repository.deleteById(exercise.id());
	}
}
