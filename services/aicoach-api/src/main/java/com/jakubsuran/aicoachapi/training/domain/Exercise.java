package com.jakubsuran.aicoachapi.training.domain;

import com.jakubsuran.aicoachapi.shared.application.ValidationException;
import java.time.Instant;
import java.util.UUID;

public class Exercise {
	private final UUID id;
	private final String userId;
	private String name;
	private PrescriptionType prescriptionType;
	private long defaultSets;
	private long defaultReps;
	private String muscleGroup;
	private long defaultTime;
	private String notes;
	private final Instant createdAt;
	private Instant updatedAt;

	private Exercise(
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
		this.userId = normalizeText(userId);
		this.name = requireName(name);
		this.prescriptionType = prescriptionType == null ? PrescriptionType.STRENGTH : prescriptionType;
		this.defaultSets = requireNonNegative(defaultSets, "defaultSets");
		this.defaultReps = requireNonNegative(defaultReps, "defaultReps");
		this.muscleGroup = normalizeText(muscleGroup);
		this.defaultTime = requireNonNegative(defaultTime, "defaultTime");
		this.notes = normalizeText(notes);
		this.createdAt = createdAt;
		this.updatedAt = updatedAt;
		validateDefaults();
	}

	public static Exercise create(
			String userId,
			String name,
			PrescriptionType prescriptionType,
			Long defaultSets,
			Long defaultReps,
			String muscleGroup,
			Long defaultTime,
			String notes) {
		var now = Instant.now();
		return new Exercise(
				UUID.randomUUID(),
				userId,
				name,
				prescriptionType,
				defaultSets == null ? 0 : defaultSets,
				defaultReps == null ? 0 : defaultReps,
				muscleGroup,
				defaultTime == null ? 0 : defaultTime,
				notes,
				now,
				now);
	}

	public static Exercise create(
			UUID id,
			String userId,
			String name,
			PrescriptionType prescriptionType,
			Long defaultSets,
			Long defaultReps,
			String muscleGroup,
			Long defaultTime,
			String notes) {
		var now = Instant.now();
		return new Exercise(
				id,
				userId,
				name,
				prescriptionType,
				defaultSets == null ? 0 : defaultSets,
				defaultReps == null ? 0 : defaultReps,
				muscleGroup,
				defaultTime == null ? 0 : defaultTime,
				notes,
				now,
				now);
	}

	public static Exercise restore(
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
		return new Exercise(
				id,
				userId,
				name,
				prescriptionType,
				defaultSets,
				defaultReps,
				muscleGroup,
				defaultTime,
				notes,
				createdAt,
				updatedAt);
	}

	public void replace(
			Exercise replacement) {
		this.name = replacement.name();
		this.prescriptionType = replacement.prescriptionType();
		this.defaultSets = replacement.defaultSets();
		this.defaultReps = replacement.defaultReps();
		this.muscleGroup = replacement.muscleGroup();
		this.defaultTime = replacement.defaultTime();
		this.notes = replacement.notes();
		this.updatedAt = Instant.now();
		validateDefaults();
	}

	public void patch(ExercisePatch patch) {
		if (patch.name().isPresent()) {
			this.name = requireName(patch.name().get());
		}
		if (patch.prescriptionType().isPresent()) {
			this.prescriptionType = patch.prescriptionType().get();
		}
		if (patch.defaultSets().isPresent()) {
			this.defaultSets = requireNonNegative(patch.defaultSets().get(), "defaultSets");
		}
		if (patch.defaultReps().isPresent()) {
			this.defaultReps = requireNonNegative(patch.defaultReps().get(), "defaultReps");
		}
		if (patch.muscleGroup().isPresent()) {
			this.muscleGroup = normalizeText(patch.muscleGroup().get());
		}
		if (patch.defaultTime().isPresent()) {
			this.defaultTime = requireNonNegative(patch.defaultTime().get(), "defaultTime");
		}
		if (patch.notes().isPresent()) {
			this.notes = normalizeText(patch.notes().get());
		}
		this.updatedAt = Instant.now();
		validateDefaults();
	}

	public boolean isShared() {
		return userId.isBlank();
	}

	public boolean isOwnedBy(String ownerUserId) {
		return userId.equals(ownerUserId);
	}

	private void validateDefaults() {
		if (prescriptionType == PrescriptionType.STRENGTH && defaultTime > 0) {
			throw new ValidationException("Strength exercises cannot use a default time.");
		}
	}

	private static String requireName(String value) {
		var normalized = normalizeText(value);
		if (normalized.isBlank()) {
			throw new ValidationException("name is required.");
		}
		if (normalized.length() > 200) {
			throw new ValidationException("name must be at most 200 characters.");
		}
		return normalized;
	}

	private static long requireNonNegative(long value, String fieldName) {
		if (value < 0) {
			throw new ValidationException(fieldName + " cannot be negative.");
		}
		return value;
	}

	private static String normalizeText(String value) {
		return value == null ? "" : value.trim();
	}

	public UUID id() {
		return id;
	}

	public String userId() {
		return userId;
	}

	public String name() {
		return name;
	}

	public PrescriptionType prescriptionType() {
		return prescriptionType;
	}

	public long defaultSets() {
		return defaultSets;
	}

	public long defaultReps() {
		return defaultReps;
	}

	public String muscleGroup() {
		return muscleGroup;
	}

	public long defaultTime() {
		return defaultTime;
	}

	public String notes() {
		return notes;
	}

	public Instant createdAt() {
		return createdAt;
	}

	public Instant updatedAt() {
		return updatedAt;
	}
}
