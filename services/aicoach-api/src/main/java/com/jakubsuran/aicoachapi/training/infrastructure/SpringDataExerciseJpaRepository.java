package com.jakubsuran.aicoachapi.training.infrastructure;

import java.util.List;
import java.util.Optional;
import java.util.UUID;
import org.springframework.data.jpa.repository.JpaRepository;

public interface SpringDataExerciseJpaRepository extends JpaRepository<ExerciseEntity, UUID> {
	List<ExerciseEntity> findByUserIdInOrderByNameAsc(List<String> userIds);

	Optional<ExerciseEntity> findByIdAndUserIdIn(UUID id, List<String> userIds);
}
