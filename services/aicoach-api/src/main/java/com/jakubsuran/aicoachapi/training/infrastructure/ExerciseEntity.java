package com.jakubsuran.aicoachapi.training.infrastructure;

import com.jakubsuran.aicoachapi.training.domain.PrescriptionType;
import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.EnumType;
import jakarta.persistence.Enumerated;
import jakarta.persistence.Id;
import jakarta.persistence.PrePersist;
import jakarta.persistence.PreUpdate;
import jakarta.persistence.Table;
import java.time.Instant;
import java.util.UUID;

@Entity
@Table(name = "training_exercises")
class ExerciseEntity {
	@Id
	private UUID id;

	@Column(name = "user_id", nullable = false, length = 200)
	private String userId;

	@Column(nullable = false, length = 200)
	private String name;

	@Enumerated(EnumType.STRING)
	@Column(name = "prescription_type", nullable = false, length = 32)
	private PrescriptionType prescriptionType;

	@Column(name = "default_sets", nullable = false)
	private long defaultSets;

	@Column(name = "default_reps", nullable = false)
	private long defaultReps;

	@Column(name = "muscle_group", nullable = false, length = 200)
	private String muscleGroup;

	@Column(name = "default_time", nullable = false)
	private long defaultTime;

	@Column(nullable = false, columnDefinition = "text")
	private String notes;

	@Column(name = "created_at", nullable = false)
	private Instant createdAt;

	@Column(name = "updated_at", nullable = false)
	private Instant updatedAt;

	protected ExerciseEntity() {
	}

	ExerciseEntity(
			UUID id,
			String userId,
			String name,
			PrescriptionType prescriptionType,
			long defaultSets,
			long defaultReps,
			String muscleGroup,
			long defaultTime,
			String notes,
			Instant createdAt,
			Instant updatedAt) {
		this.id = id;
		this.userId = userId;
		this.name = name;
		this.prescriptionType = prescriptionType;
		this.defaultSets = defaultSets;
		this.defaultReps = defaultReps;
		this.muscleGroup = muscleGroup;
		this.defaultTime = defaultTime;
		this.notes = notes;
		this.createdAt = createdAt;
		this.updatedAt = updatedAt;
	}

	@PrePersist
	void prePersist() {
		var now = Instant.now();
		if (createdAt == null) {
			createdAt = now;
		}
		if (updatedAt == null) {
			updatedAt = now;
		}
	}

	@PreUpdate
	void preUpdate() {
		updatedAt = Instant.now();
	}

	UUID getId() {
		return id;
	}

	String getUserId() {
		return userId;
	}

	String getName() {
		return name;
	}

	PrescriptionType getPrescriptionType() {
		return prescriptionType;
	}

	long getDefaultSets() {
		return defaultSets;
	}

	long getDefaultReps() {
		return defaultReps;
	}

	String getMuscleGroup() {
		return muscleGroup;
	}

	long getDefaultTime() {
		return defaultTime;
	}

	String getNotes() {
		return notes;
	}

	Instant getCreatedAt() {
		return createdAt;
	}

	Instant getUpdatedAt() {
		return updatedAt;
	}
}
