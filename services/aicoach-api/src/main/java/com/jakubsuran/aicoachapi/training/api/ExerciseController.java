package com.jakubsuran.aicoachapi.training.api;

import com.jakubsuran.aicoachapi.shared.security.CurrentUserProvider;
import com.jakubsuran.aicoachapi.training.api.contracts.ExerciseRequest;
import com.jakubsuran.aicoachapi.training.api.contracts.ExerciseResponse;
import com.jakubsuran.aicoachapi.training.api.converters.ExerciseContractConverter;
import com.jakubsuran.aicoachapi.training.application.ExerciseService;
import jakarta.validation.Valid;
import java.util.List;
import java.util.Map;
import java.util.UUID;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PatchMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@Validated
@RequestMapping("/api/v1/exercises")
public class ExerciseController {
	private final ExerciseService exercises;
	private final CurrentUserProvider currentUserProvider;
	private final ExerciseContractConverter converter;

	public ExerciseController(
			ExerciseService exercises,
			CurrentUserProvider currentUserProvider,
			ExerciseContractConverter converter) {
		this.exercises = exercises;
		this.currentUserProvider = currentUserProvider;
		this.converter = converter;
	}

	@GetMapping({"", "/"})
	List<ExerciseResponse> list() {
		var userId = currentUserProvider.currentUserId();
		return exercises.list(userId).stream().map(converter::toResponse).toList();
	}

	@PostMapping({"", "/"})
	ResponseEntity<ExerciseResponse> create(@Valid @RequestBody ExerciseRequest request) {
		var userId = currentUserProvider.currentUserId();
		var exercise = exercises.create(converter.toNewDomain(request, userId));
		return ResponseEntity.status(HttpStatus.CREATED).body(converter.toResponse(exercise));
	}

	@GetMapping({"/{id}", "/{id}/"})
	ExerciseResponse get(@PathVariable UUID id) {
		var userId = currentUserProvider.currentUserId();
		return converter.toResponse(exercises.get(id, userId));
	}

	@PutMapping({"/{id}", "/{id}/"})
	ExerciseResponse replace(@PathVariable UUID id, @Valid @RequestBody ExerciseRequest request) {
		var userId = currentUserProvider.currentUserId();
		return converter.toResponse(exercises.replace(id, userId, converter.toReplacementDomain(id, request, userId)));
	}

	@PatchMapping({"/{id}", "/{id}/"})
	ExerciseResponse patch(@PathVariable UUID id, @RequestBody Map<String, Object> body) {
		var userId = currentUserProvider.currentUserId();
		return converter.toResponse(exercises.patch(id, userId, converter.toPatchDomain(body)));
	}

	@DeleteMapping({"/{id}", "/{id}/"})
	ResponseEntity<Void> delete(@PathVariable UUID id) {
		var userId = currentUserProvider.currentUserId();
		exercises.delete(id, userId);
		return ResponseEntity.noContent().build();
	}
}
