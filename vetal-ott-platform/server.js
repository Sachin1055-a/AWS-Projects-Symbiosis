const express = require("express");
const path = require("path");
const { S3Client, GetObjectCommand } = require("@aws-sdk/client-s3");
const { getSignedUrl } = require("@aws-sdk/s3-request-presigner");
require("dotenv").config();

const app = express();
const PORT = process.env.PORT || 3000;

const REGION = process.env.AWS_REGION || "ap-south-1";
const BUCKET_NAME = process.env.S3_BUCKET_NAME || "sachin-s3-02";
const MEDIA_PREFIX = process.env.S3_MEDIA_PREFIX || "movie/";
const URL_EXPIRY_SECONDS = parseInt(process.env.PRESIGNED_URL_EXPIRY || "3600", 10);

const s3 = new S3Client({ region: REGION });
const movies = require("./data/movies.json");

app.use(express.static(path.join(__dirname, "public")));
app.use(express.json());

// Returns movie metadata only (no direct file URLs) — the frontend
// requests a signed URL separately when the user actually opens a movie.
app.get("/api/movies", (req, res) => {
  const list = Object.entries(movies).map(([id, m]) => ({
    id,
    title: m.title,
    year: m.year,
    rating: m.rating,
    match: m.match,
    genre: m.genre,
    desc: m.desc,
  }));
  res.json(list);
});

// Generates a short-lived, signed URL for a specific movie's video and poster.
// This is what keeps the S3 bucket private — nothing is publicly accessible
// without going through this endpoint first.
app.get("/api/stream/:movieId", async (req, res) => {
  const movie = movies[req.params.movieId];
  if (!movie) {
    return res.status(404).json({ error: "Movie not found" });
  }

  try {
    const videoCommand = new GetObjectCommand({
      Bucket: BUCKET_NAME,
      Key: `${MEDIA_PREFIX}${movie.videoKey}`,
    });
    const posterCommand = new GetObjectCommand({
      Bucket: BUCKET_NAME,
      Key: `${MEDIA_PREFIX}${movie.posterKey}`,
    });

    const [videoUrl, posterUrl] = await Promise.all([
      getSignedUrl(s3, videoCommand, { expiresIn: URL_EXPIRY_SECONDS }),
      getSignedUrl(s3, posterCommand, { expiresIn: URL_EXPIRY_SECONDS }),
    ]);

    res.json({
      title: movie.title,
      videoUrl,
      posterUrl,
      expiresIn: URL_EXPIRY_SECONDS,
    });
  } catch (err) {
    console.error("Error generating signed URL:", err);
    res.status(500).json({ error: "Could not generate stream URL" });
  }
});

app.get("/health", (req, res) => res.json({ status: "ok" }));

app.listen(PORT, () => {
  console.log(`Pyzilla server running on port ${PORT}`);
  console.log(`Region: ${REGION} | Bucket: ${BUCKET_NAME}`);
});
