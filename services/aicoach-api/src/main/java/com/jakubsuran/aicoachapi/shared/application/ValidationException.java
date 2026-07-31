package com.jakubsuran.aicoachapi.shared.application;

public class ValidationException extends RuntimeException {
	public ValidationException(String message) {
		super(message);
	}
}
