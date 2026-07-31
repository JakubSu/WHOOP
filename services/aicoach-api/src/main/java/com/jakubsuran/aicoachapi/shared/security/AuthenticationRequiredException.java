package com.jakubsuran.aicoachapi.shared.security;

public class AuthenticationRequiredException extends RuntimeException {
	public AuthenticationRequiredException(String message) {
		super(message);
	}
}
