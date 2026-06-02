import dotenv from "dotenv";
import { fileURLToPath } from "url";
import { dirname, join } from "path";
import { createApp } from "./app.js";

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

// Load .env first, then .env.local (which overrides .env values).
dotenv.config({ path: join(__dirname, "../.env") });
dotenv.config({ path: join(__dirname, "../.env.local"), override: true });

const app = createApp();
// Keep port 8000 so the frontend (src/services/api.ts) works unchanged.
const PORT = process.env.PORT ?? 8000;

const server = app.listen(PORT, () => {
  console.log(`Server running on http://localhost:${PORT}`);
});

function shutdown() {
  server.close();
}
process.on("SIGTERM", shutdown);
process.on("SIGINT", shutdown);
