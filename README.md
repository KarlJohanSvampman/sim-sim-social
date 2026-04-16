# sims-lab

## Introduction

The Sims Lab will attempt to simulate Sims characters, using AI Chatbots configured to "role-play" as The Sims characters, in a persistent world, running headless server-side, while also allowing users to render the world in 3D on client side, using three.js and OpenGL.

## Status

The project is very much in early experimental stage with simple geometrical shapes as placeholders for objects, and simple capsules for representing the characters. 

## Configuration 

To enable the power of AI, and AI powered minds for your simulated beings, set the following property in .env.example and rename the file to ".env" 

OPENAI_API_KEY=<your-api-key>


## Run 

Run with:
```bash
docker compose up --build
```
