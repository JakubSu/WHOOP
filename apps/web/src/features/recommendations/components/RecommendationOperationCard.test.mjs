import assert from "node:assert/strict";
import { mkdtemp, rm } from "node:fs/promises";
import { join } from "node:path";
import { pathToFileURL } from "node:url";
import test from "node:test";
import { build } from "esbuild";
import { createElement } from "react";
import { renderToStaticMarkup } from "react-dom/server";

test("renders an API-shaped add-exercise operation", async (t) => {
  const outputDirectory = await mkdtemp(
    join(process.cwd(), ".tmp-recommendation-card-"),
  );
  t.after(() => rm(outputDirectory, { force: true, recursive: true }));
  const outputFile = join(outputDirectory, "card.mjs");

  await build({
    entryPoints: ["src/features/recommendations/components/RecommendationOperationCard.tsx"],
    bundle: true,
    format: "esm",
    platform: "node",
    external: ["react", "lucide-react"],
    outfile: outputFile,
  });
  const { RecommendationOperationCard } = await import(pathToFileURL(outputFile));

  const markup = renderToStaticMarkup(
    createElement(RecommendationOperationCard, {
      operation: {
        id: "operation-1",
        status: "pending",
        operation_type: "add_exercise",
        display_text: "Add Interval",
        reason: "Build aerobic capacity.",
        payload: {
          workout: { kind: "existing", workout_id: "workout-1" },
          exercise_id: "exercise-1",
          prescription: { type: "time", sets: 2, seconds: 60, note: "" },
          position: 1,
        },
      },
      exercise: undefined,
      exerciseLibrary: [{ id: "exercise-1", name: "Interval" }],
      onSave: () => {},
      onAccept: () => {},
      onReject: () => {},
      isSaving: false,
      isAccepting: false,
      isRejecting: false,
    }),
  );

  assert.match(markup, /Interval/);
});
