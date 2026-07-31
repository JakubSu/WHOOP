package com.jakubsuran.aicoachapi.shared.api;

import com.jakubsuran.aicoachapi.shared.application.NotFoundException;
import com.jakubsuran.aicoachapi.shared.application.ValidationException;
import com.jakubsuran.aicoachapi.shared.security.AuthenticationRequiredException;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;

@RestControllerAdvice
public class GlobalExceptionHandler {

	@ExceptionHandler(AuthenticationRequiredException.class)
	ResponseEntity<ApiErrorResponse> handleAuthenticationRequired(AuthenticationRequiredException exception) {
		return ResponseEntity.status(HttpStatus.UNAUTHORIZED).body(new ApiErrorResponse(exception.getMessage()));
	}

	@ExceptionHandler(NotFoundException.class)
	ResponseEntity<ApiErrorResponse> handleNotFound(NotFoundException exception) {
		return ResponseEntity.status(HttpStatus.NOT_FOUND).body(new ApiErrorResponse(exception.getMessage()));
	}

	@ExceptionHandler(ValidationException.class)
	ResponseEntity<ApiErrorResponse> handleValidation(ValidationException exception) {
		return ResponseEntity.badRequest().body(new ApiErrorResponse(exception.getMessage()));
	}

	@ExceptionHandler(MethodArgumentNotValidException.class)
	ResponseEntity<ApiErrorResponse> handleMethodArgumentNotValid(MethodArgumentNotValidException exception) {
		var fieldError = exception.getBindingResult().getFieldError();
		var message = fieldError == null ? "Validation failed." : fieldError.getDefaultMessage();
		return ResponseEntity.badRequest().body(new ApiErrorResponse(message));
	}
}
