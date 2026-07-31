package com.jakubsuran.aicoachapi.training.api;

import com.jakubsuran.aicoachapi.training.domain.Exercise;
import com.jakubsuran.aicoachapi.training.domain.PrescriptionType;
import com.jakubsuran.aicoachapi.training.infrastructure.SpringDataExerciseJpaRepository;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.webmvc.test.autoconfigure.AutoConfigureMockMvc;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;

import static org.hamcrest.Matchers.hasSize;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.delete;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.patch;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.put;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

@SpringBootTest
@AutoConfigureMockMvc
class ExerciseControllerTests {
	@Autowired
	private MockMvc mockMvc;

	@Autowired
	private com.jakubsuran.aicoachapi.training.domain.ExerciseRepository exercises;

	@Autowired
	private SpringDataExerciseJpaRepository jpaRepository;

	@Test
	void createReturnsCamelCaseJsonAndAssignsCurrentUser() throws Exception {
		mockMvc.perform(post("/api/v1/exercises/")
						.header("X-User-Id", "user-1")
						.contentType(MediaType.APPLICATION_JSON)
						.content("""
								{
								  "name": "Bench Press",
								  "defaultSets": 4,
								  "defaultReps": 8,
								  "muscleGroup": "Chest",
								  "defaultTime": 0,
								  "notes": "Pause reps."
								}
								"""))
				.andExpect(status().isCreated())
				.andExpect(jsonPath("$.id").exists())
				.andExpect(jsonPath("$.name").value("Bench Press"))
				.andExpect(jsonPath("$.prescriptionType").value("strength"))
				.andExpect(jsonPath("$.defaultSets").value(4))
				.andExpect(jsonPath("$.muscleGroup").value("Chest"));
	}

	@Test
	void listReturnsOwnedAndSharedExercises() throws Exception {
		jpaRepository.deleteAll();
		exercises.save(Exercise.create("user-1", "Mine", null, null, null, null, null, null));
		exercises.save(Exercise.create("", "Shared", null, null, null, null, null, null));
		exercises.save(Exercise.create("user-2", "Theirs", null, null, null, null, null, null));

		mockMvc.perform(get("/api/v1/exercises/").header("X-User-Id", "user-1"))
				.andExpect(status().isOk())
				.andExpect(jsonPath("$", hasSize(2)))
				.andExpect(jsonPath("$[0].name").value("Mine"))
				.andExpect(jsonPath("$[1].name").value("Shared"));
	}

	@Test
	void getReturnsNotFoundForOtherUserExercise() throws Exception {
		var exercise = exercises.save(Exercise.create("user-2", "Theirs", null, null, null, null, null, null));

		mockMvc.perform(get("/api/v1/exercises/{id}/", exercise.id()).header("X-User-Id", "user-1"))
				.andExpect(status().isNotFound())
				.andExpect(jsonPath("$.detail").value("Exercise was not found."));
	}

	@Test
	void patchPreservesUnspecifiedFields() throws Exception {
		var exercise = exercises.save(Exercise.create("user-1", "Plank", PrescriptionType.TIMED, null, null, "Core", 30L, "Brace."));

		mockMvc.perform(patch("/api/v1/exercises/{id}/", exercise.id())
						.header("X-User-Id", "user-1")
						.contentType(MediaType.APPLICATION_JSON)
						.content("""
								{
								  "name": "Long Plank",
								  "defaultTime": 45
								}
								"""))
				.andExpect(status().isOk())
				.andExpect(jsonPath("$.name").value("Long Plank"))
				.andExpect(jsonPath("$.prescriptionType").value("timed"))
				.andExpect(jsonPath("$.muscleGroup").value("Core"))
				.andExpect(jsonPath("$.notes").value("Brace."))
				.andExpect(jsonPath("$.defaultTime").value(45));
	}

	@Test
	void putReplacesExercise() throws Exception {
		var exercise = exercises.save(Exercise.create("user-1", "Plank", PrescriptionType.TIMED, 1L, 1L, "Core", 30L, "Brace."));

		mockMvc.perform(put("/api/v1/exercises/{id}/", exercise.id())
						.header("X-User-Id", "user-1")
						.contentType(MediaType.APPLICATION_JSON)
						.content("""
								{
								  "name": "Push-Up",
								  "prescriptionType": "strength",
								  "defaultSets": 3,
								  "defaultReps": 12,
								  "muscleGroup": "Chest",
								  "defaultTime": 0,
								  "notes": "Keep core tight."
								}
								"""))
				.andExpect(status().isOk())
				.andExpect(jsonPath("$.name").value("Push-Up"))
				.andExpect(jsonPath("$.prescriptionType").value("strength"))
				.andExpect(jsonPath("$.defaultSets").value(3))
				.andExpect(jsonPath("$.defaultReps").value(12))
				.andExpect(jsonPath("$.defaultTime").value(0));
	}

	@Test
	void deleteRemovesOwnedExercise() throws Exception {
		var exercise = exercises.save(Exercise.create("user-1", "Push-Up", null, null, null, null, null, null));

		mockMvc.perform(delete("/api/v1/exercises/{id}/", exercise.id()).header("X-User-Id", "user-1"))
				.andExpect(status().isNoContent());

		mockMvc.perform(get("/api/v1/exercises/{id}/", exercise.id()).header("X-User-Id", "user-1"))
				.andExpect(status().isNotFound());
	}

	@Test
	void missingUserHeaderReturnsUnauthorized() throws Exception {
		mockMvc.perform(get("/api/v1/exercises/"))
				.andExpect(status().isUnauthorized())
				.andExpect(jsonPath("$.detail").value("X-User-Id header is required."));
	}

	@Test
	void validationErrorsReturnDetail() throws Exception {
		mockMvc.perform(post("/api/v1/exercises/")
						.header("X-User-Id", "user-1")
						.contentType(MediaType.APPLICATION_JSON)
						.content("""
								{
								  "name": "Bench Press",
								  "prescriptionType": "strength",
								  "defaultTime": 30
								}
								"""))
				.andExpect(status().isBadRequest())
				.andExpect(jsonPath("$.detail").value("Strength exercises cannot use a default time."));
	}
}
