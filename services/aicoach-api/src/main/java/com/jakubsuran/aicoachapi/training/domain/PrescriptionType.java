package com.jakubsuran.aicoachapi.training.domain;

public enum PrescriptionType {
	STRENGTH("strength"),
	TIMED("timed");

	private final String value;

	PrescriptionType(String value) {
		this.value = value;
	}

	public String getValue() {
		return value;
	}

	public static PrescriptionType fromValue(String value) {
		if (value == null || value.isBlank()) {
			return STRENGTH;
		}
		for (var type : values()) {
			if (type.value.equalsIgnoreCase(value)) {
				return type;
			}
		}
		throw new IllegalArgumentException("Unsupported prescriptionType.");
	}
}
